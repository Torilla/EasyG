import pathlib

import pyqtgraph as pg

from EasyG import defaults
from EasyG.datautils import filesystem, fsutils
from EasyG.gui import widgets

fsutils.load_shell_extensions()
Data_T = tuple[list[float], list[float]]


class PlotDataManager:
    def __init__(
        self, config: defaults.Config_T = defaults.Config.get("PlotDataManager")
    ):
        self._config = config
        self.shell = filesystem.StupidlySimpleShell()
        self._reset_shell()

    def _reset_shell(self, config: defaults.Config_T | None = None):
        def reset_fs():
            for path in self.shell.ls():
                self.shell.rm(path, recursive=True)

        def make_fs(nodes):
            for node in nodes:
                if isinstance(node, str):
                    name, children = node, []
                else:
                    name, children = node.get("name"), node.get("children", [])

                self.shell.mkdir(name)
                self.shell.cd(name)
                make_fs(children)
                self.shell.cd("..")

        reset_fs()
        make_fs(config or self._config.get("filesystem"))

    def _update_plotitems(self, path: pathlib.Path):
        id_ = path.name.removesuffix(".dat")
        data = self.shell.get_data(path)
        for item in self.shell.ls(f"plotitems/{id_}/"):
            self.shell.get_data(f"plotitems/{id_}/{item}").setData(*data)

    def register_data_source(
        self, data: Data_T, file_type=fsutils.TwoDimensionalPointArrayFile
    ):
        id_ = str(id(data))
        path = f"data/{id_}.dat"
        self.shell.touch(path, file_type=file_type)
        self.shell.set_data(path, data)
        self.shell.mkdir(f"plotitems/{id_}")
        self.shell.watch_file(path, self._update_plotitems)

        return id_

    def register_network_client(self, client):
        id_ = id(client)
        path = f"data/{id_}.dat"
        self.shell.touch(path, file_type=fsutils.NetworkClientFile)
        self.shell.set_client(path, client)
        self.shell.mkdir(f"plotitems/{id_}")
        self.shell.watch_file(path, self._update_plotitems)

        return id_

    def get_managed_plotitem(self, data_id, item_type=pg.PlotDataItem):
        path = f"data/{data_id}.dat"
        data = self.shell.get_data(path)
        plotitem = item_type(*data)
        path = f"plotitems/{data_id}/{id(plotitem)}.plotitem"
        self.shell.touch(path)
        self.shell.set_data(path, plotitem)

        return plotitem

    def get_managed_plotwidget(self, widget_id=None):
        if widget_id:
            widget = self.shell.get_data(f"plotwidgets/{widget_id}.plotwidget")

        else:
            widget = widgets.EasyGPlotWidget()
            path = f"plotwidgets/{id(widget)}.plotwidget"
            self.shell.touch(path)
            self.shell.set_data(path, widget)

        return widget
