import pathlib

import pyqtgraph as pg

from EasyG.datautils import filesystem
from EasyG.network import client as _client


class ClientIDAlreadyRegisteredError(ValueError):
    pass


class PlotDataManager:
    TABS_DIR = pathlib.Path("/tabs")
    STATIC_DATA_DIR = pathlib.Path("/tabs/static_data")
    NETWORK_CLIENTS_DIR = pathlib.Path("/tabs/network_clients")
    NETWORK_CLIENTS_DATA_FILE = pathlib.Path("raw_data.dat")
    PLOTITEM_DIR_NAME = "plotitems"

    plotItemType = pg.PlotDataItem

    def __init__(self):
        self.shell = filesystem.StupidlySimpleShell()

        self.shell.mkdir(self.TABS_DIR)
        self.shell.mkdir(self.STATIC_DATA_DIR)
        self.shell.mkdir(self.NETWORK_CLIENTS_DIR)

    def _update_plot_item(self, plotitem_path):
        print("hi")
        dataFile = plotitem_path.parent / self.NETWORK_CLIENTS_DATA_FILE
        data = self.shell.get_file(dataFile).data()
        self.shell.get_file(plotitem_path).data().setData(*data)

    def register_networkclient(self, client: _client.EasyGTCPClient) -> None:
        with self.shell.managed_cd(self.NETWORK_CLIENTS_DIR) as shell:
            clientid = client.getClientID()

            try:
                shell.mkdir(clientid)
            except filesystem.InvalidPathError:
                raise ClientIDAlreadyRegisteredError(clientid)

            shell.cd(clientid)

            file = shell.touch(self.NETWORK_CLIENTS_DATA_FILE,
                               file_type=filesystem.PointListFileObject)
            client.newLineOfData.connect(file.appendPoint)

            shell.mkdir(self.PLOTITEM_DIR_NAME)
            plotItem = pg.PlotDataItem(name=clientid)
            file = shell.touch(clientid)
            file.set_data(plotItem)

            shell.add_file_watcher(clientid, self._update_plot_item)
