from PyQt5 import QtCore, QtWidgets

from .centraltabwidget import TabManagerWidget


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
