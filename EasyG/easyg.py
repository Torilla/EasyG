from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtCore import Qt

from EasyG.datautils import plotdataitemmanager
from EasyG.gui import mainwindow
from EasyG.network import server
from EasyG.ecg import exampledata


class EasyG(object):
    def __init__(self):
        super().__init__()

        self.datamanager = plotdataitemmanager.PlotDataManager()

        self.server = server.EasyGAuthenticationServer(QHostAddress("127.0.0.1"), 9999)
        self.server.NewClientAvailable.connect(self._onNewServerClient)

        self.gui = mainwindow.MainWindow()
        self.gui.startServerAction.triggered.connect(self.server.startListening)
        self.gui.stopServerAction.triggered.connect(self.server.close)
        self.gui.startServerAction.setEnabled(True)
        self.gui.stopServerAction.setEnabled(True)
        self.gui.OpenExampleRequest.connect(self._onOpenExampleRequest)

    def _onNewServerClient(self, client):
        tabName = client.getClientID()
        tab = self.gui.centralWidget().addTab(tabName)

        path = f"/{tabName}"
        plotItem = self.datamanager.registerNetworkClientPlotItem(path, client)
        tab.plotManager.addItemToPlot(0, 0, plotItem)

        self._updateTabDockWidgetConfigs()

    def _onOpenExampleRequest(self):
        x, y, exampleName = exampledata.openExample()
        if x is None or y is None:
            return

        tabName = f"{exampleName.split('.')[0]} Example"
        self.createNewTab(tabName=tabName, plotName="Plot 1",
                          itemName=exampleName, data=(x, y))

    def _updateTabDockWidgetConfigs(self):
        config = self.datamanager.getPlotDataItemConfiguration()
        self.gui.updateTabDockWidgetConfigs(config)

    def createNewTab(self, tabName, plotName, itemName, data):
        path = f"/{tabName}"
        plotItem = self.datamanager.registerPlotItemData(
            path, data=data, plotItemName=itemName)
        tab = self.gui.tabManager.addTab(tabName)

        # create the first column of plots and insert the first plotter
        tab.insertColumn(0)
        tab.insertPlotWidget(0, 0, title=plotName)
        tab.addItemToPlot(0, 0, plotItem)

        # if this is the first tab, add the dock widget as normal
        if self.gui.tabManager.count() == 1:
            self.gui.addDockWidget(Qt.LeftDockWidgetArea, tab.dockWidget)

        # otherwise create tabified dock widgets
        else:
            dock = self.gui.tabManager.currentWidget().dockWidget
            self.gui.tabifyDockWidget(dock, tab.dockWidget)

        self._updateTabDockWidgetConfigs()
