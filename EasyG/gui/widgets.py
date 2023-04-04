from typing import Any

from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt

import pyqtgraph as pg


class ServerConfigurationWidget(QtWidgets.QGroupBox):
    ConfigurationChanged = QtCore.pyqtSignal()

    def __init__(self, title="Server Configuration", *args, **kwargs):
        super().__init__(title, *args, **kwargs)

        layout = QtWidgets.QFormLayout()
        self.setLayout(layout)

        self.ip_edit = QtWidgets.QLineEdit()
        self.ip_edit.setToolTip("The IP the server is listening at.")
        layout.addRow("IP Adress:", self.ip_edit)

        self.port_edit = QtWidgets.QLineEdit()
        self.port_edit.setToolTip("The port the server will be using.")
        self.port_edit.setValidator(QtGui.QIntValidator())
        layout.addRow("Port:", self.port_edit)

        self.maxpending_edit = QtWidgets.QLineEdit()
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

    def set_configuration(self, config):
        self.ip_edit.setText(config["HostAddress"])
        self.port_edit.setText(str(config["HostPort"]))
        self.maxpending_edit.setText(str(config["maxPendingConnections"]))

    def accept(self):
        self.ConfigurationChanged.emit()
        self.hide()

    def reject(self):
        self.hide()


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


class ProxyWidget(QtWidgets.QWidget):
    def __init__(self, widget: QtWidgets.QWidget, *args: Any, **kwargs: Any):
        """Initialize a new SplitterProxyWidget instance.

        Args:
            widget (QtWidgets.QWidget): The widget that should be proxied
            *args: Forwared to QtWidgets.QWidget.__init__
            **kwargs: Forwared to QtWidgets.QWidget.__init__
        """
        super().__init__(*args, **kwargs)

        self.__widget = widget
        self.__widget.setParent(self)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)
        layout.addWidget(self.__widget, 0, 0)

    def __getattr__(self, key):
        return getattr(self.__widget, key)

    def widget(self) -> QtWidgets.QWidget:
        """Return the proxied widget.

        Returns:
            QtWidgets.QWidget: The proxied widget.
        """
        return self.__widget


