from PyQt5 import QtCore
from PyQt5.QtNetwork import QHostAddress

from EasyG.datamanager import plotdataitemmanager
from EasyG.gui import mainwindow
from EasyG.network import server
from EasyG.ecg import exampledata


class EasyG(QtCore.QObject):
    def __init__(self):
        super().__init__()

        self.gui = mainwindow.MainWindow()
        self.datamanager = plotdataitemmanager.PlotDataItemManager()
        self.server = server.EasyGAuthenticationServer(QHostAddress("127.0.0.1"), 9999)
        self.server.NewClientAvailable.connect(self.onNewServerClient)
        self.server.startListening()
        self.gui.OpenExampleRequest.connect(self.onOpenExampleRequest)

    def onNewServerClient(self, client):
        tabName = client.getClientID()
        tab = self.gui.centralWidget().addTab(tabName)

        path = f"/{tabName}"
        plotItem = self.datamanager.registerNetworkClientPlotItem(path, client)
        tab.plotManager.addItemToPlot(0, 0, plotItem)

    def onOpenExampleRequest(self):
        x, y, exampleName = exampledata.openExample()
        if x is None or y is None:
            return

        tabName = f"{exampleName} Example"
        tab = self.gui.centralWidget().addTab(tabName)

        path = f"/{tabName}"
        plotItem = self.datamanager.registerPlotItemData(path, data=(x, y))

        tab.plotManager.addItemToPlot(0, 0, plotItem)
