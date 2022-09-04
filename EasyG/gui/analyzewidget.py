from math import ceil

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFormLayout, QVBoxLayout, QStackedLayout
from PyQt5.QtWidgets import QHBoxLayout, QGridLayout
from PyQt5.QtWidgets import QWidget, QLineEdit, QPushButton, QCheckBox
from PyQt5.QtWidgets import QGroupBox, QSpinBox, QComboBox
from PyQt5.QtWidgets import QTableWidgetItem, QTableWidget
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtGui import QDoubleValidator

_GROUPBOXSTYLESHEET = """
    QGroupBox#{} {{
        border: 2px solid gray;
        border-radius: 5px;
        margin-top: 2.5ex; /* leave space at the top for the title */
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        padding: 0 0 0 2ex;
    }}
"""

NEWPLOT = "New Plot"


class FilterOptionsWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Options")

        layout = QFormLayout()
        self.setLayout(layout)

        self.samplingRate = QLineEdit()
        self.samplingRate.setValidator(QDoubleValidator())
        layout.addRow("Sampling rate:", self.samplingRate)

        self.order = QSpinBox()
        self.order.setMinimum(1)
        self.order.setValue(2)

        layout.addRow("Order:", self.order)

    def getFilterOptions(self):
        return {"sample_rate": float(self.samplingRate.text()),
                "order": self.order.value()}