class SplitterProxyWidget(ProxyWidget):

    """class SplitterProxyWidget

    class providing additional buttons for an already existing widget which
    will be proxied. The ProxyWidget provides access to all methods of the
    proxied widget if they are not explicitly overriden by the ProxyWidget.

    All buttons are hovered over the top right corner of the proxied widget.
    If a button is clicked the corresponding class Signal is emitted.

    Attributes:
        buttonLayout (QtWidgets.QHBoxLayout): The Layout holding the buttons
            provided by the proxy widget
        extendHorizontalButton (QtWidgets.QToolButton): Button emitting an
            'ExtendHorizontalButtonClicked' signal
        ExtendHorizontalButtonClicked (QtCore.pyqtSignal[bool, object]): Signal
            emitted when the extendHorizontalButton was pressed.
        extendVerticalButton (QtWidgets.QToolButton): Button emitting an
            'ExtendVerticalButtonClicked' signal
        ExtendVerticalButtonClicked (QtCore.pyqtSignal[bool, object]): Signal
            emitted when the extendVerticalButton was pressed.
        quitButton (QtWidgets.QToolButton): utton emitting an
            'QuitButtonClicked' signal
        QuitButtonClicked (QtCore.pyqtSignal[bool, object]): Signal
            emitted when the quitButton was pressed.

        private attributes overriden by SpliterProxyWidget and which are thus
        not accessible via the ProxyWidget interface. If you need to access any
        of these methods use SplitterProxyWidget.widget() to retrieve the
        original widget.
            __widget -> attribute storing the proxied widget. use widget() to
                retrieve the original widget
            widget() -> returns the original widget
            __on_quit_request() -> emits the QuitButtonClicked signal
            __on_extend_vertical_request() -> emits the
                ExtendVerticalButtonClicked signal
            __on_extend_horizontal_request() -> emits the
                extendHoriontalButtonClicked signal
            __add_default_buttons() -> used by class.__init__ to add extra
                buttons
            __getattr__() -> provides the interface to the original widget
    """

    ExtendVerticalButtonClicked = QtCore.pyqtSignal(bool, object)
    ExtendHorizontalButtonClicked = QtCore.pyqtSignal(bool, object)
    QuitButtonClicked = QtCore.pyqtSignal(bool, object)

    def __init__(self, widget: QtWidgets.QWidget, *args: Any, **kwargs: Any):
        super().__init__(widget, *args, **kwargs)
        self.__add_default_buttons()

    @QtCore.pyqtSlot(bool)
    def __on_quit_request(self, checked: bool) -> None:
        """Emit the QuitButtonClicked Signal.

        This method is not meant to be used directly but rather as slot for the
        quit button.

        Args:
            checked (bool): True if the button was checked, false otherwise
        """
        self.QuitButtonClicked.emit(checked, self)

    @QtCore.pyqtSlot(bool)
    def __on_extend_vertical_request(self, checked: bool) -> None:
        """Emit the ExtendVerticalButtonClicked Signal.

        This method is not meant to be used directly but rather as slot for the
        respective button in the UI.

        Args:
            checked (bool): True if the button was checked, false otherwise
        """
        self.ExtendVerticalButtonClicked.emit(checked, self)

    @QtCore.pyqtSlot(bool)
    def __on_extend_horizontal_request(self, checked: bool) -> False:
        """Emit the ExtendHorizontalButtonClicked Signal.

        This method is not meant to be used directly but rather as slot for the
        respective button in the UI.

        Args:
            checked (bool): True if the button was checked, false otherwise
        """
        self.ExtendHorizontalButtonClicked.emit(checked, self)

    def __add_default_buttons(self) -> None:
        """Adds a ExtendHorizontal, ExtendVertical and QuitButton hovering at
        the top right of the proxied widget. The ExtendVerticalButton is
        hidden by default.
        """
        def quit():
            self.quitButton = QtWidgets.QToolButton()
            self.quitButton.setToolTip("Remove this plot.")
            self.quitButton.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonIconOnly)

            icon = self.style().standardIcon(
                QtWidgets.QStyle.SP_TitleBarCloseButton)
            self.quitButton.setIcon(icon)
            self.quitButton.clicked.connect(self.__on_quit_request)

            self.buttonLayout.addWidget(self.quitButton)

        def extend_vertical():
            self.extendVerticalButton = QtWidgets.QToolButton()
            self.extendVerticalButton.setToolTip(
                "Add a new plot below this plot.")
            self.extendVerticalButton.setToolButtonStyle(
                Qt.ToolButtonStyle.ToolButtonIconOnly)

            icon = self.style().standardIcon(
                QtWidgets.QStyle.SP_ToolBarVerticalExtensionButton)
            self.extendVerticalButton.setIcon(icon)
            self.extendVerticalButton.clicked.connect(
                self.__on_extend_vertical_request)

            self.buttonLayout.addWidget(self.extendVerticalButton)

        def extend_horizontal():
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
                    self.__on_extend_horizontal_request)

                self.buttonLayout.addWidget(self.extendHorizontalButton)

        self.buttonLayout = QtWidgets.QHBoxLayout()
        self.layout().addLayout(self.buttonLayout, 0, 0,
                                Qt.AlignTop | Qt.AlignRight)
        extend_vertical()
        extend_horizontal()
        quit()

        # extend horizontal is hidden by default
        self.extendHorizontalButton.hide()


class SublevelSplitter(QtWidgets.QSplitter):

    """class SubleverSplitter

    Used as a second level of splitting in the GridSplitterWidget. Simply adds
    another QSplitter.
    """

    def __init__(self, *args, **kwargs):
        """Initalize a new SublevelSplitter

        Args:
            *args: Forwared to QtWidgets.QWidget.__init__
            **kwargs: Forwared to QtWidgets.QWidget.__init__
        """
        super().__init__(orientation=Qt.Vertical, *args, **kwargs)

    def setOrientation(self, *args, **kwargs):
        raise NotImplementedError("Can't set orientation of SublevelSplitter")


