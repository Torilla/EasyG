from PyQt5 import QtWidgets

import pyqtgraph as pg

from .splitter import GridSplitterWidget


class PlotManagerWidget(QtWidgets.QWidget):
    plotWidgetType = pg.PlotWidget

    __initalized = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.splitterWidget = GridSplitterWidget()
        layout.addWidget(self.splitterWidget, 1)

    def init(self):
        if self.__initalized:
            return

        self.__initalized = True
        self.insertColumn(0)
        return self.insertPlotWidget(0, 0)

    def insertColumn(self, *args, **kwargs):
        return self.splitterWidget.insertColumn(*args, **kwargs)

    def insertPlotWidget(self, columnIdx, rowIdx, *args, **kwargs):
        widget = self.plotWidgetType(*args, **kwargs)

        self.splitterWidget.insertWidget(columnIdx, rowIdx, widget)

        return widget
