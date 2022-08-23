from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGridLayout, QFormLayout, QHBoxLayout
from PyQt5.QtWidgets import QSplitter, QGroupBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem

import pyqtgraph as pg

from EasyG.gui.analyzewidget import MainAnalyzePlotWidget


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

        dataSelectLayout.addRow("Select data source:", self.dataSelect)
        dataSelectLayout.addRow("Display results on:", self.dataTarget)

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
        plotWidget = pg.PlotWidget()
        plotWidget.addLegend()
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

        self.dataItems.append(PlotDataItem(**kwargs))

        if plotterIdx is not None:
            self.addItemToPlot(plotterIdx=plotterIdx, itemIdx=itemIdx)

        return itemIdx


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

    def addPlot(self, plotterName=None):
        plotIdx = self.plotWidget.addPlot()

        if plotterName is None:
            plotterName = "Main plot" if not plotIdx else f"Plot {plotIdx}"

        self.dataManager.addNewAvailablePlotsColumn(columnName=plotterName)

        return plotIdx

    def newDataItem(self, plotterIdx=None, **kwargs):
        itemIdx = self.plotWidget.newDataItem(plotterIdx=plotterIdx, **kwargs)

        self.dataManager.registerNewDataItem(
            rowName=kwargs.get("name", f"plot {itemIdx}"))

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
