from PyQt5.QtCore import Qt

from EasyG.datautils import plotdataitemmanager
from EasyG.gui import mainwindow
from EasyG.network import server as _server
from EasyG.ecg import exampledata
from EasyG.gui import widgets


class EasyG(object):
    def __init__(
        self, server: _server.EasyGAuthenticationServer =
        _server.EasyGAuthenticationServer.from_config()
    ):
        super().__init__()

        self.datamanager = plotdataitemmanager.PlotDataManager()

        self.gui = mainwindow.MainWindow()
        self.gui.OpenExampleRequest.connect(self._onOpenExampleRequest)

        self._start_con = self._stop_con = self._newclient_con = self._conf_con = None
        self.set_server_plugin(server)

    def set_server_plugin(
        self, server: _server.EasyGAuthenticationServer
    ) -> None:
        if getattr(self, "server", None) is not None:
            self.stop_server()

        self.gui.startServerAction.setEnabled(False)
        self.gui.stopServerAction.setEnabled(False)
        if self._start_con:
            self.gui.startServerAction.disconnect(self._start_con)
            self._start_con = None
        if self._stop_con:
            self.gui.stopServerAction.disconnect(self._stop_con)
            self._stop_con = None
        if self._newclient_con:
            self.server.NewClientAvailable.disconnect(self._newclient_con)
            self.server._newclient_con = None
        if self._conf_con:
            self.gui.configureServerAction.disconnect(self._conf_con)
            self._conf_con = None

        self.server = server
        if self.server is not None:
            self._server_config_widget = widgets.ServerConfigurationWidget(
                **self.server.configuration())
            self._server_config_widget.ConfigurationChanged.connect(
                self._on_server_configuration_changed)
            self._conf_con = self.gui.configureServerAction.triggered.connect(
                self._server_config_widget.show)
            self.gui.startServerAction.setEnabled(True)
            self._stop_con = self.gui.stopServerAction.triggered.connect(
                self.stop_server)
            self._start_con = self.gui.startServerAction.triggered.connect(
                self.start_server)
            self._newclient_con = self.server.NewClientAvailable.connect(
                self._onNewServerClient)

        self.gui.print_status("Updated the server configuration.")

    def _on_server_configuration_changed(self):
        config = self._server_config_widget.get_configuration()
        server = _server.EasyGAuthenticationServer.from_config(config)
        self.set_server_plugin(server)

    def start_server(self):
        if not self.server.is_listening():
            try:
                self.server.start_listening()

            except OSError:
                err = self.server.error_string()
                status = f"Failed to start server: {err}"

            else:

                self.gui.startServerAction.setEnabled(False)
                self.gui.stopServerAction.setEnabled(True)
                self.gui.configureServerAction.setEnabled(False)
                address = self.server.server_address().toString()
                port = self.server.server_port()
                status = f"Server listening at {address}:{port}."

        else:
            address = self.server.server_address().toString()
            status = "Server is already listening at {address}."

        self.gui.print_status(status)

    def stop_server(self):
        if self.server.is_listening():
            self.server.close()
            self.gui.stopServerAction.setEnabled(False)
            self.gui.startServerAction.setEnabled(True)
            self.gui.configureServerAction.setEnabled(True)
            self.gui.print_status("Server stopped listening.")

    def _onNewServerClient(self, client):
        tabName = client.getClientID()
        tab = self.gui.centralWidget().addTab(tabName)

        plotItem = self.datamanager.register_networkclient(client)
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
        plotItem = self.datamanager.register_static_data(
            name=itemName, data=data)
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
