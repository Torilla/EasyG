from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from EasyG.network.tcp import EasyGTCPServer, EasyGTCPSocket
from EasyG.network.client import EasyGTCPClient
from EasyG.network.client import EasyGServerSideAuthentication


class EasyGAuthenticationServer(QObject):
    NewClientAvailable = pyqtSignal(EasyGTCPClient)
    AuthenticationFailed = pyqtSignal(EasyGTCPClient)

    AcceptError = pyqtSignal(EasyGTCPSocket.SocketError)

    def __init__(self, hostAddress, hostPort,
                 server=EasyGTCPServer(),
                 clientType=EasyGTCPClient,
                 authenticationProtocol=EasyGServerSideAuthentication(),
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.hostAddress = hostAddress
        self.hostPort = hostPort

        self.server = server
        self.server.setParent(self)
        self.server.acceptError.connect(self.AcceptError)

        self.clientType = clientType

        self.authenticationProtocol = authenticationProtocol
        self.authenticationProtocol.setParent(self)

    @pyqtSlot()
    def onNewConnection(self):
        def _disconnectSignals():
            self.authenticationProtocol.authSuccess.disconnect(conS)
            self.authenticationProtocol.authFailed.disconnect(conF)

        @pyqtSlot(str)
        def emitClient(clientID):
            _disconnectSignals()
            client = self.clientType(socket=socket, clientID=clientID,
                                     parent=self)
            self.NewClientAvailable.emit(client)

        @pyqtSlot(int)
        def failClient(errCode):
            _disconnectSignals()
            client = self.clientType(socket=socket, parent=self)
            self.AuthenticationFailed.emit(client)

        socket = self.server.nextPendingConnection()

        conS = self.authenticationProtocol.authSuccess.connect(
            emitClient)
        conF = self.authenticationProtocol.authFailed.connect(
            failClient)

        self.authenticationProtocol.authenticate(socket=socket)

    def startListening(self):
        con = self.server.newConnection.connect(self.onNewConnection)

        if not self.server.listen(self.hostAddress, self.hostPort):
            self.server.newConnection.disconnect(con)
            raise OSError(self.server.errorString())

    def close(self):
        self.server.close()

    def getAddress(self):
        return f"{self.hostAddress.toString()}:{self.hostPort}"
