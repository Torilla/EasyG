from PyQt5 import QtWidgets, QtCore, QtGui


class CheckableLineEdit(QtWidgets.QWidget):
    def __init__(self, text=None, checkBoxTitle="Automatic",
                 checkState=QtCore.Qt.CheckState.Checked,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.lineEdit = QtWidgets.QLineEdit()
        self.lineEdit.setText(text)
        self.textChanged = self.lineEdit.textChanged
        # save text if user overrides it
        self._previousText = self.lineEdit.text()
        layout.addWidget(self.lineEdit)

        self.checkBox = QtWidgets.QCheckBox(checkBoxTitle)
        layout.addWidget(self.checkBox)

        self.checkBox.setCheckState(checkState)
        self._setLineEditEditable(checkState)
        self.checkBox.stateChanged.connect(self._setLineEditEditable)

    @QtCore.pyqtSlot(int)
    def _setLineEditEditable(self, checkState):
        if checkState == QtCore.Qt.CheckState.Checked:
            text = self.lineEdit.text()
            self.lineEdit.setText(self._previousText)
            self._previousText = text
            self.lineEdit.setEnabled(False)

        else:
            text = self.lineEdit.text()
            self.lineEdit.setText(self._previousText)
            self._previousText = text
            self.lineEdit.setEnabled(True)

    def setValidator(self, validator):
        self.lineEdit.setValidator(validator)

    def setText(self, text, override=False):
        if self.isChecked() or override:
            self.lineEdit.setText(text)

        else:
            self._previousText = text

    def text(self):
        return self.lineEdit.text()

    def isChecked(self):
        return self.checkBox.isChecked()


class ColorFieldButton(QtWidgets.QPushButton):
    def __init__(self, color=QtGui.QColorConstants.Green, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.colorDialog = QtWidgets.QColorDialog(parent=self)
        self.colorDialog.currentColorChanged.connect(
            self.colorDialog.setCurrentColor)
        self.colorDialog.setCurrentColor(color)
        self.setStyleSheet(f"background-color: {color.name()}")
        self.pressed.connect(self._setUserColor)

    def _setUserColor(self):
        self.colorDialog.exec()
        color = self.colorDialog.currentColor()
        self.setStyleSheet(f"background-color: {color.name()}")

    def currentColor(self):
        return self.colorDialog.currentColor()
