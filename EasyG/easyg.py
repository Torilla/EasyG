from EasyG.datautils import plotdataitemmanager
from EasyG.gui import mainwindow
from EasyG.network import server as _server
from EasyG.ecg import exampledata
from EasyG import utils


class EasyG(object):
    def __init__(
        self, server: _server.EasyGAuthenticationServer =
        _server.EasyGAuthenticationServer.from_configuration()
    ):
        super().__init__()

        self.datamanager = plotdataitemmanager.PlotDataManager()
        self.datamanager.apply_configuration()

        self.gui = mainwindow.MainWindow()
        self.gui.OpenExampleRequest.connect(self._onOpenExampleRequest)

        self._server_plugin = utils.ServerPlugin(self.gui, server)
        self._server_plugin.NewClientAvailable.connect(
            self._on_new_server_client)

    def _on_new_server_client(self, client):
        tabName = client.getClientID()
        tab = self.gui.centralWidget().addTab(tabName)

        self.datamanager.register_network_client(tab_name=tabName, client=client)
        plotItem = self.datamanager.get_network_plotitem(
            tab_name=tabName, client_id=client.getClientID()
        )
        # create the first column of plots and insert the first plotter
        tab.insertColumn(0)
        tab.insertPlotWidget(0, 0, title=tabName)
        tab.addItemToPlot(0, 0, plotItem)

        client.startParsing()

    def _onOpenExampleRequest(self):
        x, y, exampleName = exampledata.openExample()
        if x is None or y is None:
            return

        tabName = f"{exampleName.split('.')[0]} Example"
        self.createNewTab(tabName=tabName, plotName="Plot 1",
                          itemName=exampleName, data=(x, y))

    def createNewTab(self, tabName, plotName, itemName, data):
        self.datamanager.register_static_data(tab_name=tabName, data_name=plotName, data=data)
        plotItem = self.datamanager.get_static_plotitem(
            tab_name=tabName, data_name=plotName, plotitem_name=itemName)
        tab = self.gui.tabManager.addTab(tabName)

        # create the first column of plots and insert the first plotter
        tab.insertColumn(0)
        tab.insertPlotWidget(0, 0, title=plotName)
        tab.addItemToPlot(0, 0, plotItem)

        # if this is the first tab, add the dock widget as normal
#        if self.gui.tabManager.count() == 1:
#            self.gui.addDockWidget(Qt.LeftDockWidgetArea, tab.dockWidget)
#
#        # otherwise create tabified dock widgets
#        else:
#            dock = self.gui.tabManager.currentWidget().dockWidget
#            self.gui.tabifyDockWidget(dock, tab.dockWidget)
