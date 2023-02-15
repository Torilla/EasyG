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
        # last 'widget' is stretch, so omit it
        return (self._contentLayout.itemAt(i).widget()
                for i in range(self._contentLayout.count() - 1))

    def clear(self):
        for idx in range(self._contentLayout.count() - 1):
            w = self._contentLayout.takeAt(idx).widget()
            w.setParent(None)

    def addBox(self, boxTitle, boxContent):
        box = CollapsibleDataList(boxTitle)
        for item in boxContent:
            box.addItem(item)

        self._contentLayout.insertWidget(self._contentLayout.count() - 1, box)

    def updateBoxTitle(self, oldTitle, newTitle):
        for box in self._iterBoxes():
            if box.toggleButton.text() == oldTitle:
                box.toggleButton.setText(newTitle)

    def setConfiguration(self, ownedItems, forreignItems):
        self.clear()
        for plot, items in ownedItems.items():
            self.addBox(plot, items)

        if forreignItems:
            self.addBox("Other Tabs", forreignItems)

