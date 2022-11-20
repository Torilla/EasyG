from PyQt5 import QtWidgets, QtCore

import numpy as np

from .layoutwidget.splitter import ToplevelSplitter
from .datawidget.datawidget import DataWidget
from .plotwidget.plotwidget import ECGPlotWidget, ECGPlotDataItem
from EasyG.ecg import ecgprocessors, ecgfilters


class PlotManagerWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.splitterWidget = ToplevelSplitter()
        layout.addWidget(self.splitterWidget)
        layout.setStretch(0, 1)

        self.dataWidget = DataWidget()
        layout.addWidget(self.dataWidget)
        layout.setStretch(1, 0)

        # dict of global ploItems {plotItemName: plotItem}
        self._globalPlotItems = {}

        # connect the spliterPlotWidget
        self.splitterWidget.ColumnInsertRequest.connect(
            self.onColumnInsertRequest)
        self.splitterWidget.WidgetInsertRequest.connect(
            self.onWidgetInsertRequest)
        self.splitterWidget.WidgetRemoveRequest.connect(
            self.onWidgetRemoveRequest)

        # connect dataWidget
        self.dataWidget.ProcessButtonPressed.connect(
            self.onDataWidgetProcessButtonPressed)
        self.dataWidget.FilterButtonPressed.connect(
            self.onDataWidgetFilterButtonPressed)
        self.dataWidget.DataManipulationButtonPressed.connect(
            self.onDataManipulationButtonPressed)
        self.dataWidget.PlotTableItemClicked.connect(
            self.onPlotTableItemClicked)
        self.dataWidget.CurrentDataSourceChanged.connect(
            self.currentDataSourceChanged)

    def registerGlobalPlotItem(self, item):
        if not item.isGlobalAncestor():
            raise ValueError("Can only store global ancesotrs!")

        name = item.name()

        if name in self._globalPlotItems:
            if item is not self._globalPlotItems[item]:
                raise KeyError(f"Item with name {name} already registerd!")

        else:
            self._globalPlotItems[name] = item

    def getGlobalPlotItem(self, itemName):
        return self._globalPlotItems[itemName]

    def _getUniquePlotItemTitle(self, defaultTitle="data"):
        i = 0
        title = defaultTitle
        while self.dataWidget.containsDataSource(title):
            i += 1
            title = f"{defaultTitle} ({i})"

        return title

    def _getUniquePlotTitle(self, defaultTitle=None):
        if defaultTitle is None:
            defaultTitle = "Plot"

        i = 0
        title = defaultTitle
        while self.dataWidget.containsDataTarget(title):
            i += 1
            title = f"{defaultTitle} {i}"

        return title

    def _getUserPlotTitle(self, defaultTitle):
        title, isValid = QtWidgets.QInputDialog.getText(
            self,
            "Edit plot title",
            "New title:",
            text=defaultTitle)

        if isValid and title != defaultTitle:
            while self.dataWidget.containsDataTarget(title):
                title, isValid = QtWidgets.QInputDialog.getText(
                    self,
                    "Plot title already exists!",
                    "New title:",
                    text=defaultTitle)

                if not isValid or title == defaultTitle:
                    title = None
                    break

        else:
            # cancled
            title = None

        return title

    def _initNewPlotWidget(self, plotWidget, defaultTitle=None):
        title = self._getUniquePlotTitle(defaultTitle)

        if defaultTitle is None:
            title = self._getUserPlotTitle(title) or title

        plotWidget.setTitle(title)

        plotWidget.TitleChangeRequest.connect(
            self.onPlotWidgetTitleChangeRequest)

        plotWidget.NewROICoordinates.connect(
            self.onNewROICoodinates)

    def insertColumn(self, columnIdx=None):
        self.splitterWidget.insertColumn(columnIdx)

    def insertPlotWidget(self, columnIdx=None, rowIdx=None, title=None):
        plotWidget = ECGPlotWidget()
        self._initNewPlotWidget(plotWidget, defaultTitle=title)

        self.dataWidget.addDataTarget(plotWidget.getTitle())

        self.splitterWidget.insertWidget(plotWidget, columnIdx, rowIdx)

        return plotWidget

    def plotWidgetFromTitle(self, title):
        for plotWidget in self.splitterWidget.iterWidgets():
            if plotWidget.getTitle() == title:
                break

        else:
            raise ValueError(f"No such plotwidget: {title}")

        return plotWidget

    def indexOfPlotWidget(self, plotWidget):
        return self.splitterWidget.indexOf(plotWidget)

    def plot(self, columnIdx, rowIdx, **kwargs):
        name = self._getUniquePlotItemTitle(kwargs.get("name", "data"))
        kwargs["name"] = name

        plotWidget = self.splitterWidget.widget(columnIdx, rowIdx)
        plotItem = ECGPlotDataItem(**kwargs)

        colName, rowName = plotWidget.getTitle(), name

        # do not use self.addPlotItem because it relys on the dataWidget
        # already having the name present. Store the original for reference
        # and add a copy to the widget
        plotWidget.addItem(plotItem.copy())
        self.registerGlobalPlotItem(plotItem)

        self.dataWidget.addDataSource(name)
        self.dataWidget.setPlotTableCheckStateByName(
            colName, rowName,
            state=QtCore.Qt.CheckState.Checked)

        return plotItem

    def addPlotItem(self, columnIdx, rowIdx, item):
        if item.isGlobalAncestor():
            self.registerGlobalPlotItem(item)
            item = item.copy()

        widget = self.splitterWidget.widget(columnIdx, rowIdx)
        widget.addItem(item)

        colName = widget.getTitle()
        rowName = item.name()

        self.dataWidget.setPlotTableCheckStateByName(
            colName, rowName,
            state=QtCore.Qt.CheckState.Checked)

    @QtCore.pyqtSlot(int)
    def onColumnInsertRequest(self, columnIdx):
        self.splitterWidget.insertColumn(columnIdx)
        self.insertPlotWidget(columnIdx)

    @QtCore.pyqtSlot(int, int)
    def onWidgetInsertRequest(self, columnIdx, rowIdx):
        self.insertPlotWidget(columnIdx, rowIdx)

    @QtCore.pyqtSlot(int, int)
    def onWidgetRemoveRequest(self, columnIdx, rowIdx):
        widget = self.splitterWidget.widget(columnIdx, rowIdx)
        self.dataWidget.removeDataTarget(widget.getTitle())

        self.splitterWidget.removeWidget(columnIdx, rowIdx)

        for dataItem in widget.listDataItems():
            if not dataItem.hasRelatives():
                self.dataWidget.removeDataSource(dataItem.name())

            widget.removeItem(dataItem)

            dataItem.deleteLater()

    @QtCore.pyqtSlot(object)
    def onPlotWidgetTitleChangeRequest(self, plotWidget):
        newTitle = self._getUserPlotTitle(plotWidget.getTitle())

        if newTitle is not None:
            self.dataWidget.updateDataTarget(plotWidget.getTitle(),
                                             newTitle)
            plotWidget.setTitle(newTitle)

    @QtCore.pyqtSlot(float, float)
    def onNewROICoodinates(self, x0, x1):
        if x0 > x1:
            x0, x1 = x1, x0

        self.dataWidget.setDataBounds(x0, x1)

    @QtCore.pyqtSlot(str, str, int)
    def onPlotTableItemClicked(self, plotName, itemName, checkState):
        plotItem = self.getGlobalPlotItem(itemName)

        for plotWidget in self.splitterWidget.iterWidgets():
            if plotWidget.getTitle() == plotName:
                break

        else:
            raise RuntimeError("Could not determine correct plot widget!")

        if checkState == QtCore.Qt.CheckState.Checked:
            if not plotWidget.containsItemWithName(itemName):
                plotWidget.addItem(plotItem.copy())

        else:
            if plotWidget.containsItemWithName(itemName):
                plotWidget.removeItem(plotItem)

    @QtCore.pyqtSlot(str)
    def currentDataSourceChanged(self, itemName):
        rate = self.getGlobalPlotItem(itemName).estimateSampleRate()
        self.dataWidget.setSamplingRate(rate)

    def _getDataFromOptions(self, dataOptions):
        x, y = self.getGlobalPlotItem(dataOptions["data source"]).getData()

        lower, upper = dataOptions["data bounds"]

        if (lower and upper) is not None:
            bounds = np.where(np.logical_and(lower <= x, x <= upper))

        elif lower is not None:
            bounds = np.where(lower <= x)

        elif upper is not None:
            bounds = np.where(x <= upper)

        else:
            bounds = slice(0, -1)

        return x[bounds], y[bounds]

    @QtCore.pyqtSlot()
    def onDataWidgetProcessButtonPressed(self):
        dataOptions = self.dataWidget.getCurrentDataOptions()
        processOptions = self.dataWidget.getCurrentProcessOptions()

        x, y = self._getDataFromOptions(dataOptions)
        processor = getattr(ecgprocessors, processOptions.pop("processor"))
        data, measures = processor(y, **processOptions)

        rowIdx, colIdx = self.indexOfPlotWidget(
            self.plotWidgetFromTitle(dataOptions["data target"]))

        self.plot(rowIdx=rowIdx, columnIdx=colIdx,
                  x=x[data["peaklist"]], y=y[data["peaklist"]],
                  pen=None, symbolBrush="g", symbol="x", symbolSize=11,
                  name="accepted peaks")

        self.plot(rowIdx=rowIdx, columnIdx=colIdx,
                  x=x[data["removed_beats"]], y=y[data["removed_beats"]],
                  pen=None, symbolBrush="r", symbol="o", symbolSize=11,
                  name="rejected peaks")

    @QtCore.pyqtSlot()
    def onDataWidgetFilterButtonPressed(self):
        dataOptions = self.dataWidget.getCurrentDataOptions()
        filterOptions = self.dataWidget.getCurrentFilterOptions()

        x, y = self._getDataFromOptions(dataOptions)

        y = ecgfilters.HeartPyFilter(y, **filterOptions)

        rowIdx, colIdx = self.indexOfPlotWidget(
            self.plotWidgetFromTitle(dataOptions["data target"]))

        name = dataOptions["target name"] or filterOptions["filtertype"]

        self.plot(rowIdx=rowIdx, columnIdx=colIdx,
                  x=x, y=y,
                  pen=dataOptions["target color"],
                  name=name)

    @QtCore.pyqtSlot()
    def onDataManipulationButtonPressed(self):
        dataOptions = self.dataWidget.getCurrentDataOptions()
        manipulationOpts = self.dataWidget.getCurrentDataManipulationOptions()

        self.DataManipulationButtonPressed.emit(dataOptions, manipulationOpts)
