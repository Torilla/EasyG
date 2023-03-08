from PyQt5 import QtWidgets

from .plotwidget.plotwidget import PlotManagerWidget


class IndividualTabWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        self.plotManager = PlotManagerWidget()
        layout.addWidget(self.plotManager, 0, 0)

    def insertColumn(self, *args, **kwargs):
        self.plotManager.insertColumn(*args, **kwargs)

    def insertPlotWidget(self, *args, **kwargs):
        self.plotManager.insertPlotWidget(*args, **kwargs)

    def addItemToPlot(self, *args, **kwargs):
        self.plotManager.addItemToPlot(*args, **kwargs)


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
