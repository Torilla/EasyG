from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QGridLayout, QSizePolicy
from PyQt5.QtWidgets import QSplitter, QGroupBox, QFrame

import pyqtgraph as pg

from EasyG.config import setPyqtgraphConfig
from EasyG.gui.analyzewidget import MainAnalyzePlotWidget
from EasyG.gui.analyzewidget import ProcessResultTableWidget
from EasyG import ecganalysis

_CONFIG = setPyqtgraphConfig()


class PlotDataItem(pg.PlotDataItem):
    def __init__(self, *args, _ID=None, **kwargs):
        super().__init__(*args, **kwargs)

        self._ID = _ID or id(self)
        self._args = args
        self._kwargs = kwargs

    def copy(self):
        return type(self)(*self._args, _ID=self.id(), **self._kwargs)

    def id(self):
        return self._ID


class PlotWidget(pg.PlotWidget):
    # (lower, upper) x-bound of the roi in coordinates of the axis
    ROICoordinatesChanged = pyqtSignal(float, float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Region of Interest upon double click
        self._ROI = None

        # drag conenction while ROI is being drawn
        self._conROI = None

    def getROI(self):
        return self._ROI

    def setROI(self, roi):
        if roi is None:
            # unset Roi if it exists
            if (_roi := self.getROI()) is not None:
                self.removeItem(_roi)
                _roi.deleteLater()

        else:
            # set Roi
            self.addItem(roi)

        self._ROI = roi

    def setRectROI(self):
        roi = pg.RectROI(pos=self._posROI, size=(0, 0), pen="g",
                         invertible=True, sideScalers=True)
        self.setROI(roi)

    def RoiIsConnected(self):
        return self._conROI is not None

    def connectRoiDrag(self):
        self._conROI = self.scene().sigMouseMoved.connect(self._dragRectRoi)

    def disconnectRoiDrag(self):
        self.scene().sigMouseMoved.disconnect(self._conROI)
        self._conROI = None

    def _dragRectRoi(self, pos):
        pos = self.getViewBox().mapSceneToView(pos)
        size = pos - self._posROI
        self.getROI().setSize(size)
        self.ROICoordinatesChanged.emit(self._posROI.x(), pos.x())

    def mouseDoubleClickEvent(self, event):
        event.accept()

        if self.getROI() is not None:
            self.setROI(None)

        self._posROI = self.getViewBox().mapSceneToView(event.pos())
        self.setRectROI()

        # connect dragging of the ROI
        self.connectRoiDrag()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton and self.getROI() is not None:
            event.accept()
            self.setROI(None)

        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if not self.RoiIsConnected():
            super().mouseReleaseEvent(event)

        else:
            event.accept()
            self.disconnectRoiDrag()


class FramedPlotWidget(QFrame):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFrameStyle(QFrame.Box | QFrame.Raised)
        self.setLineWidth(1)
        self.setMidLineWidth(1)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        layout = QGridLayout()
        self.setLayout(layout)

        self.plotWidget = PlotWidget()
        layout.addWidget(self.plotWidget, 0, 0)

        self.resultTableWidget = ProcessResultTableWidget()
        layout.addWidget(self.resultTableWidget, 0, 0,
                         Qt.AlignTop | Qt.AlignRight)

    def __getattribute__(self, attr):
        # delegate attribute lookup to the plot widget

        try:
            attr = super().__getattribute__(attr)

        except AttributeError as err:
            attr = getattr(super().__getattribute__("plotWidget"), attr, None)

            if attr is None:
                raise err from None

        return attr

    def sizeHint(self):
        return QSize(640, 480)

    def setResultsTable(self, results):
        self.resultTableWidget.setResults(results)


class MultiPlotWidget(QSplitter):
    # plotterIdx, roi x-bounds
    ROICoordinatesChanged = pyqtSignal(int, tuple)

    def __init__(self, *args, orientation=Qt.Vertical, **kwargs):
        super().__init__(*args, **kwargs)

        self.plotWidgets = []
        self.dataItems = []
        self.setOrientation(orientation)

    def plotCount(self):
        return len(self.plotWidgets)

    def itemCount(self):
        return len(self.dataItems)

    def addPlot(self):
        def _forwardRoiCoordinates(*coords):
            idx = self.plotWidgets.index(plotWidget)
            self.ROICoordinatesChanged.emit(idx, coords)

        plotterIdx = len(self.plotWidgets)
        plotWidget = FramedPlotWidget()
        plotWidget.addLegend()

        plotWidget.ROICoordinatesChanged.connect(_forwardRoiCoordinates)

        self.plotWidgets.append(plotWidget)
        self.addWidget(plotWidget)

        return plotterIdx

    def plotContainsItem(self, plotterIdx, itemIdx):
        ids = [d.id() for d in self.plotWidgets[plotterIdx].listDataItems()]

        return self.dataItems[itemIdx].id() in ids

    def addItemToPlot(self, plotterIdx, itemIdx):
        self.plotWidgets[plotterIdx].addItem(self.dataItems[itemIdx].copy())

    def removeItemFromPlot(self, plotterIdx, itemIdx):
        _id = self.dataItems[itemIdx].id()
        widget = self.plotWidgets[plotterIdx]

        _item = next(w for w in widget.listDataItems() if w.id() == _id)
        widget.removeItem(_item)

    def newDataItem(self, plotterIdx=None, **kwargs):
        itemIdx = len(self.dataItems)

        kwargs["pen"] = kwargs.get("pen", pg.intColor(itemIdx))
        self.dataItems.append(PlotDataItem(**kwargs))

        if plotterIdx is not None:
            self.addItemToPlot(plotterIdx=plotterIdx, itemIdx=itemIdx)

        return itemIdx

    def setItemData(self, itemIdx, *args, **kwargs):
        if args:
            raise NotImplementedError("Positional update not possible")

        self.dataItems[itemIdx]._kwargs.update(kwargs)

        for idx in range(self.plotCount()):
            if self.plotContainsItem(plotterIdx=idx, itemIdx=itemIdx):
                self.removeItemFromPlot(plotterIdx=idx, itemIdx=itemIdx)
                self.addItemToPlot(plotterIdx=idx, itemIdx=itemIdx)

    def getDataFromItemIndex(self, itemIdx):
        return self.dataItems[itemIdx].getData()

    def getNameFromItemIndex(self, itemIdx):
        return self.dataItems[itemIdx].name()

    def setResultsTable(self, plotterIdx, results):
        self.plotWidgets[plotterIdx].setResultsTable(results)


class MainPlotWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QGridLayout()
        self.setLayout(layout)

        self.plotWidget = MultiPlotWidget()
        self.plotWidget.ROICoordinatesChanged.connect(
            self.onRoiCoordinatesChanged)
        layout.addWidget(self.plotWidget, 0, 0)

        self.analyzeWidget = MainAnalyzePlotWidget()
        layout.addWidget(self.analyzeWidget, 1, 0)

        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 1)

        self.analyzeWidget.filterButton().clicked.connect(self.onApplyFilter)
        self.analyzeWidget.processButton().clicked.connect(self.onProcess)

    def addPlot(self, plotterName=None):
        if plotterName is None:
            plotterName = f"Plot {self.plotWidget.plotCount()}"

        self.analyzeWidget.addDataTarget(name=plotterName)

        return self.plotWidget.addPlot()

    def newDataItem(self, plotterIdx=None, name=None, **kwargs):
        if name is None:
            name = f"plot {self.plotWidget.itemCount()}"

        idx = self.plotWidget.newDataItem(plotterIdx=plotterIdx, name=name,
                                          **kwargs)

        x, _ = self.plotWidget.getDataFromItemIndex(idx)
        assert x is not None, ("Empty plot item can not be created! "
                               f"{name}, {kwargs}")
        self.analyzeWidget.addDataSource(name=name, lowerBound=str(x[0]),
                                         upperBound=str(x[-1]))

        return idx

    def setItemData(self, *args, **kwargs):
        self.plotWidget.setItemData(*args, **kwargs)

    def onApplyFilter(self):
        filterOpts = self.analyzeWidget.getFilterOptions()
        itemIdx, plotIdx, bounds, plotName = self.analyzeWidget.getDataSelect()

        name = filterOpts["filtertype"]

        if plotIdx is None:
            plotIdx = self.addPlot(plotterName=plotName)

        x, y = self.plotWidget.getDataFromItemIndex(itemIdx)
        x, y = x[bounds], y[bounds]
        y = ecganalysis.filterSignal(y, **filterOpts)

        self.newDataItem(x=x, y=y, plotterIdx=plotIdx, name=name)

    def onProcess(self):
        processOpts = self.analyzeWidget.getProcessOptions()
        _processor = processOpts.pop("processor")
        processor = ecganalysis.getProcessor(_processor)

        itemIdx, plotIdx, bounds, plotName = self.analyzeWidget.getDataSelect()

        name = _processor

        if plotIdx is None:
            plotIdx = self.addPlot(plotterName=plotName)
            self.plotWidget.addItemToPlot(plotterIdx=plotIdx, itemIdx=itemIdx)

        x, y = self.plotWidget.getDataFromItemIndex(itemIdx)
        x, y = x[bounds], y[bounds]

        results, data = processor(x=x, y=y, processOpts=processOpts)

        _x, _y = data["accepted_peaks"]
        if _x and _y:
            self.newDataItem(x=_x, y=_y, plotterIdx=plotIdx,
                             name=f"{name} (accepted peaks)", pen=None,
                             symbolBrush="g", symbol="o")

        _x, _y = data["rejected_peaks"]
        if _x and _y:
            self.newDataItem(x=_x, y=_y, plotterIdx=plotIdx,
                             name=f"{name} (rejected peaks)", pen=None,
                             symbolBrush="r", symbol="o")

        self.plotWidget.setResultsTable(plotterIdx=plotIdx, results=results)

    def onRoiCoordinatesChanged(self, plotterIdx, bounds):
        self.analyzeWidget.updateDataBounds(plotterIdx, *bounds)
