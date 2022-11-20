from PyQt5 import QtWidgets, QtCore, QtGui


class ResampleWidget(QtWidgets.QGroupBox):
    OptionsChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        samplePointsLayout = QtWidgets.QVBoxLayout()
        self.newSamplePointsLineEdit = QtWidgets.QLineEdit()
        self.newSamplePointsLineEdit.textChanged.connect(self.OptionsChanged)
        self.newSamplePointsLineEdit.setValidator(QtGui.QIntValidator())
        self.newSamplePointsLineEdit.setText("2")
        samplePointsLayout.addWidget(self.newSamplePointsLineEdit)

        self.newSamplePointsFactorCheckBox = QtWidgets.QCheckBox("Factor")
        self.newSamplePointsFactorCheckBox.setCheckState(QtCore.Qt.Checked)
        samplePointsLayout.addWidget(self.newSamplePointsFactorCheckBox)

        layout.addRow("Number of new sample points:", samplePointsLayout)

    def currentOptions(self):
        checkState = self.newSamplePointsFactorCheckBox.checkState()
        factor = checkState == QtCore.Qt.Checked
        return {
            "factor": factor,
            "num": int(self.newSamplePointsLineEdit.text())
        }

    def anyOptionEmpty(self):
        return not self.newSamplePointsLineEdit.text()


class DataManipulationWidget(QtWidgets.QGroupBox):
    manipulationMethods = {
        "Resample": ResampleWidget
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTitle("Manipulate data")

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.manipulationMethods = QtWidgets.QComboBox()
        self.manipulationMethods.addItems(
            DataManipulationWidget.manipulationMethods)
        layout.addWidget(self.manipulationMethods)

        self.stackedManipulationLayout = QtWidgets.QStackedLayout()
        for widget in DataManipulationWidget.manipulationMethods.values():
            widget = widget()
            widget.OptionsChanged.connect(self._monitorApplyButton)
            self.stackedManipulationLayout.addWidget(widget)
        layout.addLayout(self.stackedManipulationLayout)
        self.manipulationMethods.currentIndexChanged.connect(
            self.stackedManipulationLayout.setCurrentIndex)

        self.applyButton = QtWidgets.QPushButton()
        self.applyButton.setText("Apply")
        self.applyButton.setSizePolicy(QtWidgets.QSizePolicy.Preferred,
                                       QtWidgets.QSizePolicy.Minimum)
        layout.addWidget(self.applyButton, alignment=QtCore.Qt.AlignRight)

        self.stackedManipulationLayout.currentChanged.connect(
            self._monitorApplyButton)

    def currentOptions(self):
        opts = self.stackedManipulationLayout.currentWidget().currentOptions()
        opts["manipulation method"] = self.manipulationMethods.currentText()

        return opts

    def _monitorApplyButton(self):
        if self.stackedManipulationLayout.currentWidget().anyOptionEmpty():
            self.applyButton.setEnabled(False)

        else:
            self.applyButton.setEnabled(True)
