from PyQt5.QtNetwork import QTcpServer, QTcpSocket


class EasyGTCPSocket(QTcpSocket):
    pass


class EasyGTCPServer(QTcpServer):
    def incomingConnection(self, handle):
        socket = EasyGTCPSocket(parent=self)
        if socket.setSocketDescriptor(handle):
            self.addPendingConnection(socket)

