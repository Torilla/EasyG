from __future__ import annotations
from typing import Callable
from enum import Enum, IntEnum

from PyQt5 import QtCore, QtNetwork, QtSql

import bcrypt


DEFAULT_DB_DRIVER = "QSQLITE"
_DEFAULT_DB_NAME = "EasyGClients.db"


def getPasswordHash(password: str) -> str:
    """Return the salted hash of password. Uses bcrypt.haspw.

    Args:
        password (str): The password to has

    Returns:
        str: The hashed password
    """
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def checkPassword(password: str, passwordHash: str) -> bool:
    """Check if password matches the hashed password passwordHash. Uses
    bcrypt.checkpw

    Args:
        password (str): The password to check
        passwordHash (str): The password hash to check against.

    Returns:
        bool: True if password matches passwordHash, false otherwise
    """
    return bcrypt.checkpw(password.encode(), passwordHash.encode())


class EasyGDatabaseError(IOError):

    """Raised when a Database transaction fails"""


class EasyGClientDatabase(QtCore.QObject):

    """class EasyGClientDatabase

    This class exposes an interface to register new network clients and their
    passwords, as well as to retrieve them and check passwords against stored
    ones.

    Attributes:
        dbDriver (str): The underlying PyQt database driver.
        dbName (str): The filename to use for the database.
    """

    def __init__(
        self,
        dbName: str = _DEFAULT_DB_NAME,
        dbDriver: str = DEFAULT_DB_DRIVER,
        *args, **kwargs
    ):
        """Initialize a new EasyGClientDatabase instance.

        Args:
            dbName (str, optional): the name of the databse.
            dbDriver (str, optional): the underlying database driver
            *args: Forwared to QObject.__init__
            **kwargs: Forwared to QObject.__init__
        """
        super().__init__(*args, **kwargs)

        self.dbName = dbName
        self.dbDriver = dbDriver

        self._db = QtSql.QSqlDatabase.addDatabase(self.dbDriver)
        self._db.setDatabaseName(self.dbName)

        self._initDb()

    def __enter__(self) -> EasyGClientDatabase:
        """Start a new database transaction

        Returns:
            EasyGClientDatabase: self

        Raises:
            IOError: If it it not possible to open the databse
        """
        if not self._db.open():
            raise IOError(f"Can not open database {self.dbName}")

        return self

    def __exit__(self, exec_type, exc_value, exc_tb):
        """Finish a databse transaction"""
        if exec_type is None:
            self._db.commit()

        self._db.close()

    def _initDb(self):
        """Initialize the databse with the required tables."""
        with self:
            query = QtSql.QSqlQuery()
            query.exec(
                """
                CREATE TABLE IF NOT EXISTS EasyGClients (
                    clientID TEXT PRIMARY KEY,
                    passwordHash TEXT NOT NULL
                );
                """
            )

    def _registerNewClient(self, clientID: str, passwordHash: str) -> None:
        """Register a new client in the databse. Do not use this method
        directly, use registerNewClient(clientID, password)

        Args:
            clientID (str): The ID of the client
            passwordHash (str): The hashed (!) password of the client

        Raises:
            EasyGDatabaseError: If a client with this ID has already been
                registered
        """
        with self:
            query = QtSql.QSqlQuery()
            query.prepare(
                """
                INSERT INTO EasyGClients (
                    clientID,
                    passwordHash
                )
                VALUES (:clientID, :passwordHash);
                """)

            query.bindValue(":clientID", clientID)
            query.bindValue(":passwordHash", passwordHash)

            query.exec()

        if query.lastError().isValid():
            raise EasyGDatabaseError(query.lastError().text())

    @QtCore.pyqtSlot(str, str)
    def registerNewClient(self, clientID: str, password: str) -> None:
        """Register a new client with ID clientID and password to the database.

        Args:
            clientID (str): The client ID
            password (str): The client password

        Raises:
            EasyGDatabaseError: If a client with this ID has already been
                registered
        """
        pwHash = getPasswordHash(password)
        try:
            self._registerNewClient(clientID=clientID, passwordHash=pwHash)
        except EasyGDatabaseError as err:
            raise err from None

    def _getClientPasswordHash(self, clientID: str) -> str:
        """Return the password hash belonging to client with ID equal to
        clientID. Do not use this method directly, use checkClientPassword.

        Args:
            clientID (str): The ID of the client to query

        Returns:
            str: The password has of client

        Raises:
            EasyGDatabaseError: If no such client exists
        """
        with self:
            query = QtSql.QSqlQuery()
            query.prepare(
                """
                    SELECT passwordHash FROM EasyGClients
                    WHERE clientID=:clientID;
                """)

            query.bindValue(":clientID", clientID)
            query.exec()

        if not query.first():
            raise EasyGDatabaseError(f"No clientID '{clientID}' found.")

        return query.value(0)

    @QtCore.pyqtSlot(str, str)
    def checkClientPassword(self, clientID: str, clientPassword: str) -> bool:
        """Check if the stored password belonging to clientID matches the
        given clientPassword.

        Args:
            clientID (str): The ID of the client
            clientPassword (str): The password to check against client

        Returns:
            bool: True if the password matches the client, False otherwise
        """
        try:
            pwHash = self._getClientPasswordHash(clientID)
            result = checkPassword(password=clientPassword,
                                   passwordHash=pwHash)
        except EasyGDatabaseError:
            result = False

        return result


