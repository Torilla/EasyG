from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QFormLayout, QHBoxLayout
from PyQt5.QtWidgets import QSplitter, QGroupBox, QLineEdit
from PyQt5.QtWidgets import QComboBox, QFrame
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

import pyqtgraph as pg

from EasyG.config import setPyqtgraphConfig
from EasyG.gui.analyzewidget import MainAnalyzePlotWidget
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class DataMangerWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QHBoxLayout()
        self.setLayout(layout)

        dataSelectLayout = QFormLayout()
        layout.addLayout(dataSelectLayout)

        self.dataSelect = QComboBox()
        self.dataSelect.setMinimumWidth(150)
        self.dataTarget = QComboBox()
        self.dataTarget.addItem("New plot")

        self.targetName = QLineEdit()

        dataSelectLayout.addRow("Select data source:", self.dataSelect)
        dataSelectLayout.addRow("Display results on:", self.dataTarget)
        dataSelectLayout.addRow("Name of new plot:", self.targetName)

        self.availablePlotsList = QTableWidget()
        self.availablePlotsList.setColumnCount(1)
        self.availablePlotsList.setShowGrid(False)
        self.availablePlotsList.verticalHeader().hide()
        layout.addWidget(self.availablePlotsList)
        self._horizontalHeaders = ["Available plots"]

    @staticmethod
    def _newCheckBox():
        checkBox = QTableWidgetItem()
        checkBox.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checkBox.setCheckState(Qt.Unchecked)

        return checkBox

    def registerNewDataItem(self, rowName: str):
        """
        Adds a new row to the availablePlotsList and names it rowName.
        Fills the rest of the row's cells with unchecked checkboxes.

        Also adds the name to the dataSelect lsit
        """
        item = QTableWidgetItem(rowName)
        item.setFlags(Qt.ItemIsEnabled)

        # increase the number of rows by one
        rowCount = self.availablePlotsList.rowCount()
        self.availablePlotsList.setRowCount(rowCount + 1)

        # add the name to the first cell of the new row
        self.availablePlotsList.setItem(rowCount, 0, item)

        # add checkboxes to the remaining cells in the row
        for columnIdx in range(1, self.availablePlotsList.columnCount() + 1):
            self.availablePlotsList.setItem(rowCount, columnIdx,
                                            self._newCheckBox())

        # add name to dataSelect
        self.dataSelect.addItem(rowName)

        self.availablePlotsList.resizeColumnsToContents()

    def addNewAvailablePlotsColumn(self, columnName: str):
        """
        adds a new column to the availablePlotsList and puts checkboxes
        into the cells. Names the new column columnName.

        #Also adds the name to the dataTarget list.
        """
        columnCount = self.availablePlotsList.columnCount()
        self.availablePlotsList.setColumnCount(columnCount + 1)

        for rowIdx in range(self.availablePlotsList.rowCount() + 1):
            self.availablePlotsList.setItem(rowIdx, columnCount,
                                            self._newCheckBox())

        self._horizontalHeaders.append(columnName)
        self.availablePlotsList.setHorizontalHeaderLabels(
            self._horizontalHeaders)

        # add name to dataTarget list
        self.dataTarget.addItem(columnName)

        self.availablePlotsList.resizeRowsToContents()

    def setPlotChecked(self, plotIdx, itemIdx, b=True):
        state = Qt.Checked if b else Qt.Unchecked

        # plotIdx needs to be shifted by one because the first column is
        # for names and does not cound in the index
        self.availablePlotsList.item(itemIdx, plotIdx + 1).setCheckState(state)

    def getDataSelect(self):
        itemIdx = self.dataSelect.currentIndex()

        # first index means new plot, so set it to None
        # otherwise shift the index by one to ignore new plot options
        plotIdx = self.dataTarget.currentIndex()
        plotIdx = plotIdx - 1 if plotIdx > 0 else None

        return itemIdx, plotIdx, self.targetName.text() or None


class MultiPlotWidget(QSplitter):
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
        plotterIdx = len(self.plotWidgets)
        plotWidget = PlotWidget()
        plotWidget.addLegend()
        self.plotWidgets.append(plotWidget)

        framedPlotWidtet = QFrame()
        framedPlotWidtet.setFrameStyle(QFrame.Box | QFrame.Raised)
        framedPlotWidtet.setLineWidth(1)
        framedPlotWidtet.setMidLineWidth(1)
        framedPlotWidtet.setLayout(QGridLayout())
        framedPlotWidtet.layout().addWidget(plotWidget, 0, 0)

        self.addWidget(framedPlotWidtet)

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

    def getDataFromItemIndex(self, itemIdx):
        return self.dataItems[itemIdx].getData()


class MainPlotWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QGridLayout()
        self.setLayout(layout)

        self.plotWidget = MultiPlotWidget()
        layout.addWidget(self.plotWidget, 0, 0)

        self.dataManager = DataMangerWidget()
        self.dataManager.availablePlotsList.itemClicked.connect(
            self._monitorDataManager)
        layout.addWidget(self.dataManager, 1, 0)

        self.analyzeWidget = MainAnalyzePlotWidget()
        layout.addWidget(self.analyzeWidget, 2, 0)

        layout.setRowStretch(0, 2)
        layout.setRowStretch(1, 1)

        self.analyzeWidget.filterButton().clicked.connect(self.onApplyFilter)
        self.analyzeWidget.processButton().clicked.connect(self.onProcess)

    def addPlot(self, plotterName=None):
        plotIdx = self.plotWidget.addPlot()

        if plotterName is None:
            plotterName = "Main plot" if not plotIdx else f"Plot {plotIdx}"

        self.dataManager.addNewAvailablePlotsColumn(columnName=plotterName)

        return plotIdx

    def newDataItem(self, plotterIdx=None, name=None, **kwargs):
        if name is None:
            name = f"plot {self.plotWidget.itemCount()}"

        itemIdx = self.plotWidget.newDataItem(plotterIdx=plotterIdx, name=name,
                                              **kwargs)

        self.dataManager.registerNewDataItem(rowName=name)

        if plotterIdx is not None:
            self.dataManager.setPlotChecked(plotIdx=plotterIdx,
                                            itemIdx=itemIdx)

    def _monitorDataManager(self, dataItem):
        itemIdx = dataItem.row()

        # shift one because of the name column that doesnt count
        plotIdx = dataItem.column() - 1

        containsPlot = self.plotWidget.plotContainsItem(plotterIdx=plotIdx,
                                                        itemIdx=itemIdx)

        isChecked = dataItem.checkState() == Qt.Checked

        if containsPlot and not isChecked:
            self.plotWidget.removeItemFromPlot(itemIdx=itemIdx,
                                               plotterIdx=plotIdx)

        if not containsPlot and isChecked:
            self.plotWidget.addItemToPlot(itemIdx=itemIdx, plotterIdx=plotIdx)

    def onApplyFilter(self):
        filterOpts = self.analyzeWidget.getFilterOptions()
        itemIdx, plotIdx, name = self.dataManager.getDataSelect()

        name = name or filterOpts["filtertype"]

        if plotIdx is None:
            plotIdx = self.addPlot()

        x, y = self.plotWidget.getDataFromItemIndex(itemIdx)
        y = ecganalysis.filterSignal(y, **filterOpts)

        self.newDataItem(x=x, y=y, plotterIdx=plotIdx, name=name)

    def onProcess(self):
        processOpts = self.analyzeWidget.getProcessOptions()
        _processor = processOpts.pop("processor")
        processor = ecganalysis.getProcessor(_processor)

        itemIdx, plotIdx, name = self.dataManager.getDataSelect()

        name = name or _processor

        if plotIdx is None:
            plotIdx = self.addPlot()

        x, y = self.plotWidget.getDataFromItemIndex(itemIdx)
        data, measures = processor(y, **processOpts)

        x_accepted, x_rejected = [], []
        y_accepted, y_rejected = [], []

        for idx, xIdx in enumerate(data["peaklist"]):
            if data["binary_peaklist"][idx]:
                x_accepted.append(x[xIdx])
                y_accepted.append(y[xIdx])

            else:
                x_rejected.append(x[xIdx])
                y_rejected.append(y[xIdx])

        self.newDataItem(x=x_accepted, y=y_accepted, plotterIdx=plotIdx,
                         name="accepted peaks", pen=None, symbolBrush="g",
                         symbol="o")

        self.newDataItem(x=x_rejected, y=y_rejected, plotterIdx=plotIdx,
                         name="rejected peaks", pen=None, symbolBrush="r",
                         symbol="o")
