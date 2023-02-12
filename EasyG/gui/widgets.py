from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt


class PlotDataListItem(QtWidgets.QWidget):
    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)

        self.checkBox = QtWidgets.QCheckBox()
        layout.addWidget(self.checkBox)

        self.label = QtWidgets.QLabel(f"&{text}")
        layout.addWidget(self.label)
        self.label.setBuddy(self.checkBox)

    def text(self):
        return self.label.text()


class CollapsibleDataList(QtWidgets.QWidget):
    def __init__(self, plotItemTitle, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.toggleButton = QtWidgets.QToolButton(text=plotItemTitle,
                                                  checkable=True,
                                                  checked=False)
        self.toggleButton.setStyleSheet("QToolButton { border: none; }")
        self.toggleButton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toggleButton.setArrowType(Qt.DownArrow)
        self.toggleButton.pressed.connect(self.onToggleButtonPressed)
        layout.addWidget(self.toggleButton)

        self.contentLayout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.contentLayout)

        layout.addStretch()

    @QtCore.pyqtSlot()
    def onToggleButtonPressed(self):
        checked = self.toggleButton.isChecked()
        self.toggleButton.setArrowType(Qt.DownArrow
                                       if not checked
                                       else Qt.RightArrow)
        for i in range(self.contentLayout.count()):
            item = self.contentLayout.itemAt(i).widget()
            item.show() if not checked else item.hide()

    def addItem(self, item):
        item = PlotDataListItem(item)
        self.contentLayout.addWidget(item)

    def listItemNames(self):
        return [self.contentLayout.widget(i).text()
                for i in range(self.contentLayout.count())]


class PlotDataItemAndPlotterListWidget(QtWidgets.QDockWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._contentLayout = QtWidgets.QVBoxLayout()
        self._contentLayout.addStretch()
        contentWidget = QtWidgets.QWidget()
        contentWidget.setLayout(self._contentLayout)
        self.setWidget(contentWidget)

    def _iterBoxes(self):
        return (self._contentLayout.itemAt(i).widget()
                for i in range(self._contentLayout.count()))

    def clear(self):
        for box in self._iterBoxes():
            box.setParent(None)

    def addPlotItem(self, itemName):
        for box in self._iterBoxes():
            box.addItem(itemName)

    def addPlot(self, plotName):
        box = CollapsibleDataList(plotName)
        self._contentLayout.addWidget(box)

        for itemName in self._contentLayout.widget(0).listItemNames():
            box.addItem(itemName)

    def setConfiguration(self, ownedItems, forreignItems):
        self.clear()
        for item in owenedItems:
            self.addPlotItem(item)
