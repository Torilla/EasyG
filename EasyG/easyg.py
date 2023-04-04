from EasyG.datautils import plotdatamanager
from EasyG.gui import guiwidgets
from EasyG.network import server as _server
from EasyG.ecg import exampledata
from EasyG import utils


class EasyG(object):
    def __init__(
        self, server: _server.EasyGAuthenticationServer =
        _server.EasyGAuthenticationServer.from_configuration()
    ):
        super().__init__()

        self.datamanager = plotdatamanager.PlotDataManager()

        self.gui = guiwidgets.MainWindow()
        self.gui.OpenExampleRequest.connect(self._onOpenExampleRequest)

        self._server_plugin = utils.ServerPlugin(self.gui, server)
        self._server_plugin.NewClientAvailable.connect(
            self._on_new_server_client)

    def _on_new_server_client(self, client):
        tabName = client.getClientID()
        tab = self.gui.centralWidget().addTab(tabName)

        data_id = self.datamanager.register_network_client(client=client)
        plotitem = self.datamanager.get_managed_plotitem(data_id=data_id)
        plotwidget = self.datamanager.get_managed_plotwidget()
        plotwidget.addItem(plotitem)
        # create the first column of plots and insert the first plotter
        tab.insert_column(0)
        tab.insert_widget(0, 0, plotwidget)

        client.startParsing()

    def _onOpenExampleRequest(self):
        x, y, exampleName = exampledata.openExample()
        if x is None or y is None:
            return

        tabName = f"{exampleName.split('.')[0]} Example"
        self.createNewTab(tabName=tabName, plotName="Plot 1",
                          itemName=exampleName, data=(x, y))

    def createNewTab(self, tabName, plotName, itemName, data):
        data_id = self.datamanager.register_data_source(data=data)
        plotitem = self.datamanager.get_managed_plotitem(data_id=data_id)
        tab = self.gui.tabManager.addTab(tabName)
        plotwidget = self.datamanager.get_managed_plotwidget()
        plotwidget.addItem(plotitem)
        # create the first column of plots and insert the first plotter
        tab.insert_column(0)
        tab.insert_widget(0, 0, plotwidget)
