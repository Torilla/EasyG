from PyQt5 import QtCore
import pyqtgraph as pg

from . import filesystem


class PlotDataItemManager(QtCore.QObject):
    plotItemType = pg.PlotDataItem
    _plotItemsPathTmplt = "{}" + f"{filesystem.SEP}{plotItemType.__name__}s"

    AvailableDataChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # the FileSystem stores the actual data
        self.fs = filesystem.FileSystem()

    def _pipeDataToPlotItems(self, path: str):
        for plotItem in self.getPlotItems(path):
            plotItem.setData(*self.fs.getData(path))

    def registerPlotItemData(self, path: str, data, plotItemName=None):
        self.fs.mkdir(path=path, data=data)

        plotItem = self.plotItemType(*data, name=plotItemName or path)
        plotItemPath = self._plotItemsPathTmplt.format(path)

        self.fs.mkdir(path=plotItemPath, data=[plotItem])
        self.fs.watchData(path, self._pipeDataToPlotItems)

        self.AvailableDataChanged.emit()

        return plotItem

    def registerNetworkClientPlotItem(self, path, client, plotItemName=None):
        client = filesystem.NetworkClientDataObject(client)
        self.fs.mkdir(path, data=client)
        plotItem = self.plotItemType(*client.data(), name=plotItemName or path)
        plotItemPath = self._plotItemsPathTmplt.format(path)
        self.fs.mkdir(path=plotItemPath, data=[plotItem])

        client.DataChanged.connect(lambda: self._pipeDataToPlotItems(path))
        client.startParsing()

        self.AvailableDataChanged.emit()

        return plotItem

    def getPlotItems(self, dataPath):
        path = self._plotItemsPathTmplt.format(dataPath)
        return self.fs.getData(path)

    def getPlotDataItemConfiguration(self):
        return {dataNode: [item.name() for item in self.getPlotItems(f"{filesystem.ROOT}{dataNode}")]
                for dataNode in self.fs.ls(filesystem.ROOT)}