class GridSplitterWidget(QtWidgets.QSplitter):

    """class GridSplitterWidget

    This class provides a way of storing a grid of widgets. The grid layout
    is Column first row second. This means the columns can be adjusted in
    width only globally, while the rows inside the columns can be adjusted
    independently of any other columns

    Attributes:
        ColumnInsertRequest (QtCore.pyqtSignal[int]): Emitted with the
            respective column index where to insert a new column in the grid.
        proxyWidgetType (SplitterProxyWidget): The used ProxyWidget type.
        WidgetInsertRequest (QtCore.pyqtSignal[int, int]): Emitted with the
            respective column and row indices where to insert a new Widget.
        WidgetRemoveRequest (QtCore.pyqtSignal[int, int]): Emitted with the
            respective column and row indices where to remove a widget
    """

    proxyWidgetType = SplitterProxyWidget

    # columnIdx
    ColumnInsertRequest = QtCore.pyqtSignal(int)
    # columnIdx, rowIdx
    WidgetInsertRequest = QtCore.pyqtSignal(int, int)
    WidgetRemoveRequest = QtCore.pyqtSignal(int, int)

    def __init__(self, *args, **kwargs):
        """Initalize a new GridSplitterWidget

        Args:
            *args: Forwared to QtWidgets.QWidget.__init__
            **kwargs: Forwared to QtWidgets.QWidget.__init__
        """
        super().__init__(orientation=Qt.Horizontal, *args, **kwargs)

    def _initNewProxyWidget(self, widget):
        proxyWidget = self.proxyWidgetType(widget=widget)
        proxyWidget.ExtendVerticalButtonClicked.connect(
            self.onSublevelExtendVertical)
        proxyWidget.QuitButtonClicked.connect(self.onSublevelQuit)
        proxyWidget.ExtendHorizontalButtonClicked.connect(
            self.onSublevelExtendHorizontal)

        return proxyWidget

    def setOrientation(self, *args, **kwargs):
        raise NotImplementedError("Can't set orientation of ToplevelSplitter")

    def columnCount(self) -> int:
        """Return the current number of clumns in the grid.

        Returns:
            int: The number of columns in the grid
        """
        return self.count()

    def rowCountOfColumn(self, columnIdx: int) -> int:
        """Return the current row count in column with index columnIdx

        Args:
            columnIdx (int): The index of the column to query

        Returns:
            int: The number of rows in the requested column
        """
        return self.widget(columnIdx).count()

    def widget(
        self, columnIdx: int, rowIdx: int | None = None
    ) -> QtWidgets.QWidget:
        """Return the widget which is stored at coordinates columnIdx, rowIdx.
        If rowIdx is None, the entire column is returned.

        Args:
            columnIdx (int): The columnIndex to query
            rowIdx (int | None, optional): The rowIndex to query
        """
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

    def insertColumn(self, columnIdx: int) -> None:
        """Insert a new Column into the grid. The column will be empty by
        default. Use insertWidget to add widget to the column

        Args:
            columnIdx (int): Where to insert the column
        """
        super().insertWidget(columnIdx, SublevelSplitter())

    def insertWidget(
        self, columnIdx: int, rowIdx: int, widget: QtWidgets.QWidget
    ) -> None:
        """Insert a new Widget into the Grid.

        Args:
            columnIdx (int): The column Index where to insert
            rowIdx (int): The row Index where to insert
            widget (QtWidgets.QWidget): The widget to insert
        """
        widget = self._initNewProxyWidget(widget)

        if rowIdx == 0 or not self.rowCountOfColumn(columnIdx):
            # first widget in the row gets extend horizontal button
            widget.extendHorizontalButton.show()

            try:
                # if we had one in first position, hide its button instead
                self.widget(columnIdx, 0).extendHorizontalButton.hide()
            except IndexError:
                pass

        self.widget(columnIdx).insertWidget(rowIdx, widget)

    def removeWidget(self, columnIdx: int, rowIdx: int) -> None:
        """Remove a widget from the Grid. The widget will be scheduled for
        deletion.

        Args:
            columnIdx (int): The column Index to query
            rowIdx (int): The row Index to query
        """
        if rowIdx == 0 and self.rowCountOfColumn(columnIdx) > 1:
            self.widget(columnIdx, 1).extendHorizontalButton.show()

        widget = self.widget(columnIdx, rowIdx)
        widget.hide()
        widget.deleteLater()
        widget.setParent(None)

    def indexOf(self, widget: QtWidgets.QWidget) -> tuple[int, int]:
        """Retun the column and row Indices of the stored widget.

        Args:
            widget (QtWidgets.QWidget): The widget to find.

        Returns:
            tuple[int, int]: The column and row index of the stored widget

        Raises:
            ValueError: If the widget cannot be found.
        """
        isProxy = isinstance(widget, self.proxyWidgetType)

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

    @QtCore.pyqtSlot(bool, object)
    def onSublevelQuit(self, checked: bool, widget: QtWidgets.QWidget) -> None:
        """Slot called when a QuitButton Signal was emitted."""
        columnIdx, rowIdx = self.indexOf(widget)
        self.WidgetRemoveRequest.emit(columnIdx, rowIdx)

    @QtCore.pyqtSlot(bool, object)
    def onSublevelExtendVertical(
        self, checked: bool, widget: QtWidgets.QWidget
    ) -> None:
        """Slot called when a ExtendVertical Signal was emitted."""
        columnIdx, rowIdx = self.indexOf(widget)
        self.WidgetInsertRequest.emit(columnIdx, rowIdx + 1)

    @QtCore.pyqtSlot(bool, object)
    def onSublevelExtendHorizontal(
        self, checked: bool, widget: QtWidgets.QWidget
    ) -> None:
        """Slot called when a ExtendHorizontal Signal was emitted."""
        columnIdx, _ = self.indexOf(widget)
        self.ColumnInsertRequest.emit(columnIdx + 1)
