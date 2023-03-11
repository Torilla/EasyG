from PyQt5 import QtWidgets, QtGui, QtCore


class ServerConfigurationWidget(QtWidgets.QGroupBox):
    ConfigurationChanged = QtCore.pyqtSignal()

    def __init__(self, HostAddress, HostPort, maxPendingConnections,
                 title="Server Configuration", *args, **kwargs):
        super().__init__(title, *args, **kwargs)

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.ip_edit = QtWidgets.QLineEdit()
        self.ip_edit.setToolTip("The IP the server is listening at.")
        self.ip_edit.setText(HostAddress)
        layout.addRow("IP Adress:", self.ip_edit)

        self.port_edit = QtWidgets.QLineEdit()
        self.port_edit.setText(str(HostPort))
        self.port_edit.setToolTip("The port the server will be using.")
        self.port_edit.setValidator(QtGui.QIntValidator())
        layout.addRow("Port:", self.port_edit)

        self.maxpending_edit = QtWidgets.QLineEdit()
        self.maxpending_edit.setText(str(maxPendingConnections))
        self.maxpending_edit.setToolTip("Maximum no. of pending connections")
        self.maxpending_edit.setValidator(QtGui.QIntValidator(1, 1000))
        layout.addRow("Maximum pending:",
                      self.maxpending_edit)

        self.buttons = QtWidgets.QDialogButtonBox(self)
        self.buttons.setGeometry(QtCore.QRect(50, 240, 341, 32))
        self.buttons.setOrientation(QtCore.Qt.Horizontal)
        self.buttons.setStandardButtons(
            QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_configuration(self):
        return {
            "HostAddress": self.ip_edit.text(),
            "HostPort": int(self.port_edit.text()),
            "maxPendingConnections": int(self.maxpending_edit.text())
        }

    def accept(self):
        self.ConfigurationChanged.emit()
        self.hide()

    def reject(self):
        self.hide()
