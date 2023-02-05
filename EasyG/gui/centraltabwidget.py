from PyQt5 import QtWidgets

from .plotwidget.plotwidget import PlotManagerWidget


class CentralTabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)

    def addNewPlotManager(self, *args, **kwargs):
        widget = PlotManagerWidget()
        super().addTab(widget, *args, **kwargs)

        return widget

    def insertNewPlotManager(self, *args, **kwargs):
        widget = PlotManagerWidget()
        super().insertTab(widget, *args, **kwargs)

        return widget

    def addTab(self, *args, **kwargs):
        raise NotImplementedError("Can't add widgets directly! "
                                  "Use addNewPlotManager to add new Tabs!")

    def insertTab(self, *args, **kwargs):
        raise NotImplementedError("Can't insert widgets directly! "
                                  "Use insertNewPlotManager to insert new Tabs!")
