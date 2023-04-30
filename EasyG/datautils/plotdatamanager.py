import pathlib

import pyqtgraph as pg

from EasyG import defaults
from EasyG.datautils import sssh, fsutils
from EasyG.gui import widgets

Data_T = tuple[list[float], list[float]]

# required for setting network clients
fsutils.load_shell_extensions()


class PlotDataManager:
    def __init__(
        self, config: defaults.Config_T = defaults.Config.get("PlotDataManager")
    ):
        self._config = config
        self.shell = sssh.StupidlySimpleShell()
        self._reset_shell()

    def _reset_shell(self):
        def reset_shell():
            self.shell.cd("/")
            for path in self.shell.ls():
                self.shell.rm(path, recursive=True)

        def make_fs(nodes):
            def import_metadata():
                for cfg in node.get("files", {}).values():
                    mod, cls = cfg.get("file_type", "sssh.LeafNode").split(".")
                    cfg["file_type"] = getattr(globals()[mod], cls)

            for node in nodes:
                import_metadata()

                if isinstance(node, str):
                    name, children = node, []
                else:
                    name, children = node.get("name"), node.get("children", [])

                self.shell.mkdir(name)
                with self.shell.managed_cd(name):
                    self.shell.set_metadata(".", "files", node["files"])
                    make_fs(children)

        reset_shell()
        make_fs(self._config.get("filesystem"))

    def _update_plotitems(self, path: pathlib.Path):
        id_ = path.stem
        data = self.shell.get_data(path)
        for item in self.shell.ls(f"data/plotitems/{id_}/"):
            self.shell.get_data(f"data/plotitems/{id_}/{item}").setData(*data)

    def register_data_source(
        self, data: Data_T, file_type=fsutils.TwoDimensionalPointArrayFile
    ):
        id_ = str(id(data))
        meta = self.shell.get_metadata("data", "files")["default"]
        path = f"data/{id_}{meta['suffix']}"
        self.shell.touch(path, file_type=meta["file_type"])
        self.shell.set_data(path, data)
        self.shell.mkdir(f"data/plotitems/{id_}")
        self.shell.watch_file(path, self._update_plotitems)

        return id_

    def remove_data_source(self, data_id):
        meta = self.shell.get_metadata("data", "files")["default"]
        self.shell.unwatch_file(f"data/{data_id}{meta['suffix']}")
        self.shell.rm(f"data/plotitems/{data_id}", recursive=True)

        return self.shell.rm(f"data/{data_id}{meta['suffix']}").data

    def register_network_client(self, client):
        id_ = str(id(client))
        meta = self.shell.get_metadata("data", "files")["network_clients"]
        path = f"data/{id_}{meta['suffix']}"
        self.shell.touch(path, file_type=meta["file_type"])
        self.shell.set_client(path, client)
        self.shell.mkdir(f"data/plotitems/{id_}")
        self.shell.watch_file(path, self._update_plotitems)

        return id_

    def get_managed_plotitem(self, data_id, item_type=pg.PlotDataItem, file_type="default"):
        meta = self.shell.get_metadata("data", "files")[file_type]
        path = f"data/{data_id}{meta['suffix']}"
        data = self.shell.get_data(path)
        plotitem = item_type(*data)

        meta = self.shell.get_metadata("data/plotitems", "files")["default"]
        path = f"data/plotitems/{data_id}/{id(plotitem)}{meta['suffix']}"
        self.shell.touch(path)
        self.shell.set_data(path, plotitem)

        return plotitem

    def remove_managed_plotitem(self, item_id, data_id):
        meta = self.shell.get_metadata("data/plotitems", "files")["default"]

        return self.shell.rm(f"data/plotitems/{data_id}/{item_id}{meta['suffix']}").data

    def get_managed_plotwidget(self):
        widget = widgets.EasyGPlotWidget()
        meta = self.shell.get_metadata("plotwidgets", "files")["default"]
        path = f"plotwidgets/{id(widget)}{meta['suffix']}"
        self.shell.touch(path, file_type=meta['file_type'])
        self.shell.set_data(path, widget)

        return widget

    def remove_managed_plotwidget(self, widget_id):
        meta = self.shell.get_metadata("plotwidgets", "files")["default"]

        return self.shell.rm(f"plotwidgets/{widget_id}{meta['suffix']}").data
