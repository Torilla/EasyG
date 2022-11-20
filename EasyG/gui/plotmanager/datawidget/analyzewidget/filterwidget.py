from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from EasyG.config import getAnalyzeWidgetConfig
from ...layoutwidget.buttons import CheckableLineEdit

_ANALYZECONFIG = getAnalyzeWidgetConfig()
_AVAILABLEFILTERS = _ANALYZECONFIG["FilterWidget"]
_FILTERCONFIG = _ANALYZECONFIG["FilterWidget.Options"]


class FilterOptionsWidget(QtWidgets.QGroupBox):
    OptionsChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.samplingRate = CheckableLineEdit()
        self.samplingRate.setValidator(QtGui.QDoubleValidator())
        layout.addRow("Sampling rate:", self.samplingRate)

        self.order = QtWidgets.QSpinBox()
        self.order.setMinimum(1)
        self.order.setValue(_FILTERCONFIG.getint("order"))

        layout.addRow("Order:", self.order)

        self.samplingRate.textChanged.connect(self.OptionsChanged)
        self.order.valueChanged.connect(self.OptionsChanged)

    def getFilterOptions(self):
        return {"sample_rate": float(self.samplingRate.text()),
                "order": self.order.value()}

    def setSamplingRate(self, rate):
        self.samplingRate.setText(f"{rate:.2f}")

    def anyOptionEmpty(self):
        return not self.samplingRate.text()


class SinglePassFilterWidget(FilterOptionsWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cutOff = QtWidgets.QLineEdit()
        self.cutOff.setValidator(QtGui.QDoubleValidator())

        self.layout().addRow("Cutoff:", self.cutOff)

        self.cutOff.textChanged.connect(self.OptionsChanged)

    def getFilterOptions(self):
        opts = super().getFilterOptions()
        opts["cutoff"] = float(self.cutOff.text())

        return opts

    def anyOptionEmpty(self):
        return super().anyOptionEmpty() or not self.cutOff.text()


class BandPassFilterWidget(FilterOptionsWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.cutOffLower = QtWidgets.QLineEdit()
        self.cutOffLower.setValidator(QtGui.QDoubleValidator())

        self.cutOffUpper = QtWidgets.QLineEdit()
        self.cutOffUpper.setValidator(QtGui.QDoubleValidator())

        layout = self.layout()
        layout.addRow("Lower cutoff:", self.cutOffLower)
        layout.addRow("Upper cutoff:", self.cutOffUpper)

        self.cutOffLower.textChanged.connect(self.OptionsChanged)
        self.cutOffUpper.textChanged.connect(self.OptionsChanged)

    def getFilterOptions(self):
        opts = super().getFilterOptions()
        opts["cutoff"] = [float(self.cutOffLower.text()),
                          float(self.cutOffUpper.text())]

        return opts

    def anyOptionEmpty(self):
        return (super().anyOptionEmpty() or not self.cutOffLower.text()
                or not self.cutOffUpper.text())


class DataFilterWidget(QtWidgets.QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Filter data")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.availableFilters = QtWidgets.QComboBox()
        layout.addWidget(self.availableFilters)

        self.stackedFilterLayout = QtWidgets.QStackedLayout()
        for fltrName, fltr in _AVAILABLEFILTERS.items():
            fltr = globals()[f"{fltr}FilterWidget"]
            fltr = fltr()
            fltr.OptionsChanged.connect(self._monitorApplyButton)
            self.availableFilters.addItem(fltrName)
            self.stackedFilterLayout.addWidget(fltr)
        self.stackedFilterLayout.currentChanged.connect(
            self._monitorApplyButton)

        self.availableFilters.currentIndexChanged.connect(
            self.stackedFilterLayout.setCurrentIndex)
        layout.addLayout(self.stackedFilterLayout)

        self.applyButton = QtWidgets.QPushButton()
        self.applyButton.setText("Apply")
        self.applyButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                       QtWidgets.QSizePolicy.Minimum)
        layout.addWidget(self.applyButton, alignment=Qt.AlignRight)

    def setSamplingRate(self, rate):
        for idx in range(self.stackedFilterLayout.count()):
            self.stackedFilterLayout.widget(idx).setSamplingRate(rate)

    def _monitorApplyButton(self):
        if self.stackedFilterLayout.currentWidget().anyOptionEmpty():
            self.applyButton.setEnabled(False)

        else:
            self.applyButton.setEnabled(True)

    def currentOptions(self):
        filterType = self.availableFilters.currentText()
        opts = self.stackedFilterLayout.currentWidget().getFilterOptions()
        opts["filtertype"] = filterType

        return opts
