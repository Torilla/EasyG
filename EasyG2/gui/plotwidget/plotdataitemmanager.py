from collections import defaultdict


class PlotItemManager(object):
    _availableDataPaths = []
    
    def __init__(self):
        # Dictionary {DataManagerID: [PlotItems,...]}
        self._plotItems = defaultdict(list)

    def registerPlotItem(self, id, item):
