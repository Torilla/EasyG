from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt


class SplitterProxyWidget(QtWidgets.QWidget):

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

    def __init__(self, widget: QtWidgets.QWidget, *args, **kwargs):
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

        self.__add_default_buttons()

    def widget(self) -> QtWidgets.QWidget:
        """Return the proxied widget.

        Returns:
            QtWidgets.QWidget: The proxied widget.
        """
        return self.__widget

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

    def __getattr__(self, attr):
        return getattr(self.__widget, attr)


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
