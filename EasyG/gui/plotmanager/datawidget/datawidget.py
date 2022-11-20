from PyQt5 import QtWidgets, QtGui, QtCore

from ..layoutwidget.buttons import ColorFieldButton
from .plottablewidget import PlotTableWidget
from .analyzewidget.datamanipulationwidget import DataManipulationWidget
from .analyzewidget.filterwidget import DataFilterWidget
from .analyzewidget.processorwidget import ProcessOptionsWidget


class DataOptionWidget(QtWidgets.QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTitle("Select Data")

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.availableDataSources = QtWidgets.QComboBox()
        self.availableDataSources.setMinimumWidth(150)
        layout.addRow("Operate on:", self.availableDataSources)

        dataRangeLayout = QtWidgets.QHBoxLayout()
        self.lowerDataBound = QtWidgets.QLineEdit()
        self.lowerDataBound.setValidator(QtGui.QDoubleValidator())
        self.upperDataBound = QtWidgets.QLineEdit()
        self.upperDataBound.setValidator(QtGui.QDoubleValidator())
        dataRangeLayout.addWidget(self.lowerDataBound)
        dataRangeLayout.addWidget(self.upperDataBound)
        layout.addRow("Select data range:", dataRangeLayout)

        self.availableDataTargets = QtWidgets.QComboBox()
        layout.addRow("Display results on:", self.availableDataTargets)

        self.dataTargetName = QtWidgets.QLineEdit()
        layout.addRow("New plot name:", self.dataTargetName)

        self.dataTargetColor = ColorFieldButton()
        layout.addRow("Select color:", self.dataTargetColor)

    def setDataBounds(self, lower, upper):
        self.lowerDataBound.setText(f"{lower:.2f}")
        self.upperDataBound.setText(f"{upper:.2f}")

    def addDataTarget(self, target):
        if self.availableDataTargets.findText(target) != -1:
            raise ValueError(f"Can't add dublicate target: {target}")

        self.availableDataTargets.addItem(target)

    def removeDataTarget(self, target):
        idx = self.availableDataTargets.findText(target)
        if idx == -1:
            raise ValueError("No such target!")

        self.availableDataTargets.removeItem(idx)

    def containsDataTarget(self, target):
        return self.availableDataTargets.findText(target) != -1

    def updateDataTarget(self, previousTarget, newTarget):
        if self.availableDataTargets.findText(newTarget) != -1:
            raise ValueError(f"Can't add dublicate target: {newTarget}")

        idx = self.availableDataTargets.findText(previousTarget)
        if idx == -1:
            raise ValueError("No such target!")

        self.availableDataTargets.setItemText(idx, newTarget)

    def addDataSource(self, source):
        if self.containsDataSource(source):
            raise ValueError(f"Can't add dublicate source: {source}")

        self.availableDataSources.addItem(source)

    def containsDataSource(self, source):
        return self.availableDataSources.findText(source) != -1

    def updateDataSource(self, previousSouce, newSource):
        if self.containsDataSource(newSource):
            raise ValueError("Can't set dublicate souce!")

        idx = self.availableDataSources.findText(previousSouce)
        if idx == -1:
            raise ValueError(f"No such source: {previousSouce}")

        self.availableDataSources.setItemText(idx, newSource)

    def removeDataSource(self, source):
        idx = self.availableDataSources.findText(source)
        if idx == -1:
            raise ValueError(f"No such source: {source}")

        self.availableDataSources.removeItem(idx)

    def currentDataBounds(self):
        lower = self.lowerDataBound.text()
        upper = self.upperDataBound.text()

        lower = float(lower) if lower else None
        upper = float(upper) if upper else None

        if (lower and upper) is not None and lower > upper:
            lower, upper = upper, lower

        return lower, upper

    def currentOptions(self):
        return {
            "data source": self.availableDataSources.currentText(),
            "data target": self.availableDataTargets.currentText(),
            "data bounds": self.currentDataBounds(),
            "target name": self.dataTargetName.text() or None,
            "target color": self.dataTargetColor.currentColor()
        }


class DataWidget(QtWidgets.QWidget):
    # signals wrapped from class attributes
    ProcessButtonPressed = QtCore.pyqtSignal()
    FilterButtonPressed = QtCore.pyqtSignal()
    DataManipulationButtonPressed = QtCore.pyqtSignal()
    PlotTableItemClicked = QtCore.pyqtSignal(str, str, int)
    CurrentDataSourceChanged = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.plotTableWidget = PlotTableWidget()
        self.plotTableWidget.PlotItemClicked.connect(
            self.PlotTableItemClicked)
        layout.addWidget(self.plotTableWidget)

        self.dataOptionWidget = DataOptionWidget()
        self.dataOptionWidget.availableDataSources.currentTextChanged.connect(
            self.CurrentDataSourceChanged)
        layout.addWidget(self.dataOptionWidget)

        self.dataManipulationWidget = DataManipulationWidget()
        self.dataManipulationWidget.applyButton.pressed.connect(
            self.DataManipulationButtonPressed)
        layout.addWidget(self.dataManipulationWidget)

        self.filterWidget = DataFilterWidget()
        self.filterWidget.applyButton.pressed.connect(
            self.FilterButtonPressed)
        layout.addWidget(self.filterWidget)

        self.processWidget = ProcessOptionsWidget()
        self.processWidget.applyButton.pressed.connect(
            self.ProcessButtonPressed)
        layout.addWidget(self.processWidget)

    def availableDataTargets(self):
        return self.dataOptionWidget.availableDataTargets

    def availableDataSources(self):
        return self.dataOptionWidget.availableDataSources

    def containsDataTarget(self, target):
        return self.dataOptionWidget.containsDataTarget(target)

    def containsDataSource(self, source):
        return self.dataOptionWidget.containsDataSource(source)

    def addDataTarget(self, target):
        self.dataOptionWidget.addDataTarget(target)
        self.plotTableWidget.addColumn(target)

    def addDataSource(self, source):
        self.dataOptionWidget.addDataSource(source)
        self.plotTableWidget.addRow(source)

    def removeDataTarget(self, target):
        self.dataOptionWidget.removeDataTarget(target)
        self.plotTableWidget.removeColumn(target)

    def removeDataSource(self, source):
        self.dataOptionWidget.removeDataSource(source)
        self.plotTableWidget.removeRow(source)

    def updateDataTarget(self, previousTarget, newTarget):
        self.dataOptionWidget.updateDataTarget(previousTarget, newTarget)
        self.plotTableWidget.updateColumnName(previousTarget, newTarget)

    def updateDataSource(self, previousSouce, newSource):
        self.dataOptionWidget.updateDataSource(previousSouce, newSource)
        self.plotTableWidget.updateRowName(previousSouce, newSource)

    def setDataBounds(self, lower, upper):
        self.dataOptionWidget.setDataBounds(lower, upper)

    def setSamplingRate(self, rate):
        self.filterWidget.setSamplingRate(rate)
        self.processWidget.setSamplingRate(rate)

    def getCurrentDataOptions(self):
        return self.dataOptionWidget.currentOptions()

    def getCurrentProcessOptions(self):
        return self.processWidget.currentOptions()

    def getCurrentFilterOptions(self):
        return self.filterWidget.currentOptions()

    def getCurrentDataManipulationOptions(self):
        return self.dataManipulationWidget.currentOptions()

    def setPlotTableCheckState(self, columnIdx, rowIdx, state):
        self.plotTableWidget.setCheckState(columnIdx, rowIdx, state)

    def setPlotTableCheckStateByName(self, columnName, rowName, state):
        self.plotTableWidget.setCheckStateByName(columnName, rowName, state)