class AuthenticationControlFlags(bytes, Enum):

    """class AuthenticationControlFlags.
    Simple Enum that stores some control flags for client authentication

    Attributes:
        EOM (bytes): End of Message
        FAILED (int): Client Authentication Failed
        SUCCESS (int): Client Authentication Successfull
    """

    def __new__(cls, value):
        """Initialize a new AuthenticationControlFlags class

        Args:
            value (TYPE): Description

        Returns:
            TYPE: Description
        """
        if isinstance(value, bytes):
            obj = super().__new__(cls, value)
            obj._value_ = value

        else:
            obj = super().__new__(cls, [value])
            obj._value_ = value.to_bytes((value.bit_length() + 7) // 8,
                                         byteorder="big")

        return obj

    EOM = b"\n"
    SUCCESS = 0
    FAILED = 1

    def __eq__(self, other: str | bytes) -> bool:
        """Check if other is equal to a given member of the Enum

        Args:
            other (str | bytes): What to compare to

        Returns:
            bool: True if euqality with other holds, False otherwise
        """
        try:
            other = other.to_bytes((other.bit_length() + 7) // 8,
                                   byteorder="big")
        except AttributeError:
            pass

        return self.value == other


class AuthenticationErrorCodes(IntEnum):

    """class AuthenticationErrorCodes
    Simple Enum that holds Authentication Error Codes

    Attributes:
        BAD_AUTH (int): Bad authentication
        SOCKET_ERROR (int): Socker error
    """

    SOCKET_ERROR = 0
    BAD_AUTH = 1


class EasyGAbstractAuthenticationProtocol(QtCore.QObject):

    """class EasyGAbstractAuthenticationProtocol
    Abstract base clas for authentication protocols

    Attributes:
        authFailed (TYPE): signal emitted when authentication failed
        authSuccess (TYPE): signal emitted when authenticationw as succesfull
        CLIENTDB (TYPE): The database instance holding the registered clients.
    """

    CLIENTDB = EasyGClientDatabase()

    authSuccess = QtCore.pyqtSignal(str)
    authFailed = QtCore.pyqtSignal(int)

    @classmethod
    def setClientDB(cls, db: EasyGClientDatabase) -> None:
        """Set a new client databse

        Args:
            db (EasyGClientDatabase): The database instance to use
        """
        cls.CLIENTDB = db


