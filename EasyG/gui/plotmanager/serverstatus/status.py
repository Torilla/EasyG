from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5 import QtCore


class StatusCircleWidget(QtWidgets.QWidget):
    def paintEvent(self, event):
        p = QtGui.QPainter(self)
        p.setBrush(QtCore.Qt.red)
        p.setPen(QtCore.Qt.black)
        p.drawEllipse(self.rect().center(), 15, 15)

    def sizeHint(self):
        return QtCore.QSize(50, 50)


class ServerStatusWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        statusLayout = QtWidgets.QFormLayout()
        self.statusCircle = StatusCircleWidget()
        statusLayout.addRow("Status:", self.statusCircle)
        layout.addLayout(statusLayout)

        self.nameLabel = QtWidgets.QLabel()
        nameLayout = QtWidgets.QFormLayout()
        nameLayout.addRow("Client name:", self.nameLabel)
        layout.addLayout(nameLayout)

        self.addressLabel = QtWidgets.QLabel()
        self.addressLabel.resize(50, 20)
        addressLayout = QtWidgets.QFormLayout()
        addressLayout.addRow("Client Address:", self.addressLabel)
        layout.addLayout(addressLayout)

        layout.addStretch()
