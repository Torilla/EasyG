from PyQt5 import QtCore
from PyQt5 import QtWidgets

from EasyG.gui.plotmanager.plotmanagerwidget import PlotManagerWidget
from EasyG.ecg import exampleecg


class CentralWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def widgetFromTabName(self, tabName):
        widget = None

        for idx in range(self.count()):
            if self.tabText(idx) == tabName:
                widget = self.widget(idx)
                break

        return widget

    def _getUniqueTabName(self, defaultName):
        i = 0
        name = defaultName
        while self.widgetFromTabName(name) is not None:
            i += 1
            name = f"{defaultName} ({i})"

        return name

    @QtCore.pyqtSlot(str)
    def newMainPlotTab(self, tabName, x, y, plotName, plotterName="Main Plot"):
        widget = PlotManagerWidget()

        widget.insertColumn()
        plotWidget = widget.insertPlotWidget(title=plotName)

        widget.plot(0, 0, x=x, y=y, name=plotName)
        plotWidget.getAxis("bottom").setLabel(text="time / ms")
        plotWidget.getAxis("left").setLabel(text="Electrical potential / mV")

        tabName = self._getUniqueTabName(tabName)
        self.addTab(widget, tabName)

        return widget


class MainWindow(QtWidgets.QMainWindow):
    # tabName, tabOptions
    NewTabRequest = QtCore.pyqtSignal(str, dict)

    def __init__(self, size=QtCore.QSize(1024, 1280), *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.resize(size)

        centralWidget = CentralWidget()
        self.setCentralWidget(centralWidget)

        self._initMenuBar()

    def _initMenuBar(self):
        def fileMenu():
            self.fileMenu = menuBar.addMenu("&File")

            self.openMenu = self.fileMenu.addMenu("&Open")

            self.openFileAction = QtWidgets.QAction("&File")
            self.openMenu.addAction(self.openFileAction)

            self.openExampleAction = QtWidgets.QAction("&Example")
            self.openExampleAction.triggered.connect(self.openExample)
            self.openMenu.addAction(self.openExampleAction)

            self.fileMenu.addSeparator()

            self.exitAction = QtWidgets.QAction("&Exit")
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

    def openExample(self):
        x, y, exampleName = exampleecg.openExample()

        tabName = f"{exampleName} Example"
        tabOptions = {
            "x": x,
            "y": y,
            "plotName": tabName,
            "plotterName": "Main Plot"
        }

        self.centralWidget().newMainPlotTab(tabName=tabName, **tabOptions)