class EasyGServerSideAuthentication(EasyGAbstractAuthenticationProtocol):

    """class EasyGServerSideAuthentication
    The protocol used by the server to authenticate clients against a
    EasyGClientDatabase instance.
    """

    @QtCore.pyqtSlot(QtNetwork.QTcpSocket)
    def authenticate(self, socket: QtNetwork.QTcpSocket) -> None:
        """Authenticate an incoming client against the databse. If
        authentication was succesfull, authSuccess is emmited with the client,
        otherwise authFailed is emitted with the error code.

        Args:
            socket (QtNetwork.QTcpSocket): The socket to authenticate
        """
        @QtCore.pyqtSlot()
        def readAuth():
            socket.readyRead.disconnect(con)

            clientID = str(socket.readLine()[:-1], "utf-8")

            try:
                clientID, clientPW = clientID.split(":")

            except ValueError:
                clientPW = None

            if clientPW is not None and self.CLIENTDB.checkClientPassword(
                    clientID=clientID, clientPassword=clientPW):
                socket.write(AuthenticationControlFlags.SUCCESS)
                socket.write(AuthenticationControlFlags.EOM)
                self.authSuccess.emit(clientID)

            else:
                socket.write(str(AuthenticationErrorCodes.BAD_AUTH).encode())
                socket.write(AuthenticationControlFlags.EOM)

                self.authFailed.emit(AuthenticationErrorCodes.BAD_AUTH)

            socket.disconnected.disconnect(conD)

        @QtCore.pyqtSlot()
        def onDisconnect():
            socket.disconnected.disconnect(conD)
            socket.readyRead.disconnect(con)
            self.authFailed.emit(AuthenticationErrorCodes.SOCKET_ERROR)

        con = socket.readyRead.connect(readAuth)  # type: ignore[arg-type]
        conD = socket.disconnected.connect(onDisconnect)  # type: ignore[arg-type]


class EasyGClientSideAuthentication(EasyGAbstractAuthenticationProtocol):

    """class EasyGClientSideAuthentication
    This class performs the client side authentication against a an
    EasyGAuthenticationServer instance.

    Attributes:
        authSuccess (QtCore.pyqtSignal): Emitted if we authenticated
            successuflly
    """

    authSuccess = QtCore.pyqtSignal()

    @QtCore.pyqtSlot(QtNetwork.QTcpSocket, str, str)
    def authenticate(
        self, socket: QtNetwork.QTcpSocket, clientID: str, clientPassword: str
    ) -> None:
        """Authenticate using the current conncetion to the authentication
        server

        Args:
            socket (QtNetwork.QTcpSocket): The socket providing the connection
            clientID (str): The client ID to use for authentication
            clientPassword (str): The password belonging to the client
        """
        @QtCore.pyqtSlot()
        def waitForReply():
            socket.readyRead.disconnect(con)

            if socket.readLine()[:-1] == AuthenticationControlFlags.SUCCESS:
                self.authSuccess.emit()

            else:
                self.authFailed.emit(AuthenticationErrorCodes.BAD_AUTH)

        con = socket.readyRead.connect(waitForReply)  # type: ignore[arg-type]

        socket.write(f"{clientID}:{clientPassword}".encode())
        socket.write(AuthenticationControlFlags.EOM)


class EasyGAbstractClient(QtCore.QObject):

    """Abstract class providing parser methods."""

    @staticmethod
    def defaultParser(data: str) -> list[str]:
        return [data]

    @staticmethod
    def floatParser(data: str) -> list[float]:
        return [float(d) for d in data.split()]


