from PyQt5 import QtCore
from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtCore import Qt

from EasyG.datamanager import plotdataitemmanager
from EasyG.gui import mainwindow
from EasyG.network import server
from EasyG.ecg import exampledata


class EasyG(QtCore.QObject):
    def __init__(self):
        super().__init__()

        self.gui = mainwindow.MainWindow()
        self.datamanager = plotdataitemmanager.PlotDataItemManager()
        self.datamanager.AvailableDataChanged.connect(self.onAvailableDataChanged)
        self.server = server.EasyGAuthenticationServer(QHostAddress("127.0.0.1"), 9999)
        self.server.NewClientAvailable.connect(self.onNewServerClient)
        self.gui.startServerAction.triggered.connect(self.server.startListening)
        self.gui.stopServerAction.triggered.connect(self.server.close)
        self.gui.startServerAction.setEnabled(True)
        self.gui.stopServerAction.setEnabled(True)
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

        tabName = f"{exampleName.split('.')[0]} Example"
        tab = self.gui.centralWidget().addTab(tabName)
        self.gui.addDockWidget(Qt.LeftDockWidgetArea, tab.dockWidget)
        path = f"/{tabName}"
        plotItem = self.datamanager.registerPlotItemData(path, data=(x, y),
                                                         plotItemName=exampleName)
        tab.plotManager.addItemToPlot(0, 0, plotItem)

    def onAvailableDataChanged(self):
        config = self.datamanager.getPlotDataItemConfiguration()
        self.gui.updateTabDockWidgetConfigs(config)