class SinglePassFilterWidget(FilterOptionsWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cutOff = QLineEdit()
        self.cutOff.setValidator(QDoubleValidator())

        self.layout().insertRow(0, "Cutoff:", self.cutOff)

    def getFilterOptions(self):
        opts = super().getFilterOptions()
        opts["cutoff"] = float(self.cutOff.text())

        return opts


class BandPassFilterWidget(FilterOptionsWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cutOffLower = QLineEdit()
        self.cutOffLower.setValidator(QDoubleValidator())

        self.cutOffUpper = QLineEdit()
        self.cutOffUpper.setValidator(QDoubleValidator())

        layout = self.layout()
        layout.insertRow(0, "Lower cutoff:", self.cutOffLower)
        layout.insertRow(1, "Upper cutoff:", self.cutOffUpper)

    def getFilterOptions(self):
        opts = super().getFilterOptions()
        opts["cutoff"] = [float(self.cutOffLower.text()),
                          float(self.cutOffUpper.text())]

        return opts


class MainFilterWidget(QGroupBox):
    availableFilters = {"Lowpass filter": SinglePassFilterWidget,
                        "Highpass filter": SinglePassFilterWidget,
                        "Bandpass filter": BandPassFilterWidget,
                        "Notch filter": SinglePassFilterWidget}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Filter Signal")
        self.setObjectName(type(self).__name__)
        self.setStyleSheet(_GROUPBOXSTYLESHEET.format(self.objectName()))

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.availableFilters = QComboBox()
        self.availableFilters.addItems(MainFilterWidget.availableFilters)
        layout.addWidget(self.availableFilters)

        self.stackedFilterLayout = QStackedLayout()
        for fltr in MainFilterWidget.availableFilters.values():
            self.stackedFilterLayout.addWidget(fltr())
        self.availableFilters.currentIndexChanged.connect(
            self.stackedFilterLayout.setCurrentIndex)
        layout.addLayout(self.stackedFilterLayout)

        self.applyButton = QPushButton()
        self.applyButton.setText("Apply")
        self.applyButton.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Minimum)
        layout.addWidget(self.applyButton, alignment=Qt.AlignRight)

    def getFilterOptions(self):
        filterType = self.availableFilters.currentText().split(" ")[0].lower()
        opts = self.stackedFilterLayout.currentWidget().getFilterOptions()
        opts["filtertype"] = filterType

        return opts


class HeartPyProcessWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Options")

        layout = QFormLayout()
        self.setLayout(layout)

        self.samplingRate = QLineEdit()
        layout.addRow("Sampling rate:", self.samplingRate)

        self.windowSize = QLineEdit()
        self.windowSize.setValidator(QDoubleValidator())
        self.windowSize.setText("0.75")
        layout.addRow("Window size:", self.windowSize)

        self.frequencyMethod = QComboBox()
        self.frequencyMethod.addItems(["Welch", "Periodogram", "FFT"])
        layout.addRow("Frequency method:", self.frequencyMethod)

        self.welchWindowSize = QLineEdit()
        self.welchWindowSize.setValidator(QDoubleValidator())
        self.welchWindowSize.setText("240")
        layout.addRow("Welch window size:", self.welchWindowSize)

        self.reportTime = QCheckBox()
        self.frequencyDomain = QCheckBox()
        self.squarePowerSpecturm = QCheckBox()

    def getProcessOptions(self):
        return {"windowsize": float(self.windowSize.text()),
                "sample_rate": float(self.samplingRate.text()),
                "freq_method": self.frequencyMethod.currentText(),
                "welch_wsize": float(self.welchWindowSize.text())}


class ProcessResultTableWidget(QTableWidget):
    MAXLENCOLUMN = 7

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.verticalHeader().hide()
        self.setShowGrid(False)
        self.setSize()

    def setResults(self, results):
        nRows = len(results)
        if nRows > self.MAXLENCOLUMN:
            nRows = self.MAXLENCOLUMN

        self.setRowCount(nRows)
        nCols = ceil(len(results) / self.MAXLENCOLUMN)

        # include property column for each result column
        self.setColumnCount(nCols * 2)

        self.setHorizontalHeaderLabels(["Property", "Value"] * nCols)

        nColumn = -1

        for rowIdx, (name, value) in enumerate(results.items()):
            if not rowIdx % self.MAXLENCOLUMN:
                nColumn += 2

            if rowIdx >= self.MAXLENCOLUMN:
                rowIdx -= (nColumn // 2) * self.MAXLENCOLUMN

            name = QTableWidgetItem(name)
            name.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.setItem(rowIdx, nColumn - 1, name)

            value = QTableWidgetItem(value)
            value.setTextAlignment(Qt.AlignCenter)
            self.setItem(rowIdx, nColumn, value)

        self.setSize()

    def setSize(self):
        self.setFixedSize(self.horizontalHeader().length()
                          + self.verticalHeader().width(),
                          self.verticalHeader().length()
                          + self.horizontalHeader().height())


class ProcessOptionsWidget(QWidget):
    availableProcessors = {"HeartPy.process": HeartPyProcessWidget,
                           "HeartPy.find_peaks": HeartPyProcessWidget}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        layout = QVBoxLayout()
        self.setLayout(layout)

        self.availableProcessors = QComboBox()
        self.availableProcessors.addItems(
            ProcessOptionsWidget.availableProcessors)
        layout.addWidget(self.availableProcessors)

        self.stackedProcessorLayout = QStackedLayout()
        for proc in ProcessOptionsWidget.availableProcessors.values():
            self.stackedProcessorLayout.addWidget(proc())
        layout.addLayout(self.stackedProcessorLayout)
        self.availableProcessors.currentIndexChanged.connect(
            self.stackedProcessorLayout.setCurrentIndex)

        self.applyButton = QPushButton("Execute")
        self.applyButton.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Minimum)
        layout.addWidget(self.applyButton, alignment=Qt.AlignRight)

    def getProcessOptions(self):
        data = self.stackedProcessorLayout.currentWidget().getProcessOptions()
        data["processor"] = self.availableProcessors.currentText()

        return data


class MainProcessWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName(type(self).__name__)
        self.setStyleSheet(_GROUPBOXSTYLESHEET.format(self.objectName()))

        self.setTitle("Extract data from signal")

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.processOptions = ProcessOptionsWidget()
        layout.addWidget(self.processOptions)

    def getProcessOptions(self):
        return self.processOptions.getProcessOptions()

    def processButton(self):
        return self.processOptions.applyButton


class DataMangerWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName(type(self).__name__)
        self.setStyleSheet(_GROUPBOXSTYLESHEET.format(self.objectName()))

        self.setTitle("Select source and target")

        layout = QFormLayout()
        self.setLayout(layout)

        # First row what data to use
        self.dataSource = QComboBox()
        self.dataSource.currentIndexChanged.connect(self._setDataBounds)
        layout.addRow("Operate on data:", self.dataSource)

        # Second row which part of the data to use
        dataBoundsLayout = QHBoxLayout()
        self.lowerBoundEdit = QLineEdit()
        self.lowerBoundEdit.textChanged.connect(self._rememberUserDataBounds)
        dataBoundsLayout.addWidget(self.lowerBoundEdit)
        self.upperBoundEdit = QLineEdit()
        self.upperBoundEdit.textChanged.connect(self._rememberUserDataBounds)
        dataBoundsLayout.addWidget(self.upperBoundEdit)
        self.resetBoundsButton = QPushButton("reset")
        self.resetBoundsButton.clicked.connect(self.resetDataBounds)
        dataBoundsLayout.addWidget(self.resetBoundsButton)
        layout.addRow("Data range:", dataBoundsLayout)

        # Third row where to put the results data
        self.dataTarget = QComboBox()
        self.dataTarget.addItem(NEWPLOT)
        self.dataTarget.setEditable(True)
        self.dataTarget.currentIndexChanged.connect(self._allowNewPlotEditable)
        layout.addRow("Display results on:", self.dataTarget)

        # keep a list of databounds so we can switch
        self._dataBounds = []
        self._defaultBounds = []

    def _allowNewPlotEditable(self, srcIdx):
        if srcIdx == 0:
            self.dataTarget.setEditable(True)
        else:
            self.dataTarget.setEditable(False)

    def _setDataBounds(self, srcIdx):
        lo, up = self._dataBounds[srcIdx]
        self.lowerBoundEdit.setText(lo)
        self.upperBoundEdit.setText(up)

    def _rememberUserDataBounds(self):
        lo = self.lowerBoundEdit.text()
        up = self.upperBoundEdit.text()

        self._dataBounds[self.dataSource.currentIndex()] = (lo, up)

    def resetDataBounds(self, pressed, srcIdx=None):
        if srcIdx is None:
            srcIdx = self.dataSource.currentIndex()

        self._dataBounds[srcIdx] = self._defaultBounds[srcIdx]

        if srcIdx == self.dataSource.currentIndex():
            lo, up = self._dataBounds[srcIdx]
            self.lowerBoundEdit.setText(lo)
            self.upperBoundEdit.setText(up)

        else:
            self.dataSource.setCurrentIndex(srcIdx)

    def updateDataBounds(self, srcIdx, lower, upper):
        if lower > upper:
            upper, lower = lower, upper

        lower, upper = str(int(lower)), str(int(upper))
        self._dataBounds[srcIdx] = (lower, upper)

        if self.dataSource.currentIndex() == srcIdx:
            self.lowerBoundEdit.setText(lower)
            self.upperBoundEdit.setText(upper)

        else:
            self.dataSource.setCurrentIndex(srcIdx)

    def addDataSource(self, name, upperBound, lowerBound):
        upperBound, lowerBound = str(int(upperBound)), str(int(lowerBound))
        self._dataBounds.append((lowerBound, upperBound))
        self._defaultBounds.append((lowerBound, upperBound))
        self.dataSource.addItem(name)

    def getDataSelect(self):
        itemIdx = self.dataSource.currentIndex()

        # first index means new plot, so set it to None
        # otherwise shift the index by one to ignore new plot options
        plotIdx = self.dataTarget.currentIndex()
        plotIdx = plotIdx - 1 if plotIdx > 0 else None

        lowerBound = int(self.lowerBoundEdit.text())
        upperBound = int(self.upperBoundEdit.text())
        plotBounds = slice(lowerBound, upperBound)

        plotterName = None
        if plotIdx is None:
            # first row is the name of the new plotter
            plotterName = self.dataTarget.currentText()

        return itemIdx, plotIdx, plotBounds, plotterName

    def addDataTarget(self, name):
        self.dataTarget.addItem(name)


class MainAnalyzePlotWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Manipulate and analyze data")

        layout = QHBoxLayout()
        self.setLayout(layout)

        self.dataManager = DataMangerWidget()
        layout.addWidget(self.dataManager)

        self.processWidget = MainProcessWidget()
        layout.addWidget(self.processWidget)

        self.filterWidget = MainFilterWidget()
        layout.addWidget(self.filterWidget)

    def getTargetName(self):
        return self.dataManager.getTargetName()

    def addDataTarget(self, **kwargs):
        self.dataManager.addDataTarget(**kwargs)

    def addDataSource(self, **kwargs):
        self.dataManager.addDataSource(**kwargs)

    def getDataSelect(self, **kwargs):
        return self.dataManager.getDataSelect(**kwargs)

    def getFilterOptions(self):
        return self.filterWidget.getFilterOptions()

    def getProcessOptions(self):
        return self.processWidget.getProcessOptions()

    def processButton(self):
        return self.processWidget.processButton()

    def filterButton(self):
        return self.filterWidget.applyButton

    def setDataRange(self, *args, **kwargs):
        self.dataManager.setDataRange(*args, **kwargs)

    def updateDataBounds(self, *args, **kwargs):
        self.dataManager.updateDataBounds(*args, **kwargs)
