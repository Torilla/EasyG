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
            self.openExampleAction.triggered.connect(
                self.OpenExampleRequest.emit)
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        self.splitter = widgets.GridSplitterWidget()
        layout.addWidget(self.splitter, 0, 0)

        self.dataWidgetManager = widgets.DataWidgetManager()
        layout.addWidget(self.dataWidgetManager, 1, 0)

    def insert_column(self, columnIdx):
        self.splitter.insertColumn(columnIdx)

    def insert_widget(self, columnIdx, rowIdx, widget):
        self.splitter.insertWidget(columnIdx, rowIdx, widget)


class TabManagerWidget(QtWidgets.QTabWidget):
    _TabWidgetType = IndividualTabWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def addTab(self, label, *args, **kwargs):
        return self.insertTab(*args, idx=-1, label=label, **kwargs)

    def insertTab(
        self, idx: int, label: str, *args, **kwargs
    ) -> IndividualTabWidget:
        widget = self._TabWidgetType(*args, **kwargs)
        super().insertTab(idx, widget, label)

        return widget
