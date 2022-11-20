from PyQt5.QtCore import QObject, pyqtSlot, qDebug

from EasyG.config import getConfig

from EasyG.network import server
from EasyG.network.tcp import EasyGTCPSocket
from EasyG.network.client import EasyGTCPClient
from EasyG.gui.mainwidget import EasyGMainWindow
from EasyG.gui.plotwidget import EasyGServerPlotWidget

Config = getConfig()


class EasyGServerPluginHandler(QObject):
    def __init__(self, serverPlugin=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._serverPlugin = None
        self._serverErrorCon = None
        self._serverNewClientCon = None

        self.setServerPlugin(serverPlugin)

    def serverPlugin(self):
        return self._serverPlugin

    def _disconnectServerSignals(self):
        if (serv := self.serverPlugin()) is not None:
            if self._serverErrorCon:
                serv.acceptError.disconnect(self._serverErrorCon)
                self._serverErrorCon = None

            if self._serverNewClientCon:
                serv.newClient.disconnect(self._serverNewClientCon)
                self._serverNewClientCon = None

    @pyqtSlot(EasyGTCPSocket.SocketError)
    def _onServerError(self, error):
        msg = f"EasyG ServerError: {error}"
        qDebug(msg)
        self.mainWindow.statusBar().showMessage(msg)

    @pyqtSlot(EasyGTCPClient)
    def _onNewClient(self, client):
        self._addServerPlotTabWidget(client=client)

    def _addServerPlotTabWidget(self, client):
        raise NotImplementedError

    def setServerPlugin(self, serverPlugin):
        self._disconnectServerSignals()
        oldServ = self.serverPlugin()

        self._serverPlugin = serverPlugin

        if serverPlugin is not None:
            self._serverPlugin.setParent(self)

            self._serverErrorCon = serverPlugin.acceptError.connect(
                self._onServerError)

            self._serverNewClientCon = serverPlugin.newClient.connect(
                self._onNewClient)

        return oldServ

    @pyqtSlot()
    def _startServerPlugin(self):
        serv = self.serverPlugin()
        try:
            serv.startListening()
            msg = f"Server started listening on {serv.getAddress()}"
            qDebug(msg)
            self.mainWindow.statusBar().showMessage(msg)
            self.mainWindow.stopServerAction.setEnabled(True)
            self.mainWindow.startServerAction.setEnabled(False)

        except OSError as err:
            qDebug(f"ServerPlugin Error: {err}")

    @pyqtSlot()
    def _stopServerPlugin(self):
        serv = self.serverPlugin()
        serv.close()
        msg = f"Server stopped listening on {serv.getAddress()}"
        qDebug(msg)
        self.mainWindow.statusBar().showMessage(msg)
        self.mainWindow.stopServerAction.setEnabled(False)
        self.mainWindow.startServerAction.setEnabled(True)


class EasyGGUI(EasyGServerPluginHandler):
    def __init__(self, serverPlugin=None, *args, **kwargs):
        self._startServerCon = None
        self._stopServerCon = None

        super().__init__(serverPlugin=serverPlugin, *args, **kwargs)

        self.mainWindow = EasyGMainWindow(
            title=Config.get("gui", "title"),
            geometry=Config.getGeometry("gui", "geometry"))

    def show(self):
        self.mainWindow.show()

    def hide(self):
        self.mainWindow.hide()

    @pyqtSlot()
    def _disconnectServerSignals(self):
        super()._disconnectServerSignals()
        if self._startServerCon is not None:
            self.mainWindow.startServerAction.triggered.disconnect(
                self._startServerCon)
            self.mainWindow.startServerAction.setEnabled(False)

        if self._stopServerCon is not None:
            self.mainWindow.stopServerAction.triggered.disconnect(
                self._stopServerCon)
            self.mainWindow.stopServerAction.setEnabled(False)

    def setServerPlugin(self, serverPlugin):
        oldServ = super().setServerPlugin(serverPlugin)

        if serverPlugin is not None:
            act = self.mainWindow.startServerAction
            self._startServerCon = act.triggered.connect(
                self._startServerPlugin)
            act.setEnabled(True)

            act = self.mainWindow.stopServerAction
            self._stopServerCon = act.triggered.connect(
                self._stopServerPlugin)

        return oldServ

    def setDefaultServerPlugin(self):
        serv = getattr(server, Config["server.config"]["type"])

        host = Config.getHostAddress("server", "address")
        port = Config.getint("server", "port")

        serv = serv(hostAddress=host, hostPort=port)

        return self.setServerPlugin(serv)

    def _addServerPlotTabWidget(self, client):
        widget = EasyGServerPlotWidget(serverClient=client)
        clientID = client.getClientID()
        tabName = f"EasyG Server Client: {clientID}"

        self.mainWindow.addMainPlotWidgetTab(tabName=tabName, widget=widget,
                                             name=clientID)
