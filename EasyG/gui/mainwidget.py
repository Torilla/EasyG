from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5.QtWidgets import QAction

from EasyG.gui.plotwidget import MainPlotWidget
from EasyG import exampleecg


class CentralWidget(QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def newMainPlotTab(self, tabName, widget=None):
        if widget is None:
            widget = MainPlotWidget()

        self.addTab(widget, tabName)

        return widget


class MainWindow(QMainWindow):
    def __init__(self, size=QSize(640, 480), *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(size)

        centralWidget = CentralWidget()
        self.setCentralWidget(centralWidget)

        self._initMenuBar()

    def _initMenuBar(self):
        def fileMenu():
            self.fileMenu = menuBar.addMenu("&File")

            self.openMenu = self.fileMenu.addMenu("&Open")

            self.openFileAction = QAction("&File")
            self.openMenu.addAction(self.openFileAction)

            self.openExampleAction = QAction("&Example")
            self.openExampleAction.triggered.connect(self.openExample)
            self.openMenu.addAction(self.openExampleAction)

            self.fileMenu.addSeparator()

            self.exitAction = QAction("&Exit")
            self.fileMenu.addAction(self.exitAction)

        def serverMenu():
            self.serverMenu = menuBar.addMenu("&Server")

            self.configureServerAction = QAction("&Configure")
            self.serverMenu.addAction(self.configureServerAction)

            self.serverMenu.addSeparator()

            self.startServerAction = QAction("&Listen for clients")
            self.startServerAction.setEnabled(False)
            self.serverMenu.addAction(self.startServerAction)

            self.stopServerAction = QAction("&Stop listening")
            self.stopServerAction.setEnabled(False)
            self.serverMenu.addAction(self.stopServerAction)

        menuBar = self.menuBar()
        fileMenu()
        serverMenu()

    def newMainPlotTab(self, **kwargs):
        return self.centralWidget().newMainPlotTab(**kwargs)

    def openExample(self):
        x, y = exampleecg.openExample()

        plotWidget = self.newMainPlotTab(tabName="SciPy Example")
        plotIdx = plotWidget.addPlot(plotterName="Main plot")
        plotWidget.newDataItem(x=x, y=y, plotterIdx=plotIdx,
                               name="SciPy Example")
