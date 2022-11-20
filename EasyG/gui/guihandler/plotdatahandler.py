class PlotDataHandler(object):
    def __init__(self, plotMangerWidget, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plotManger = plotMangerWidget

    def _onProcessButtonPressed(self, dataOptions, processOptions):
        start, stop = dataOptions["data bounds"]
        x, y = self.plotManager.getGlobalPlotItem(
            dataOptions["data source"]).getData()

        if start is not None:
            start = next(idx for idx, v in enumerate(x) if v >= start)

        if stop is not None:
            stop = next(idx for idx, v in enumerate(x) if v >= stop)

        x, y = x[start:stop], y[start:stop]

        self._analysisWorker.StartProcessing.emit(
            processOptions.pop("processor"),        # target Process
            (y,),                                   # Process Args
            processOptions,                         # Process Kwargs
            dataOptions)                            # meta Info for results
