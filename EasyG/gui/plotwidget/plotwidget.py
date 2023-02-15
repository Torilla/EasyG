from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt

import pyqtgraph as pg

from .splitter import GridSplitterWidget


class EasyGPlotWidget(pg.PlotWidget):
    # self
    TitleChangeRequest = QtCore.pyqtSignal(object)
    # x0, x1 coordinates of self._ROI
    NewROICoordinates = QtCore.pyqtSignal(float, float)

    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        # ----------------------------------------------------------------------
        # canno't use super().__init__ to call the baseclass init because
        # it conflicts with QObject init. We have to call the code ourself.
        # It is taken directly from the source:
        # https://pyqtgraph.readthedocs.io/en/latest/_modules/pyqtgraph/widgets/PlotWidget.html
        # ----------------------------------------------------------------------
        pg.GraphicsView.__init__(self, parent, background=background)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)
        self.enableMouse(False)
        if plotItem is None:
            self.plotItem = pg.PlotItem(**kargs)
        else:
            self.plotItem = plotItem
        self.setCentralItem(self.plotItem)
        # Explicitly wrap methods from plotItem
        for m in ['addItem', 'removeItem', 'autoRange', 'clear', 'setAxisItems', 'setXRange',
                  'setYRange', 'setRange', 'setAspectLocked', 'setMouseEnabled',
                  'setXLink', 'setYLink', 'enableAutoRange', 'disableAutoRange',
                  'setLimits', 'register', 'unregister', 'viewRect']:
            setattr(self, m, getattr(self.plotItem, m))
        self.plotItem.sigRangeChanged.connect(self.viewRangeChanged)
        # -----------------------END OF ORIGINAL INIT---------------------------

        self.addLegend()

        # region of interest, activated by double clicking
        self._ROI = pg.RectROI(pos=(0, 0), size=(0, 0),
                               pen=pg.mkPen("g", width=1.5, style=Qt.DashLine),
                               invertible=True)
        self._ROI.sigRegionChangeFinished.connect(self.emitROICoordinates)
        self._ROI.hide()
        self.addItem(self._ROI)

        # connection of the setROISize slot upon double click
        self._setROISizeConnection = None

        self.titleLabelContextMenu = QtWidgets.QMenu(self)
        self.titleLabelEditTextAction = self.titleLabelContextMenu.addAction(
            "Edit Title")

        # inject a contextMenuEventHandler into the titleLabel so we can catch
        # right click events
        self.plotItem.titleLabel.contextMenuEvent = self._showTitleContextMenu

    def _showTitleContextMenu(self, event):
        event.accept()
        action = self.titleLabelContextMenu.exec(QtGui.QCursor.pos())

        if action == self.titleLabelEditTextAction:
            self.TitleChangeRequest.emit(self)

    def getTitle(self):
        return self.plotItem.titleLabel.text

    def setTitle(self, title):
        self.plotItem.setTitle(title)

    def mouseDoubleClickEvent(self, event):
        event.accept()

        self._ROI.setSize((0, 0))

        pos = self.getViewBox().mapSceneToView(event.pos())
        self._ROI.setPos(pos)
        self._setROISizeConnection = self.scene().sigMouseMoved.connect(
            self._setROISize)
        self._ROI.show()

    @QtCore.pyqtSlot(object)
    def _setROISize(self, pos):
        pos = self.getViewBox().mapSceneToView(pos)
        self._ROI.setSize(pos - self._ROI.pos())

    def mouseReleaseEvent(self, event):
        if self._setROISizeConnection is not None:
            event.accept()
            self.scene().sigMouseMoved.disconnect(self._setROISizeConnection)
            self._setROISizeConnection = None

        else:
            super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.RightButton and self._ROI.isVisible():
            event.accept()
            self._ROI.hide()

        else:
            super().mousePressEvent(event)

    def emitROICoordinates(self):
        x0 = self._ROI.pos().x()
        x1 = x0 + self._ROI.size().x()

        self.NewROICoordinates.emit(x0, x1)


class PlotManagerWidget(QtWidgets.QWidget):
    plotWidgetType = EasyGPlotWidget

    # previous, newtitle
    TitleChanged = QtCore.pyqtSignal(str, str)

    PlotConfigOutdated = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.splitterWidget = GridSplitterWidget()
        layout.addWidget(self.splitterWidget, 1)

        self.splitterWidget.ColumnInsertRequest.connect(
            self._onColumnInsertRequest)
        self.splitterWidget.WidgetInsertRequest.connect(
            self._onWidgetInsertRequest)
        self.splitterWidget.WidgetRemoveRequest.connect(
            self._onWidgetRemoveRequest)

    def _onColumnInsertRequest(self, columnIdx):
        self.insertColumn(columnIdx)
        self.insertPlotWidget(columnIdx, 0)
        self.PlotConfigOutdated.emit()

    def _onWidgetInsertRequest(self, columnIdx, rowIdx):
        self.insertPlotWidget(columnIdx, rowIdx)
        self.PlotConfigOutdated.emit()

    def _onWidgetRemoveRequest(self, columnIdx, rowIdx):
        self.removePlotWidget(columnIdx, rowIdx)
        self.PlotConfigOutdated.emit()

    def _onTitleChangeRequest(self, widget, defaultTitle="Plot"):
        oldTitle = widget.getTitle()
        newTitle, isValid = QtWidgets.QInputDialog.getText(self,
                                                           "Edit plot title",
                                                           "New title:",
                                                           text=defaultTitle)

        if isValid:
            widget.setTitle(newTitle)

            self.TitleChanged.emit(oldTitle, newTitle)

    def insertColumn(self, columnIdx):
        self.splitterWidget.insertColumn(columnIdx)

    def insertPlotWidget(self, columnIdx, rowIdx, *args, **kwargs):
        widget = self.plotWidgetType(*args, **kwargs)
        widget.TitleChangeRequest.connect(self._onTitleChangeRequest)
        self.splitterWidget.insertWidget(columnIdx, rowIdx, widget)

    def removePlotWidget(self, columnIdx, rowIdx):
        self.splitterWidget.removeWidget(columnIdx, rowIdx)

    def addItemToPlot(self, columnIdx, rowIdx, item, *args, **kwargs):
        self.splitterWidget.widget(columnIdx, rowIdx).addItem(item, *args, **kwargs)

    def getCurrentPlotConfiguration(self):
        config = {}

        for colIdx in range(self.splitterWidget.columnCount()):
            for rowIdx in range(self.splitterWidget.rowCountOfColumn(colIdx)):
                w = self.splitterWidget.widget(colIdx, rowIdx)
                config[w.getTitle()] = [i.name() for i in w.listDataItems()]

        return config
