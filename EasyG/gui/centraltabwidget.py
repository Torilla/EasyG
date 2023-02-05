from PyQt5 import QtWidgets

from .plotwidget.plotwidget import PlotManagerWidget


class IndividualTabWidget(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QGridLayout()
        self.setLayout(layout)

        self.plotManger = PlotManagerWidget()
        layout.addWidget(self.plotManger, 0, 0)


class TabManagerWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def addTab(self, label, *args, **kwargs):
        super().addTab(widget=IndividualTabWidget(*args, **kwargs), label=label)

    def insertTab(self, idx, label, *args, **kwargs):
        super().insertTab(idx=idx, widget=IndividualTabWidget(*args, **kwargs),
                          label=label)
