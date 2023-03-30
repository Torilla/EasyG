from collections import namedtuple
import pathlib

import pyqtgraph as pg

from EasyG import defaults
from EasyG.datautils import filesystem, fsutils
from EasyG.network import client as _client


class PlotDataManagerError(Exception):

    """Raise when a PlotDataManager operation fails"""


class DataItemAlreadyExists(PlotDataManagerError):

    """Raised when trying to register a data source with a name that has
    alrady been registred
    """


class PlotitemAlreadyExistsError(DataItemAlreadyExists):

    """Raised when trying to create a new managed plotitem with a name
    that has already been registered.
    """


class ClientIDAlreadyRegisteredError(DataItemAlreadyExists):

    """Raised when trying to register a network client with the same ID as
    one that has already been registered
    """


class NoSuchDataItemError(PlotDataManagerError):

    """Raised when trying to create a new plotitem from a data source that
    has not been regeistered before.
    """


class PlotDataManager:

    """class PlotDataManager

    This class is responsible for storing data, creating plotitems associated
    with this data and updating plotitems in case the underlying data changes.
    It also provides acces to the raw data.
    """

    plotitem_type: type[pg.PlotDataItem] = pg.PlotDataItem

    def __init__(self) -> None:
        """Initialize a new PlotDataManager instance
        """
        self.shell = filesystem.StupidlySimpleShell()

    def apply_configuration(
        self, config: dict = defaults.Config["PlotDataManager"]
    ) -> None:
        configuration = namedtuple("configuration", ("filesystem",
                                                     "static_data",
                                                     "network_clients"))
        self._config = configuration(**config)
        self._apply_filesystem_config()

    def _apply_filesystem_config(self):
        def generate_filesystem_recursivley(nodes):
            for node in nodes:
                name = node["name"]
                self.shell.mkdir(name)
                self.shell.cd(name)
                generate_filesystem_recursivley(node.get("children", []))
                self.shell.cd("..")

        generate_filesystem_recursivley(self._config.filesystem)

    def _update_plotitems(self, path: pathlib.Path):
        data = self.shell.get_data(path)

        with self.shell.managed_cd(path.parent):
            self.shell.cd(self._config.static_data["plotitem_dir"])
            for file in self.shell.ls():
                self.shell.get_data(file).setData(*data)

    def get_static_plotitem(
        self, tab_name: str, data_name: str, plotitem_name: str
    ) -> pg.PlotDataItem:
        cfg = self._config.static_data
        root_dir = pathlib.Path(cfg["root_dir"])

        data_dir = root_dir / cfg["data_dir"].format(tab_name=tab_name)
        data_file = data_dir / cfg["data_file"].format(data_name=data_name)
        try:
            data = self.shell.get_data(data_file)
        except filesystem.InvalidPathError:
            raise NoSuchDataItemError(data_file) from None

        plotitem_dir = data_dir / cfg["plotitem_dir"]
        plotitem_file = plotitem_dir / cfg["plotitem_file"].format(plotitem_name=plotitem_name)

        try:
            self.shell.touch(plotitem_file)
        except filesystem.InvalidPathError:
            raise DataItemAlreadyExists(plotitem_file) from None

        plotitem = self.plotitem_type(*data)
        self.shell.set_data(plotitem_file, plotitem)

        return plotitem

    def register_static_data(
        self,
        tab_name: str,
        data_name: str,
        data: tuple[list[float], list[float]]
    ):

        cfg = self._config.static_data
        root_dir = pathlib.Path(cfg["root_dir"])

        data_dir = root_dir / cfg["data_dir"].format(tab_name=tab_name)
        data_file = data_dir / cfg["data_file"].format(data_name=data_name)

        try:
            self.shell.mkdir(data_dir)
        except filesystem.InvalidPathError:
            raise DataItemAlreadyExists(data_dir) from None

        self.shell.touch(data_file, file_type=fsutils.TwoDimensionalPointArrayFile)

        self.shell.set_data(data_file, data)
        self.shell.watch_file(data_file, self._update_plotitems)

        plotitem_dir = data_dir / cfg["plotitem_dir"]
        self.shell.mkdir(plotitem_dir)

    def get_network_plotitem(self, tab_name: str, client_id: str) -> pg.PlotDataItem:
        cfg = self._config.network_clients
        root_dir = pathlib.Path(cfg["root_dir"])

        data_dir = root_dir / cfg["data_dir"].format(tab_name=tab_name)
        data_file = data_dir / cfg["data_file"].format(client_id=client_id)
        try:
            data = self.shell.get_data(data_file)
        except filesystem.InvalidPathError:
            raise NoSuchDataItemError(data_file) from None

        plotitem_dir = data_dir / cfg["plotitem_dir"]
        plotitem_file = plotitem_dir / cfg["plotitem_file"].format(client_id=client_id)

        try:
            self.shell.touch(plotitem_file)
        except filesystem.InvalidPathError:
            raise DataItemAlreadyExists(plotitem_file) from None

        plotitem = self.plotitem_type(*data)
        self.shell.set_data(plotitem_file, plotitem)

        return plotitem

    def register_network_client(self, tab_name: str, client: _client.EasyGTCPClient):
        cfg = self._config.network_clients
        root_dir = pathlib.Path(cfg["root_dir"])

        data_dir = root_dir / cfg["data_dir"].format(tab_name=tab_name)
        data_file = data_dir / cfg["data_file"].format(client_id=client.getClientID())

        try:
            self.shell.mkdir(data_dir)
        except filesystem.InvalidPathError:
            raise ClientIDAlreadyRegisteredError(data_dir) from None

        self.shell.touch(data_file, file_type=fsutils.NetworkClientFile)
        file = self.shell.filesystem.get_node(data_file)
        file.set_client(client)

        self.shell.watch_file(data_file, self._update_plotitems)

        plotitem_dir = data_dir / cfg["plotitem_dir"]
        self.shell.mkdir(plotitem_dir)
