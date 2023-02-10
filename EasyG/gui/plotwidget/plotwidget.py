from PyQt5 import QtWidgets

import pyqtgraph as pg

from .splitter import GridSplitterWidget


class PlotManagerWidget(QtWidgets.QWidget):
    plotWidgetType = pg.PlotWidget

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        self.splitterWidget = GridSplitterWidget()
        layout.addWidget(self.splitterWidget, 1)

    def insertColumn(self, columnIdx):
        self.splitterWidget.insertColumn(columnIdx)

    def insertPlotWidget(self, columnIdx, rowIdx, *args, **kwargs):
        widget = self.plotWidgetType(*args, **kwargs)

        self.splitterWidget.insertWidget(columnIdx, rowIdx, widget)

    def addItemToPlot(self, columnIdx, rowIdx, item, *args, **kwargs):
        self.splitterWidget.widget(columnIdx, rowIdx).addItem(item, *args, **kwargs)
