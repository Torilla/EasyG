from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt

import pyqtgraph as pg

from .splitter import GridSplitterWidget


class EasyGPlotWidget(pg.PlotWidget):

    """class EasyGPlotWidget

    class Extending the functionality of the original pyqtgraph.PlotWidget

    Attributes:
        NewROICoordinates (QtCore.pyqtSignal[float, float]): Signal emitted
            when the user draws a RegionOfInteres on the Screen. It provides
            the x0, x1 (so the length) coordinates of the ROI.
        plotItem (pyqtgraph.PlotItem): See pyqtgraph.PlotWidget documentaiton
        TitleChangeRequest (QtCore.pyqtSignal[float, float]): Description
        titleLabelContextMenu (QtWidgets.QMenu): A QMenu instance used when
            the user wants to change the Titel of the PlotWidget
        titleLabelEditTextAction (QtWidgets.QAction): The action executed when
            a titelLabelContextMenu is executed
    """

    # self
    TitleChangeRequest = QtCore.pyqtSignal(object)
    # x0, x1 coordinates of self._ROI
    NewROICoordinates = QtCore.pyqtSignal(float, float)

    def __init__(self,
                 parent: QtCore.QObject | None = None,
                 background: str = 'default',
                 plotItem: pg.PlotItem | None = None,
                 **kargs):
        """Initalize a new EasyGPlotWidget isntance. The method is directly
        taken from the original pyqtgraph.PlotWidget source as we need to
        modify its behavior without resorting to super().__init__ (see below)

        Args:
            see pyqtgraph.PlotWidget documentation
        """
        # ----------------------------------------------------------------------
        # canno't use super().__init__ to call the baseclass init because
        # it conflicts with QObject init. We have to call the code ourself.
        # It is taken directly from the source:
        # https://pyqtgraph.readthedocs.io/en/latest/_modules/pyqtgraph/widgets/PlotWidget.html
        # ----------------------------------------------------------------------
        pg.GraphicsView.__init__(self, parent, background=background)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                           QtWidgets.QSizePolicy.Policy.Expanding)
        self.enableMouse(False)
        if plotItem is None:
            self.plotItem = pg.PlotItem(**kargs)
        else:
            self.plotItem = plotItem
        self.setCentralItem(self.plotItem)
        # Explicitly wrap methods from plotItem
        for m in ['addItem', 'removeItem', 'autoRange', 'clear',
                  'setAxisItems', 'setXRange', 'setYRange', 'setRange',
                  'setAspectLocked', 'setMouseEnabled', 'setXLink', 'setYLink',
                  'enableAutoRange', 'disableAutoRange', 'setLimits',
                  'register', 'unregister', 'viewRect']:
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

    def _showTitleContextMenu(self, event: QtGui.QMouseEvent) -> None:
        event.accept()
        action = self.titleLabelContextMenu.exec(QtGui.QCursor.pos())

        if action == self.titleLabelEditTextAction:
            self.TitleChangeRequest.emit(self)

    def getTitle(self) -> str:
        return self.plotItem.titleLabel.text

    def setTitle(self, title: str) -> None:
        self.plotItem.setTitle(title)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent) -> None:
        event.accept()

        self._ROI.setSize((0, 0))

        pos = self.getViewBox().mapSceneToView(event.pos())
        self._ROI.setPos(pos)
        self._setROISizeConnection = self.scene().sigMouseMoved.connect(
            self._setROISize)
        self._ROI.show()

    @QtCore.pyqtSlot(object)
    def _setROISize(self, pos: QtCore.QPointF) -> None:
        pos = self.getViewBox().mapSceneToView(pos)
        self._ROI.setSize(pos - self._ROI.pos())

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent) -> None:
        if self._setROISizeConnection is not None:
            event.accept()
            self.scene().sigMouseMoved.disconnect(self._setROISizeConnection)
            self._setROISizeConnection = None

        else:
            super().mouseReleaseEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        if event.button() == Qt.RightButton and self._ROI.isVisible():
            event.accept()
            self._ROI.hide()

        else:
            super().mousePressEvent(event)

    def emitROICoordinates(self) -> None:
        x0 = self._ROI.pos().x()
        x1 = x0 + self._ROI.size().x()

        self.NewROICoordinates.emit(x0, x1)


class PlotManagerWidget(QtWidgets.QWidget):
    plotWidgetType = EasyGPlotWidget

    # previous, newtitle
    TitleChanged = QtCore.pyqtSignal(str, str)

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

    def _onColumnInsertRequest(self, columnIdx: int) -> None:
        self.insertColumn(columnIdx)
        self.insertPlotWidget(columnIdx, 0)

    def _onWidgetInsertRequest(self, columnIdx: int, rowIdx: int) -> None:
        self.insertPlotWidget(columnIdx, rowIdx)

    def _onWidgetRemoveRequest(self, columnIdx: int, rowIdx: int) -> None:
        self.removePlotWidget(columnIdx, rowIdx)

    def _onTitleChangeRequest(
        self, widget: EasyGPlotWidget, defaultTitle: str = "Plot"
    ) -> None:
        oldTitle = widget.getTitle()
        newTitle, isValid = QtWidgets.QInputDialog.getText(self,
                                                           "Edit plot title",
                                                           "New title:",
                                                           text=defaultTitle)

        if isValid:
            widget.setTitle(newTitle)

            self.TitleChanged.emit(oldTitle, newTitle)

    def insertColumn(self, columnIdx: int) -> None:
        self.splitterWidget.insertColumn(columnIdx)

    def insertPlotWidget(
        self, columnIdx: int, rowIdx: int, *args, **kwargs
    ) -> None:
        widget = self.plotWidgetType(*args, **kwargs)
        widget.TitleChangeRequest.connect(self._onTitleChangeRequest)
        self.splitterWidget.insertWidget(columnIdx, rowIdx, widget)

    def removePlotWidget(self, columnIdx: int, rowIdx: int) -> None:
        self.splitterWidget.removeWidget(columnIdx, rowIdx)

    def addItemToPlot(
        self, columnIdx: int, rowIdx: int, item: pg.PlotItem, *args, **kwargs
    ) -> None:
        self.splitterWidget.widget(columnIdx, rowIdx).addItem(item, *args,
                                                              **kwargs)
