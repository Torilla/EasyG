from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFormLayout, QVBoxLayout, QStackedLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QLineEdit, QPushButton, QCheckBox
from PyQt5.QtWidgets import QGroupBox, QSpinBox, QComboBox
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


class FilterOptionsWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Options")

        layout = QFormLayout()
        self.setLayout(layout)

        self.order = QSpinBox()
        self.order.setMinimum(1)
        self.order.setValue(2)

        layout.addRow("Order:", self.order)

    def getFilterOptions(self):
        return {"order": self.order.value()}


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
        return self.stackedFilterLayout.currentWidget().getFilterOptions()


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


class MainProcessWidget(QGroupBox):
    availableProcessors = {"Process signal": HeartPyProcessWidget,
                           "Find peaks": HeartPyProcessWidget}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setObjectName(type(self).__name__)
        self.setStyleSheet(_GROUPBOXSTYLESHEET.format(self.objectName()))

        self.setTitle("Extract data from signal")

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.availableProcessors = QComboBox()
        self.availableProcessors.addItems(
            MainProcessWidget.availableProcessors)
        layout.addWidget(self.availableProcessors)

        self.stackedProcessorLayout = QStackedLayout()
        for proc in MainProcessWidget.availableProcessors.values():
            self.stackedProcessorLayout.addWidget(proc())
        layout.addLayout(self.stackedProcessorLayout)
        self.availableProcessors.currentIndexChanged.connect(
            self.stackedProcessorLayout.setCurrentIndex)

        self.applyButton = QPushButton("Execute")
        self.applyButton.setSizePolicy(QSizePolicy.Preferred,
                                       QSizePolicy.Minimum)
        layout.addWidget(self.applyButton, alignment=Qt.AlignRight)


class MainAnalyzePlotWidget(QGroupBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Manipulate and analye signal")

        layout = QGridLayout()
        self.setLayout(layout)

        self.processWidget = MainProcessWidget()
        layout.addWidget(self.processWidget, 1, 0)

        self.filterWidget = MainFilterWidget()
        layout.addWidget(self.filterWidget, 1, 1)
