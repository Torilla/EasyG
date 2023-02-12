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
        layout.addWidget(self.plotManager, 0, 0)

        self.plotManager.insertColumn(0)
        self.plotManager.insertPlotWidget(0, 0)


class TabManagerWidget(QtWidgets.QTabWidget):
    TabWidgetType = IndividualTabWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def addTab(self, label, *args, **kwargs):
        return self.insertTab(*args, idx=-1, label=label, **kwargs)

    def insertTab(self, idx, label, *args, **kwargs):
        widget = self.TabWidgetType(*args, **kwargs)
        super().insertTab(idx, widget, label)

        return widget

    def updateDockWidgetConfig(self, config):
        for idx in range(self.count()):
            _config = config.copy()
            tab = self.widget(idx)
            ownedItems = _config.pop(tab.tabText())

            tab.dockWidget.setConfiguration(ownedItems, _config)
