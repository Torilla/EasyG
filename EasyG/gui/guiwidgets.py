from PyQt5 import QtCore, QtWidgets

from EasyG.gui import widgets


class MainWindow(QtWidgets.QMainWindow):
    OpenExampleRequest = QtCore.pyqtSignal()

    def __init__(self, windowTitle="EasyG", geometry=(100, 100, 800, 600)):
        super().__init__()

        self.setWindowTitle(windowTitle)
        self.setGeometry(*geometry)

        self.tabManager = TabManagerWidget()
        self.setCentralWidget(self.tabManager)

        self._initMenuBar()

    def _initMenuBar(self):
        def fileMenu():
            self.fileMenu = menuBar.addMenu("&File")

            self.openMenu = self.fileMenu.addMenu("&Open")

            self.openFileAction = QtWidgets.QAction("&File")
            self.openMenu.addAction(self.openFileAction)

            self.openExampleAction = QtWidgets.QAction("&Example")
            self.openExampleAction.triggered.connect(self.OpenExampleRequest.emit)
            self.openMenu.addAction(self.openExampleAction)

            self.fileMenu.addSeparator()

            self.exitAction = QtWidgets.QAction("&Exit")
            self.exitAction.triggered.connect(self.deleteLater)
            self.fileMenu.addAction(self.exitAction)

        def serverMenu():
            self.serverMenu = menuBar.addMenu("&Server")

            self.configureServerAction = QtWidgets.QAction("&Configure")
            self.serverMenu.addAction(self.configureServerAction)

            self.serverMenu.addSeparator()

            self.startServerAction = QtWidgets.QAction("&Listen for clients")
            self.startServerAction.setEnabled(False)
            self.serverMenu.addAction(self.startServerAction)

            self.stopServerAction = QtWidgets.QAction("&Stop listening")
            self.stopServerAction.setEnabled(False)
            self.serverMenu.addAction(self.stopServerAction)

        menuBar = self.menuBar()
        fileMenu()
        serverMenu()

    def print_status(self, message, timeout=10000):
        self.statusBar().showMessage(message, timeout)


class IndividualTabWidget(QtWidgets.QWidget):
    # self, columnIdx, rowIdx
    WidgetInsertRequest = QtCore.pyqtSignal(object, int, int)
    WidgetRemoveRequest = QtCore.pyqtSignal(object, int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        self.splitter = widgets.GridSplitterWidget()
        layout.addWidget(self.splitter, 0, 0)
        self.splitter.WidgetInsertRequest.connect(self._on_widget_insert_request)
        self.splitter.WidgetRemoveRequest.connect(self._on_widget_remove_request)
        self.splitter.ColumnInsertRequest.connect(self._on_column_insert_request)
        self.splitter.ColumnRemoveRequest.connect(self._on_column_remove_request)

    def insert_column(self, columnIdx):
        self.splitter.insert_column(columnIdx)

    def insert_widget(self, columnIdx, rowIdx, widget):
        self.splitter.insert_widget(columnIdx, rowIdx, widget)

    def remove_widget(self, columnIdx, rowIdx):
        return self.splitter.remove_widget(columnIdx, rowIdx)

    def get_widget(self, columnIdx, rowIdx):
        return self.splitter.widget(columnIdx, rowIdx)

    def _on_column_insert_request(self, columnIdx):
        self.splitter.insert_column(columnIdx)
        self.WidgetInsertRequest.emit(self, columnIdx, 0)

    def _on_column_remove_request(self, columnIdx):
        widget = self.splitter.remove_column(columnIdx)
        assert not widget.count()
        widget.deleteLater()

    def _on_widget_insert_request(self, columnIdx, rowIdx):
        self.WidgetInsertRequest.emit(self, columnIdx, rowIdx)

    def _on_widget_remove_request(self, columnIdx, rowIdx):
        self.WidgetRemoveRequest.emit(self, columnIdx, rowIdx)


class TabManagerWidget(QtWidgets.QTabWidget):
    # IndividualTabWidget, columnIdx, rowIdx
    WidgetInsertRequest = QtCore.pyqtSignal(object, int, int)
    WidgetRemoveRequest = QtCore.pyqtSignal(object, int, int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def addTab(self, *args, **kwargs):
        raise NotImplementedError("Use add_tab instead of addTab.")

    def add_tab(self, label, *args, **kwargs):
        return self.insert_tab(*args, idx=-1, label=label, **kwargs)

    def inserTab(self, *args, **kwargs):
        raise NotImplementedError("Use insert_tab instead of insertTab.")

    def insert_tab(self, idx: int, label: str, *args, **kwargs) -> IndividualTabWidget:
        widget = IndividualTabWidget(*args, **kwargs)
        widget.WidgetInsertRequest.connect(self.WidgetInsertRequest)
        widget.WidgetRemoveRequest.connect(self.WidgetRemoveRequest)
        super().insertTab(idx, widget, label)

        return widget
