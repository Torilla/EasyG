from PyQt5 import QtWidgets

from .plotwidget.plotwidget import PlotManagerWidget


class IndividualTabWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

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
        widget = self.TabWidgetType(*args, **kwargs)
        super().addTab(widget, label)

        return widget

    def insertTab(self, idx, label, *args, **kwargs):
        widget = self.TabWidgetType(*args, **kwargs)
        super().insertTab(idx=idx, widget=widget,
                          label=label)

        return widget
