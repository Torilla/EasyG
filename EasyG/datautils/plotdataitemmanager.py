import pathlib

import pyqtgraph as pg

from EasyG.datautils import filesystem
from EasyG.network import client as _client


class DataItemAlreadyExists(Exception):

    """Raised when trying to register a data source with a name that has
    alrady been registred
    """

    pass


class ClientIDAlreadyRegisteredError(DataItemAlreadyExists):

    """Raised when trying to register a network client with the same ID as
    one that has already been registered
    """

    pass


class PlotDataManager:

    """class PlotDataManager

    This class is responsible for storing data, creating plotitems associated
    with this data and updating plotitems in case the underlying data changes.
    It also provides acces to the raw data.
    """

    TABS_DIR: pathlib.Path = pathlib.Path("/tabs")
    STATIC_DATA_DIR: pathlib.Path = pathlib.Path("/tabs/static_data")
    NETWORK_CLIENTS_DIR: pathlib.Path = pathlib.Path("/tabs/network_clients")
    RAW_DATA_FILE: str = "raw_data.dat"
    PLOTITEM_DIR_NAME: str = "plotitems"

    plotitem_type: type[pg.PlotDataItem] = pg.PlotDataItem

    def __init__(self) -> None:
        """Initialize a new PlotDataManager instance
        """
        self.shell: filesystem.StupidlySimpleShell = filesystem.StupidlySimpleShell()

        self.shell.mkdir(self.TABS_DIR)
        self.shell.mkdir(self.STATIC_DATA_DIR)
        self.shell.mkdir(self.NETWORK_CLIENTS_DIR)

    def _update_plot_items(self, data_path: pathlib.Path) -> None:
        """Update all plotitems that are associated with data stored at
        data_path with the current data.

        Args:
            data_path (pathlib.Path): The path to the dataobject.
        """
        tabdir = data_path.parent
        plotitem_file = (tabdir / self.PLOTITEM_DIR_NAME
                         / f"{tabdir.name}.plotitem")

        data = self.shell.get_file(data_path).data()
        file = self.shell.get_file(plotitem_file)
        file.data().setData(*data)

    def register_static_data(
        self, name: str, data: tuple[list[float], list[float]]
    ) -> pg.PlotDataItem:
        """Register a new static data source. The PlotDataManager will store
        the data, create a plotitem associated with this data and update the
        plotitem whenever the data changes. The plotitem is returned so it can
        be added to a pg.PlotWidget instance.

        Args:
            name (str): The name of the new plotitem
            data (tuple[list[float], list[float]]): The data to display in the
                plotitem
        """
        with self.shell.managed_cd(self.STATIC_DATA_DIR) as shell:
            # create directory for this dataitem at /tabs/static_data/name
            try:
                shell.mkdir(name)
            except filesystem.InvalidPathError:
                raise DataItemAlreadyExists(name)

            # create the file to store the data at
            # /tabs/static_data/name/raw_data.dat
            shell.cd(name)
            file = filesystem.PointListFileObject(name=self.RAW_DATA_FILE)
            shell.add_file(file)
            # notify the plotitems when data has changed
            shell.add_file_watcher(self.RAW_DATA_FILE, self._update_plot_items)

            # create plotitem dir and add a plotitem to it at
            # /tabs/static_data/name/plotitems/name.plotitem
            shell.mkdir(self.PLOTITEM_DIR_NAME)
            shell.cd(self.PLOTITEM_DIR_NAME)

            plotitem = self.plotitem_type(name=name)
            plotfile = filesystem.FileObject(name=f"{name}.plotitem",
                                             data=plotitem)
            shell.add_file(plotfile)

            # return the ploitem for further processing
            return plotitem

    def register_networkclient(
        self, client: _client.EasyGTCPClient
    ) -> pg.PlotDataItem:
        """Register a new network client. The PlotDataManager will store the
        network client, create a plotitem associated with the data coming from
        the network client and update the plotitem whenever new data arrives
        form the network client. The plotitem is returned so it can be added
        to a pg.PlotWidget instance.

        Args:
            client (_client.EasyGTCPClient): The network client to register.
        """
        with self.shell.managed_cd(self.NETWORK_CLIENTS_DIR) as shell:
            clientdir = client.getClientID()

            # create a new directory for this client
            try:
                shell.mkdir(clientdir)
            except filesystem.InvalidPathError:
                raise ClientIDAlreadyRegisteredError(clientdir)

            # change into /tabs/network_clients/clientID
            shell.cd(clientdir)

            # create File to store the data in
            # /tabs/network_clients/clientID/raw_data.dat
            file = filesystem.PointListFileObject(
                name=self.RAW_DATA_FILE)
            shell.add_file(file)
            # pipe new client data into the file
            client.newLineOfData.connect(file.appendPoint)
            # notify plotitems when data has changed
            shell.add_file_watcher(self.RAW_DATA_FILE, self._update_plot_items)

            # create a subdir for the plotitems at /tabs/clientID/plotitems
            shell.mkdir(self.PLOTITEM_DIR_NAME)
            # change into it
            shell.cd(self.PLOTITEM_DIR_NAME)

            # create a new plotitem as well as a file to store it in at
            # /tabs/clientID/plotitems/clientID.plotitem
            plotitem = self.plotitem_type(name=clientdir)
            plotfile = filesystem.FileObject(name=f"{clientdir}.plotitem",
                                             data=plotitem)
            shell.add_file(plotfile)

            # return the plotitem for further processing
            return plotitem
