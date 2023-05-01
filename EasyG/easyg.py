from EasyG.datautils import plotdatamanager
from EasyG.gui import guiwidgets
from EasyG.network import server as _server
from EasyG.ecg import exampledata
from EasyG import utils


class EasyG(object):
    def __init__(
        self,
        server: _server.EasyGAuthenticationServer = _server.EasyGAuthenticationServer.from_configuration(),
    ):
        super().__init__()

        self.datamanager = plotdatamanager.PlotDataManager()
        # map plotitem_id -> data_id the plotitem is constructed from
        self._data_id_map: dict[int, int] = {}

        self.mainWindow = guiwidgets.MainWindow()
        self.mainWindow.OpenExampleRequest.connect(self._on_open_example_request)

        self.tabManager = guiwidgets.TabManagerWidget()
        self.mainWindow.setCentralWidget(self.tabManager)

        self._server_plugin = utils.ServerPlugin(self.mainWindow, server)
        self._server_plugin.NewClientAvailable.connect(self._on_new_server_client)

    def _on_new_server_client(self, client):
        tab_name = client.getClientID()

        data_id = self.datamanager.register_network_client(client=client)
        self.create_new_tab(
            tab_name=tab_name,
            plot_name="Plot 1",
            item_name="test item",
            data_id=data_id,
            file_type="network_clients",
        )
        client.startParsing()

    def _on_open_example_request(self):
        x, y, exampleName = exampledata.openExample()
        if x is None or y is None:
            return

        tab_name = f"{exampleName.split('.')[0]} Example"
        data_id = self.datamanager.register_data_source(data=(x, y))
        self.create_new_tab(
            tab_name=tab_name,
            plot_name="Plot 1",
            item_name="Test item",
            data_id=data_id,
        )

    def create_new_tab(
        self, tab_name, plot_name, item_name, data_id, file_type="default"
    ):
        plotitem, id_ = self.datamanager.get_managed_plotitem(
            data_id=data_id, file_type=file_type
        )
        self._data_id_map[id_] = data_id
        plotitem.set_title(item_name)

        plotwidget, plotwidget_id = self.datamanager.get_managed_plotwidget()
        plotwidget.set_title(plot_name)
        plotwidget.addItem(plotitem)

        tab = self.tabManager.add_tab(tab_name)
        tab.WidgetInsertRequest.connect(self._on_tab_widget_insert_request)
        tab.WidgetRemoveRequest.connect(self._on_tab_widget_remove_request)
        tab.insert_column(0)
        tab.insert_widget(0, 0, plotwidget)

        return plotwidget_id

    def _on_tab_widget_insert_request(self, tabWidget, columnIdx, rowIdx):
        # request user input what should be plotted
        plotwidget, plotwidget_id = self.datamanager.get_managed_plotwidget()
        tabWidget.insert_widget(columnIdx, rowIdx, plotwidget)

    def _on_tab_widget_remove_request(self, tabWidget, columnIdx, rowIdx):
        plotwidget = tabWidget.remove_widget(columnIdx, rowIdx)

        for item in plotwidget.listDataItems():
            item_id = id(item)
            data_id = self._data_id_map[item_id]
            self.datamanager.remove_managed_plotitem(data_id, item_id).deleteLater()
            del self._data_id_map[item_id]

        self.datamanager.remove_managed_plotwidget(id(plotwidget)).deleteLater()
