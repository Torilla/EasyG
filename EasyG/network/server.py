from PyQt5 import QtCore
from PyQt5 import QtNetwork

from EasyG.network import tcp, client
from EasyG import defaults


class EasyGAuthenticationServer(QtCore.QObject):
    NewClientAvailable = QtCore.pyqtSignal(client.EasyGTCPClient)
    AuthenticationFailed = QtCore.pyqtSignal(client.EasyGTCPClient)

    AcceptError = QtCore.pyqtSignal(tcp.EasyGTCPSocket.SocketError)

    def __init__(
        self, hostAddress: QtNetwork.QHostAddress, hostPort: int,
        server: tcp.EasyGTCPServer = tcp.EasyGTCPServer(),
        client_type: type[client.EasyGTCPClient] = client.EasyGTCPClient,
        authentication_protocol: client.EasyGServerSideAuthentication =
        client.EasyGServerSideAuthentication(),
        *args, **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.hostAddress = hostAddress
        self.hostPort = hostPort

        self.server = server
        self.server.setParent(self)
        self.server.acceptError.connect(self.AcceptError)
        # populated with newConnection connection when server starts listening
        self._server_connection = None

        self.client_type = client_type

        self.authentication_protocol = authentication_protocol
        self.authentication_protocol.setParent(self)

    def set_max_pending_connections(self, n: int):
        self.server.setMaxPendingConnections(n)

    @QtCore.pyqtSlot()
    def on_new_connection(self):
        def _disconnectSignals():
            self.authentication_protocol.authSuccess.disconnect(conS)
            self.authentication_protocol.authFailed.disconnect(conF)

        @QtCore.pyqtSlot(str)
        def emit_client(clientID):
            _disconnectSignals()
            client = self.client_type(socket=socket, clientID=clientID,
                                      parent=self)
            self.NewClientAvailable.emit(client)

        @QtCore.pyqtSlot(int)
        def fail_client(errCode):
            _disconnectSignals()
            client = self.client_type(socket=socket, parent=self)
            self.AuthenticationFailed.emit(client)

        socket = self.server.nextPendingConnection()

        conS = self.authentication_protocol.authSuccess.connect(
            emit_client)
        conF = self.authentication_protocol.authFailed.connect(
            fail_client)

        self.authentication_protocol.authenticate(socket=socket)

    def start_listening(self):
        if self._server_connection is None:
            self._server_connection = self.server.newConnection.connect(
                self.on_new_connection)

            if not self.server.listen(self.hostAddress, self.hostPort):
                self.server.newConnection.disconnect(self._server_connection)
                raise OSError(self.server.errorString())

    def is_listening(self):
        return self.server.isListening()

    def close(self):
        if self._server_connection is not None:
            self.server.newConnection.disconnect(self._server_connection)
            self._server_connection = None
            self.server.close()

    @classmethod
    def from_config(cls, config: dict = defaults.Config["Server"]):
        address = QtNetwork.QHostAddress(config["HostAddress"])
        port = config["HostPort"]
        maxPending = config["maxPendingConnections"]

        server = cls(address, port)
        server.set_max_pending_connections(maxPending)

        return server

    def configuration(self):
        return {
            "HostAddress": self.hostAddress.toString(),
            "HostPort": self.hostPort,
            "maxPendingConnections": self.server.maxPendingConnections()
        }
