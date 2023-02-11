import pyqtgraph as pg

from . import filesystem


class PlotDataItemManager(object):
    plotItemType = pg.PlotDataItem
    _plotItemsPathTmplt = "{}" + f"{filesystem.SEP}{plotItemType.__name__}s"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # the FileSystem stores the actual data
        self.fs = filesystem.FileSystem()

    def _pipeDataToPlotItems(self, path: str):
        for plotItem in self.getPlotItems(path):
            plotItem.setData(*self.fs.getData(path))

    def registerPlotItemData(self, path: str, data):
        self.fs.mkdir(path=path, data=data)

        plotItem = self.plotItemType(*data, name=path)
        plotItemPath = self._plotItemsPathTmplt.format(path)
        self.fs.mkdir(path=plotItemPath, data=[plotItem])

        self.fs.watchData(path, self._pipeDataToPlotItems)

        return plotItem

    def registerNetworkClientPlotItem(self, path, client):
        client = filesystem.NetworkClientDataObject(client)
        self.fs.mkdir(path, data=client)
        plotItem = self.plotItemType(*client.data(), name=path)
        plotItemPath = self._plotItemsPathTmplt.format(path)
        self.fs.mkdir(path=plotItemPath, data=[plotItem])

        client.DataChanged.connect(lambda: self._pipeDataToPlotItems(path))
        client.startParsing()

        return plotItem

    def getPlotItems(self, dataPath):
        path = self._plotItemsPathTmplt.format(dataPath)
        return self.fs.getDataObject(path).data()