class EasyGTCPClient(EasyGAbstractClient):

    """class EasyGTCPClient
    This class exposes the Interface that is used to handle a client connection
    on the server side.

    Attributes:
        clientID (str): The client ID to used for authentication
        dataParser (Callable): The parser parsing raw incoming data to useful
            version of the data for processing
        disconnected (QtCore.pyqtSignal): Emmitted when the client disconnected
            from the server
        newLineOfData (TQtCore.pyqtSignal[list]): Emitted with the parsed data
            when new data arrive
        socket (QtNetwork.QTcpSocket): The underlying TCP socket.
        SocketState (QtNetwork.QTcpSocker.SocketState): The current state of
            the underlying socket.
    """

    newLineOfData = QtCore.pyqtSignal(list)
    disconnected = QtCore.pyqtSignal()

    def __init__(
        self,
        socket: QtNetwork.QTcpSocket,
        clientID=None,
        dataParser=EasyGAbstractClient.floatParser,
        *args, **kwargs
    ) -> None:
        """Initalize a new EasyGTCPClient

        Args:
            socket (QtNetwork.QTcpSocket): The socket that provides the
                connection
            clientID (None, optional): The ID of the client
            dataParser (TYPE, optional): The parser parsing the raw data
            *args: Forwarted to QObject.__init__
            **kwargs: Forwarted to QObject.__init__
        """
        super().__init__(*args, **kwargs)

        self.setSocket(socket)
        self.setClientID(clientID)
        self.setDataParser(dataParser)

        self._dataBuffer = QtCore.QByteArray()
        self._readyReadConnection = None

    def setSocket(self, socket: QtNetwork.QTcpSocket) -> None:
        """Set the used socket.

        Args:
            socket (QtNetwork.QTcpSocket): The socket to use
        """
        self.socket = socket
        self.socket.setParent(self)
        self.SocketState = self.socket.SocketState
        self.socket.disconnected.connect(self.disconnected)

    def setClientID(self, clientID: str) -> None:
        """Set the ID of the client

        Args:
            clientID (str): The ID to use
        """
        self.clientID = clientID

    def getClientID(self) -> str | None:
        """The ID of the client if any is set

        Returns:
            str | None: The ID if any is set
        """
        return self.clientID

    def setDataParser(self, parser: Callable) -> None:
        """Summary

        Args:
            parser (Callable): Set the method that parses raw data
        """
        self.dataParser = parser

    @QtCore.pyqtSlot()
    def _onReadyRead(self) -> None:
        """
        Reads all avaible data from the socket and splits it into lines.
        Each line is parsed and and parsing result is emitted as newLineOfData.
        """
        self._dataBuffer.append(self.socket.readAll())
        idx = self._dataBuffer.lastIndexOf(b"\n")

        if idx > 0:
            data = self._dataBuffer[:idx]
            self._dataBuffer = self._dataBuffer[idx + 1:]

            for d in str(data, "utf-8").split("\n"):
                d = self.dataParser(d)
                self.newLineOfData.emit(d)

        elif idx == 0:
            self._dataBuffer.clear()

    def isValid(self) -> bool:
        """Return the validity of the underlying socket

        Returns:
            bool: True if the socket is valid, false otherwise
        """
        return self.socket.isValid()

    def state(self) -> QtNetwork.QTcpSocket.SocketState:
        """Return the current state of the socket

        Returns:
            QtNetwork.QTcpSocket.SocketState: Current socket state
        """
        return self.socket.state()

    def startParsing(self) -> None:
        """Start parsing raw data and emitting the result as NewDataAvailable
        """
        if not self._readyReadConnection:
            self._readyReadConnection = self.socket.readyRead.connect(
                self._onReadyRead)

    def stopParsing(self) -> None:
        """Stop parsing raw data and emitting it.
        """
        if self._readyReadConnection:
            self.socket.readyRead.disconnect(self._readyReadConnection)

    def getClientAddress(self) -> str:
        """Return the current address in use by this spcket

        Returns:
            str: The current socket address
        """
        return self.socket.peerAddress().toString()

    def disconnectFromHost(self) -> None:
        """Sever the connection to this client."""
        self.stopParsing()
        self.socket.disconnectFromHost()
