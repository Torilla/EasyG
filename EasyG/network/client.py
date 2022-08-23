from enum import Enum, IntEnum

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QByteArray
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

import bcrypt

from EasyG.network.tcp import EasyGTCPSocket


DEFAULT_DB_DRIVER = "QSQLITE"
_DEFAULT_DB_NAME = "EasyGClients.db"


def getPasswordHash(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def checkPassword(password, passwordHash):
    return bcrypt.checkpw(password.encode(), passwordHash.encode())


class EasyGDatabaseError(IOError):
    pass


class EasyGClientDatabase(QObject):
    def __init__(self, dbName=_DEFAULT_DB_NAME, dbDriver=DEFAULT_DB_DRIVER,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.dbName = dbName
        self.dbDriver = dbDriver

        self._db = QSqlDatabase.addDatabase(self.dbDriver)
        self._db.setDatabaseName(self.dbName)

        self._initDb()

    def __enter__(self):
        if not self._db.open():
            raise IOError(f"Can not open database {self.dbName}")

        return self

    def __exit__(self, exec_type, exc_value, exc_tb):
        if exec_type is None:
            self._db.commit()

        self._db.close()

    def _initDb(self):
        with self:
            query = QSqlQuery()
            query.exec(
                """
                CREATE TABLE IF NOT EXISTS EasyGClients (
                    clientID TEXT PRIMARY KEY,
                    passwordHash TEXT NOT NULL
                );
                """
            )

    def _registerNewClient(self, clientID, passwordHash):
        with self:
            query = QSqlQuery()
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

    @pyqtSlot(str, str)
    def registerNewClient(self, clientID, password):
        pwHash = getPasswordHash(password)
        self._registerNewClient(clientID=clientID, passwordHash=pwHash)

    def _getClientPasswordHash(self, clientID):
        with self:
            query = QSqlQuery()
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

    @pyqtSlot(str, str)
    def checkClientPassword(self, clientID, clientPassword):
        try:
            pwHash = self._getClientPasswordHash(clientID)
            result = checkPassword(password=clientPassword,
                                   passwordHash=pwHash)
        except EasyGDatabaseError:
            result = False

        return result


class AuthenticationControlFlags(bytes, Enum):
    def __new__(cls, value):
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

    def __eq__(self, other):
        try:
            other = other.to_bytes((other.bit_length() + 7) // 8,
                                   byteorder="big")
        except AttributeError:
            pass

        return self.value == other


class AuthenticationErrorCodes(IntEnum):
    SOCKET_ERROR = 0
    BAD_AUTH = 1


class EasyGAbstractAuthenticationProtocol(QObject):
    CLIENTDB = EasyGClientDatabase()

    authSuccess = pyqtSignal(str)
    authFailed = pyqtSignal(int)

    @classmethod
    def setClientDB(cls, db):
        cls.CLIENTDB = db


class EasyGServerSideAuthentication(EasyGAbstractAuthenticationProtocol):
    @pyqtSlot(EasyGTCPSocket)
    def authenticate(self, socket):
        @pyqtSlot()
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

        @pyqtSlot()
        def onDisconnect():
            socket.disconnected.disconnect(conD)
            socket.readyRead.disconnect(con)
            self.authFailed.emit(AuthenticationErrorCodes.SOCKET_ERROR)

        con = socket.readyRead.connect(readAuth)
        conD = socket.disconnected.connect(onDisconnect)


class EasyGClientSideAuthentication(EasyGAbstractAuthenticationProtocol):
    authSuccess = pyqtSignal()

    @pyqtSlot(EasyGTCPSocket, str, str)
    def authenticate(self, socket, clientID, clientPassword):
        @pyqtSlot()
        def waitForReply():
            socket.readyRead.disconnect(con)

            if socket.readLine()[:-1] == AuthenticationControlFlags.SUCCESS:
                self.authSuccess.emit()

            else:
                self.authFailed.emit(AuthenticationErrorCodes.BAD_AUTH)

        con = socket.readyRead.connect(waitForReply)

        socket.write(f"{clientID}:{clientPassword}".encode())
        socket.write(AuthenticationControlFlags.EOM)


class EasyGAbstractClient(QObject):
    @staticmethod
    def defaultParser(data: str) -> list[str]:
        return [data]

    @staticmethod
    def floatParser(data: str) -> list[float]:
        return [float(d) for d in data.split()]


class EasyGTCPClient(EasyGAbstractClient):
    newLineOfData = pyqtSignal(list)
    disconnected = pyqtSignal()

    def __init__(self, socket, clientID=None,
                 dataParser=EasyGAbstractClient.floatParser,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSocket(socket)
        self.setClientID(clientID)
        self.setDataParser(dataParser)

        self._dataBuffer = QByteArray()
        self._con = None

    def setSocket(self, socket):
        self.socket = socket
        self.socket.setParent(self)
        self.SocketState = self.socket.SocketState
        self.socket.disconnected.connect(self.disconnected)

    def setClientID(self, clientID):
        self.clientID = clientID

    def getClientID(self):
        return self.clientID

    def setDataParser(self, parser):
        self.dataParser = parser

    @pyqtSlot()
    def _onReadyRead(self):
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

    def isValid(self):
        return self.socket.isValid()

    def state(self):
        return self.socket.state()

    def startParsing(self, clearBufferPrior=False):
        if clearBufferPrior:
            self.socket.readAll()

        self._con = self.socket.readyRead.connect(self._onReadyRead)

    def stopParsing(self):
        if self._con:
            self.socket.readyRead.disconnect(self._con)

    def getClientAddress(self):
        return self.socket.peerAddress().toString()

    def disconnectFromHost(self):
        self.socket.disconnectFromHost()
