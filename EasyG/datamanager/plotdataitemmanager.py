import pyqtgraph as pg

from . import filesystem


class PlotDataItemManager(object):
    plotItemType = pg.PlotDataItem
    _plotItemsPathTmplt = "{}" + f"{filesystem.SEP}{plotItemType.__name__}s"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # the FileSystem stores the actual data
        self.fs = filesystem.FileSystem()

    def _pipeDataToPlotItems(self, path: str, obj: filesystem.DataObject):
        for plotItem in self.fs.getDataObject(path).data():
            plotItem.setData(*obj.data())

    def registerDataObject(self, obj: filesystem.DataObject, path: str):
        self.fs.mkdir(path=path, data=obj)

        plotItem = self.plotItemType(*obj.data(), name=path)
        plotItemPath = self._plotItemsPathTmplt.format(path)
        self.fs.mkdir(path=plotItemPath, data=filesystem.DataObject([plotItem]))

        obj.DataChanged.connect(
            lambda data: self._pipeDataToPlotItems(plotItemPath, data))

    def getPlotItems(self, dataPath):
        path = self._plotItemsPathTmplt.format(dataPath)
        return self.fs.getDataObject(path).data()
