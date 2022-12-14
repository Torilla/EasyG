from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt


class SplitterProxyWidget(QtWidgets.QWidget):
    extendVerticalButtonClicked = QtCore.pyqtSignal(bool, object)
    extendHorizontalButtonClicked = QtCore.pyqtSignal(bool, object)
    quitButtonClicked = QtCore.pyqtSignal(bool, object)

    def __init__(self, widget, parent=None):
        super().__init__(parent=parent)

        self._widget = widget
        self._widget.setParent(self)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self._widget, 0, 0)

        self._addDefaultButtons()

    def widget(self):
        return self._widget

    @QtCore.pyqtSlot(bool)
    def _onQuitRequest(self, checked):
        self.quitButtonClicked.emit(checked, self)

    @QtCore.pyqtSlot(bool)
    def _onExtendVerticalRequest(self, checked):
        self.extendVerticalButtonClicked.emit(checked, self)

    @QtCore.pyqtSlot(bool)
    def _onExtendHorizontalRequest(self, checked):
        self.extendHorizontalButtonClicked.emit(checked, self)

    def _addDefaultButtons(self):
        def quit():
            self.quitButton = QtWidgets.QToolButton()
            self.quitButton.setToolTip("Remove this plot.")
            self.quitButton.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonIconOnly)

            icon = self.style().standardIcon(
                QtWidgets.QStyle.SP_TitleBarCloseButton)
            self.quitButton.setIcon(icon)
            self.quitButton.clicked.connect(self._onQuitRequest)

            self.buttonLayout.addWidget(self.quitButton)

        def extendVertical():
            self.extendVerticalButton = QtWidgets.QToolButton()
            self.extendVerticalButton.setToolTip(
                "Add a new plot below this plot.")
            self.extendVerticalButton.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonIconOnly)

            icon = self.style().standardIcon(
                QtWidgets.QStyle.SP_ToolBarVerticalExtensionButton)
            self.extendVerticalButton.setIcon(icon)
            self.extendVerticalButton.clicked.connect(
                self._onExtendVerticalRequest)

            self.buttonLayout.addWidget(self.extendVerticalButton)

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(self.buttonLayout, 0, 0,
                                Qt.AlignTop | Qt.AlignRight)
        extendVertical()
        quit()

    def addExtendHorizontalButton(self):
        if not hasattr(self, "extendHorizontalButton"):
            # only add it once
            self.extendHorizontalButton = QtWidgets.QToolButton()
            self.extendHorizontalButton.setToolTip(
                "Add a new plot to the right of this plot.")
            self.extendHorizontalButton.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonIconOnly)

            icon = self.style().standardIcon(
                QtWidgets.QStyle.SP_ToolBarHorizontalExtensionButton)
            self.extendHorizontalButton.setIcon(icon)
            self.extendHorizontalButton.clicked.connect(
                self._onExtendHorizontalRequest)

            self.buttonLayout.addWidget(self.extendHorizontalButton)

    def __getattr__(self, attr):
        return getattr(self._widget, attr)


class SublevelSplitter(QtWidgets.QSplitter):
    def __init__(self, parent=None):
        super().__init__(orientation=Qt.Vertical, parent=parent)

    def setOrientation(self, *args, **kwargs):
        raise NotImplementedError("Can't set orientation of SublevelSplitter")


class ToplevelSplitter(QtWidgets.QSplitter):
    proxyWidgetType = SplitterProxyWidget

    # columnIdx
    ColumnInsertRequest = QtCore.pyqtSignal(int)
    # columnIdx, rowIdx
    WidgetInsertRequest = QtCore.pyqtSignal(int, int)
    WidgetRemoveRequest = QtCore.pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(orientation=Qt.Horizontal, parent=parent)

    def setOrientation(self, *args, **kwargs):
        raise NotImplementedError("Can't set orientation of ToplevelSplitter")

    def insertColumn(self, columnIdx=None):
        if columnIdx is None:
            columnIdx = self.count()

        super().insertWidget(columnIdx, SublevelSplitter())

    def removeColumn(self, columnIdx):
        widget = self.widget(columnIdx)
        widget.hide()
        widget.setParent(None)
        widget.deleteLater()

    def insertWidget(self, widget, columnIdx=None, rowIdx=None):
        if columnIdx is None:
            columnIdx = self.count() - 1

        colWidget = self.widget(columnIdx)

        if rowIdx is None:
            rowIdx = colWidget.count()

        proxyWidget = self.proxyWidgetType(widget=widget)
        proxyWidget.extendVerticalButtonClicked.connect(
            self.onSublevelExtendVertical)
        proxyWidget.quitButtonClicked.connect(self.onSublevelQuit)

        if colWidget.count() == 0:
            # first widget in the column gets a extend horizontal button
            proxyWidget.addExtendHorizontalButton()

        # always connect the extend horizontal button because it might
        # get added later
        proxyWidget.extendHorizontalButtonClicked.connect(
            self.onSublevelExtendHorizontal)

        colWidget.insertWidget(rowIdx, proxyWidget)

    def removeWidget(self, columnIdx, rowIdx):
        widget = self.widget(columnIdx, rowIdx)
        widget.hide()
        widget.deleteLater()
        widget.setParent(None)

        if self.widget(columnIdx).count() == 0:
            # if the column is now empty, remove it
            self.removeColumn(columnIdx)

        elif rowIdx == 0:
            # the first item should always have extend horiztonal button
            self.widget(columnIdx, 0).addExtendHorizontalButton()

    def widget(self, columnIdx, rowIdx=None):
        colWidget = super().widget(columnIdx)

        if colWidget is None:
            raise IndexError(f"Column Index {columnIdx} out of bound: "
                             f"len({self.count()})")

        if rowIdx is not None:
            widget = colWidget.widget(rowIdx)

            if widget is None:
                raise IndexError(f"Row Index {rowIdx} out of bound: "
                                 f"len({colWidget.count()})")

        else:
            widget = colWidget

        return widget

    def indexOf(self, widget):
        isProxy = isinstance(widget, SplitterProxyWidget)

        for columnIdx in range(self.count()):
            colWidget = self.widget(columnIdx)

            if isProxy:
                rowIdx = colWidget.indexOf(widget)
                if rowIdx != -1:
                    break

            else:
                # we store proxyWidgets, not the widgets directly
                for rowIdx in range(colWidget.count()):
                    if colWidget.widget(rowIdx).widget() is widget:
                        break
                else:
                    continue

                break

        else:
            raise ValueError(f"No such widget: {widget}")

        return columnIdx, rowIdx

    def iterWidgets(self):
        for colIdx in range(self.count()):
            colWidget = self.widget(colIdx)
            for rowIdx in range(colWidget.count()):
                # we store proxywidgets, return the widget contained inside
                yield colWidget.widget(rowIdx).widget()

    @QtCore.pyqtSlot(bool, object)
    def onSublevelQuit(self, checked, widget):
        columnIdx, rowIdx = self.indexOf(widget)
        self.WidgetRemoveRequest.emit(columnIdx, rowIdx)

    @QtCore.pyqtSlot(bool, object)
    def onSublevelExtendVertical(self, checked, widget):
        columnIdx, rowIdx = self.indexOf(widget)
        self.WidgetInsertRequest.emit(columnIdx, rowIdx + 1)

    @QtCore.pyqtSlot(bool, object)
    def onSublevelExtendHorizontal(self, checked, widget):
        columnIdx, _ = self.indexOf(widget)
        self.ColumnInsertRequest.emit(columnIdx + 1)
