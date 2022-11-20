from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

from EasyG.config import getAnalyzeWidgetConfig
from ...layoutwidget.buttons import CheckableLineEdit

_ANALYZECONFIG = getAnalyzeWidgetConfig()
_HEARTPYPROCESSCONFIG = _ANALYZECONFIG["Processor.HeartPyProcess"]


class HeartPyProcessWidget(QtWidgets.QGroupBox):
    OptionsChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.samplingRate = CheckableLineEdit()
        self.samplingRate.textChanged.connect(self.OptionsChanged)
        self.samplingRate.setValidator(QtGui.QDoubleValidator())
        layout.addRow("Sampling rate:", self.samplingRate)

        self.windowSize = QtWidgets.QLineEdit()
        self.windowSize.textChanged.connect(self.OptionsChanged)
        self.windowSize.setValidator(QtGui.QDoubleValidator())
        self.windowSize.setText(_HEARTPYPROCESSCONFIG["window size"])
        layout.addRow("Window size:", self.windowSize)

        self.frequencyMethod = QtWidgets.QComboBox()
        self.frequencyMethod.addItems(
            _HEARTPYPROCESSCONFIG.getlist("frequency methods"))
        layout.addRow("Frequency method:", self.frequencyMethod)

        self.welchWindowSize = QtWidgets.QLineEdit()
        self.welchWindowSize.textChanged.connect(self.OptionsChanged)
        self.welchWindowSize.setValidator(QtGui.QDoubleValidator())
        self.welchWindowSize.setText(_HEARTPYPROCESSCONFIG.get(
            "welch windowsize"))
        layout.addRow("Welch window size:", self.welchWindowSize)

    def getProcessOptions(self):
        return {"windowsize": float(self.windowSize.text()),
                "sample_rate": float(self.samplingRate.text()),
                "freq_method": self.frequencyMethod.currentText(),
                "welch_wsize": float(self.welchWindowSize.text())}

    def setSamplingRate(self, rate):
        self.samplingRate.setText(f"{rate:.2f}")

    def anyOptionEmpty(self):
        return (not self.samplingRate.text() or not self.windowSize.text()
                or not self.welchWindowSize.text())


class ProcessOptionsWidget(QtWidgets.QGroupBox):
    availableProcessors = {}
    for section in _ANALYZECONFIG:
        if section is not None and section.startswith("Processor."):
            # new ProcessorWidget
            name = section.removeprefix("Processor.")
            availableProcessors[name] = globals()[name + "Widget"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Process data")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.availableProcessors = QtWidgets.QComboBox()
        self.availableProcessors.addItems(
            ProcessOptionsWidget.availableProcessors)
        layout.addWidget(self.availableProcessors)

        self.stackedProcessorLayout = QtWidgets.QStackedLayout()
        for proc in ProcessOptionsWidget.availableProcessors.values():
            proc = proc()
            proc.OptionsChanged.connect(self._monitorApplyButton)
            self.stackedProcessorLayout.addWidget(proc)
        layout.addLayout(self.stackedProcessorLayout)
        self.availableProcessors.currentIndexChanged.connect(
            self.stackedProcessorLayout.setCurrentIndex)
        self.stackedProcessorLayout.currentChanged.connect(
            self._monitorApplyButton)

        self.applyButton = QtWidgets.QPushButton("Apply")
        self.applyButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                       QtWidgets.QSizePolicy.Minimum)
        layout.addWidget(self.applyButton, alignment=Qt.AlignRight)

    def setSamplingRate(self, rate):
        for idx in range(self.stackedProcessorLayout.count()):
            self.stackedProcessorLayout.widget(idx).setSamplingRate(rate)

    def _monitorApplyButton(self):
        if self.stackedProcessorLayout.currentWidget().anyOptionEmpty():
            self.applyButton.setEnabled(False)

        else:
            self.applyButton.setEnabled(True)

    def currentOptions(self):
        data = self.stackedProcessorLayout.currentWidget().getProcessOptions()
        data["processor"] = self.availableProcessors.currentText()

        return data
