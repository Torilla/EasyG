from __future__ import annotations
from typing import TypedDict

from PyQt5 import QtCore
from PyQt5 import QtNetwork

from EasyG.network import client
from EasyG import defaults


class ServerConfiguration(TypedDict):

    """class ServerConfiguration

    Simple type wrapper for a server configuration
    Attributes:
        HostAddress (QtNetwork.QHostAddress)
        HostPort (int)
        maxPendingConnections (int)
    """

    HostAddress: str
    HostPort: int
    maxPendingConnections: int


class EasyGAuthenticationServer(QtCore.QObject):

    """class EasyGAuthenticationServer

    This class provides a simple wrapper around the native QTcpServer.
    It adds an additional authentication protocol that is defined in
    EasyG.network.clients and implements a simple ID and password check.

    Attributes:
        AcceptError (QtCore.pyqtSignal[client.EasyGTCPClient]): Emitted when
            the server emits a acceptError
        authentication_protocol (network.client.EasyGServerSideAuthentication):
            The used authentication protocol
        AuthenticationFailed (QtCore.pyqtSignal[client.EasyGTCPClient]):
            Emitted when then authnetication of a client failed
        client_type (client.EasyGTCPClient): The client class that is used
            when new clients are initialized
        host_address (QtNetwork.QHostAddress): The address the server will be
            listening at
        host_port (int): The port the server will be listening at
        NewClientAvailable (TYPE): Emitted when a client was succesfully
            authenticated
        server (QtNetwork.QTcpServer): The underlying native server
            implementation.
    """

    NewClientAvailable = QtCore.pyqtSignal(client.EasyGTCPClient)
    AuthenticationFailed = QtCore.pyqtSignal(client.EasyGTCPClient)

    AcceptError = QtCore.pyqtSignal(QtNetwork.QAbstractSocket.SocketError)

    def __init__(
        self,
        host_address: QtNetwork.QHostAddress,
        host_port: int,
        server: QtNetwork.QTcpServer = QtNetwork.QTcpServer(),
        client_type: type[client.EasyGTCPClient] = client.EasyGTCPClient,
        authentication_protocol: client.EasyGServerSideAuthentication =
        client.EasyGServerSideAuthentication(),
        *args, **kwargs
    ):
        """Initialize a new EasyGAuthenticationServer instance

        Args:
            host_address (QtNetwork.QHostAddress): The address to listen at
            host_port (int): The port to listen at
            server (tcp.EasyGTCPServer, optional): The native underlying server
                implementation
            client_type (type[client.EasyGTCPClient], optional): The class
                used when a new client is initalized
            authentication_protocol (EasyGServerSideAuthentication, optional):
                The used authentication protocol
            *args: Forwarded to QObject.__init__
            **kwargs: Forwarded to QObject.__init__
        """
        super().__init__(*args, **kwargs)

        self.host_address = host_address
        self.host_port = host_port

        self.server = server
        self.server.setParent(self)
        self.server.acceptError.connect(self.AcceptError)
        # populated with newConnection connection when server starts listening
        self._server_connection = None

        self.client_type = client_type

        self.authentication_protocol = authentication_protocol
        self.authentication_protocol.setParent(self)

    def set_max_pending_connections(self, n: int):
        """Set the maximum number of pending connections

        Args:
            n (int): The maximum number of pending connections to set to
        """
        self.server.setMaxPendingConnections(n)

    @QtCore.pyqtSlot()
    def on_new_connection(self) -> None:
        """Slot executed when the underlying server recieves a new client.
        It carries out the authentication of the client and either emits it
        using the NewClientAvailable signal or the AuthenticationFailed signal.
        """
        def _disconnectSignals() -> None:
            self.authentication_protocol.authSuccess.disconnect(conS)
            self.authentication_protocol.authFailed.disconnect(conF)

        @QtCore.pyqtSlot(str)
        def emit_client(clientID: str) -> None:
            _disconnectSignals()
            client = self.client_type(socket=socket, clientID=clientID,
                                      parent=self)
            self.NewClientAvailable.emit(client)

        @QtCore.pyqtSlot(int)
        def fail_client(errCode: int) -> None:
            _disconnectSignals()
            client = self.client_type(socket=socket, parent=self)
            self.AuthenticationFailed.emit(client)

        socket = self.server.nextPendingConnection()

        conS = self.authentication_protocol.authSuccess.connect(
            emit_client)  # type: ignore[arg-type]
        conF = self.authentication_protocol.authFailed.connect(
            fail_client)  # type: ignore[arg-type]

        self.authentication_protocol.authenticate(socket=socket)

    def start_listening(self) -> None:
        """Start listening at the given address and port. If the server is
        already listening, this will have no effect.

        Raises:
            OSError: If it is not possible to listen at the given address.
                Use server.error_string() to get more information in that case
        """
        if self._server_connection is None:
            self._server_connection = self.server.newConnection.connect(
                self.on_new_connection)

            if not self.server.listen(self.host_address, self.host_port):
                self.server.newConnection.disconnect(self._server_connection)
                raise OSError(self.server.errorString())

    def is_listening(self) -> bool:
        """Determine if the server is listening

        Returns:
            bool: True if the server is listening false otherwise
        """
        return self.server.isListening()

    def close(self):
        """Close the server connection. If the server is not listening, this
        will have no effect.
        """
        if self._server_connection is not None:
            self.server.newConnection.disconnect(self._server_connection)
            self._server_connection = None
            self.server.close()

    def server_address(self) -> QtNetwork.QHostAddress:
        """Return the currently set host address

        Returns:
            QtNetwork.QHostAddress: The current host address
        """
        return self.server.serverAddress()

    def server_port(self) -> int:
        """Return the currently set host port

        Returns:
            int: The current host port
        """
        return self.server.serverPort()

    def error_string(self) -> str | None:
        """Return the string describing the last error that occured.

        Returns:
            str | None: The string describing the last error, if any.
        """
        return self.server.errorString()

    @classmethod
    def from_configuration(
        cls, configuration: ServerConfiguration = defaults.Config["Server"]
    ) -> EasyGAuthenticationServer:
        """Get a new server instance from a configuration dictionary.

        Args:
            configuration (ServerConfiguration, optional): If not provided, the
                default configuration set in defaults.yml will be used.
        """
        address = QtNetwork.QHostAddress(configuration["HostAddress"])
        port = configuration["HostPort"]
        maxPending = configuration["maxPendingConnections"]

        server = cls(address, port)
        server.set_max_pending_connections(maxPending)

        return server

    def get_configuration(self) -> ServerConfiguration:
        return ServerConfiguration(
            HostAddress=self.host_address.toString(),
            HostPort=self.host_port,
            maxPendingConnections=self.server.maxPendingConnections()
        )
