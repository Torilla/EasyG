from EasyG.datamanager import plotdataitemmanager, filesystem
from EasyG.gui import mainwindow
from EasyG.ecg import exampledata


class EasyG(object):
    def __init__(self, gui=mainwindow.MainWindow,
                 datamanager=plotdataitemmanager.PlotDataItemManager()):
        super().__init__()

        self.gui = gui()
        self.datamanager = datamanager
        self.gui.OpenExampleRequest.connect(self.onOpenExampleRequest)

    def onOpenExampleRequest(self):
        x, y, exampleName = exampledata.openExample()

        tabName = f"{exampleName} Example"
        tab = self.gui.centralWidget().addTab(tabName)

        path = f"/{tabName}"
        self.datamanager.registerDataObject(filesystem.DataObject((x, y)),
                                            path)

        for item in self.datamanager.getPlotItems(path):
            tab.plotManager.addItemToPlot(0, 0, item)
