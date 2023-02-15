from collections import defaultdict

from PyQt5 import QtWidgets

from .plotwidget.plotwidget import PlotManagerWidget
from EasyG.gui.widgets import PlotDataItemAndPlotterListWidget


class IndividualTabWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        self.dockWidget = PlotDataItemAndPlotterListWidget()

        self.plotManager = PlotManagerWidget()
        self.plotManager.TitleChanged.connect(self.dockWidget.updateBoxTitle)
        layout.addWidget(self.plotManager, 0, 0)

    def insertColumn(self, *args, **kwargs):
        self.plotManager.insertColumn(*args, **kwargs)

    def insertPlotWidget(self, *args, **kwargs):
        self.plotManager.insertPlotWidget(*args, **kwargs)

    def addItemToPlot(self, *args, **kwargs):
        self.plotManager.addItemToPlot(*args, **kwargs)

    def updateDockWidgetConfig(self, ownedItems, forreignItems):
        curentConfig = self.plotManager.getCurrentPlotConfiguration()

        # sort owned items in currently plotted (active) and _inactive items
        config = defaultdict(list)

        for item in ownedItems:
            for plot, activeItems in curentConfig.items():
                if item in activeItems:
                    config[plot].append(item)
                else:
                    config["_inactive"].append(item)

        self.dockWidget.setConfiguration(config, forreignItems)


class TabManagerWidget(QtWidgets.QTabWidget):
    _TabWidgetType = IndividualTabWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.currentChanged.connect(self._onCurrentChanged)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def _onCurrentChanged(self, idx):
        self.currentWidget().dockWidget.raise_()

    def addTab(self, label, *args, **kwargs):
        return self.insertTab(*args, idx=-1, label=label, **kwargs)

    def insertTab(self, idx, label, *args, **kwargs):
        widget = self._TabWidgetType(*args, **kwargs)
        super().insertTab(idx, widget, label)

        return widget

    def updateDockWidgetConfig(self, config):
        for idx in range(self.count()):
            _config = config.copy()
            ownedItems = _config.pop(self.tabText(idx))

            self.widget(idx).updateDockWidgetConfig(ownedItems, _config)
