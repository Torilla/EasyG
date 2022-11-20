from PyQt5 import QtCore, QtWidgets


class GUIHandler(QtCore.QObject):
    def __init__(self, gui, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.gui = gui

        # connect the gui
        self.gui.NewTabRequest.connect(self._onNewTab)

        # set up the worker thread for data analysis and processing
        self._threadPool = QtCore.QThreadPool.globalInstance()

    @QtCore.pyqtSlot(str, dict)
    def _onNewTab(self, tabName, tabOptions):
        widget = self.gui.newMainTab(tabName=tabName, **tabOptions)

        print(widget.ProcessButtonPressed.connect(self.onProcessButtonPressed))
#        widget.FilterButtonPressed.connect(self.onFilterButtonPressed)
#        widget.DataManipulationButtonPressed.connect(
#            self.onDataManipulationButtonPressed)

    @QtCore.pyqtSlot(str, object, object)
    def _onProcessingFinished(self, methodName, results, metaInfo):
        getattr(self, f"_on{methodName}Results")(results, metaInfo)

    @QtCore.pyqtSlot(str, Exception)
    def _onProcessingFailed(self, methodName, err):
        QtWidgets.QMessageBox.warning(self.gui,
                                      "Processing failed!",
                                      "Data processing failed for "
                                      f"{methodName}: {err}",
                                      QtWidgets.QMessageBox.Ok)

    @QtCore.pyqtSlot(dict, dict)
    def onProcessButtonPressed(self, dataOptions, processOptions):
        start, stop = dataOptions["data bounds"]
        plotManager = self.gui.centralWidget().currentWidget()
        x, y = plotManager.getGlobalPlotItem(
            dataOptions["data source"]).getData()

        if start is not None:
            start = next(idx for idx, v in enumerate(x) if v >= start)

        if stop is not None:
            stop = next(idx for idx, v in enumerate(x) if v >= stop)

        x, y = x[start:stop], y[start:stop]

        dataOptions["plot manager"] = plotManager

        self._analysisWorker.StartProcessing.emit(
            processOptions.pop("processor"),        # target Process
            (y,),                                   # Process Args
            processOptions,                         # Process Kwargs
            dataOptions)                            # meta Info for results

    def _onHeartPyProcessResults(self, results, metaInfo):
        plotManager = metaInfo["plot manager"]
        data, results = results
        plotWidget = plotManager.plotWidgetFromTitle(metaInfo["data target"])
        colIdx, rowIdx = plotManager.indexOfPlotWidget(plotWidget)

        itemName = metaInfo["data source"]
        if not plotWidget.containsItemWithName(itemName):
            plotItem = plotManager.getGlobalPlotItem(itemName).copy()
            plotManager.addPlotItem(colIdx, rowIdx, plotItem)
            x, y = plotItem.getData()

        else:
            x, y = plotWidget.itemFromName(itemName).getData()

        acceptedPeaks, recjectedPeaks = [], []
        xAccepted, xRejected = [], []

        for idx, isPeak in zip(data["peaklist"], data["binary_peaklist"]):
            _x = x[idx]
            _y = y[idx]
            if isPeak:
                xAccepted.append(_x)
                acceptedPeaks.append(_y)
            else:
                xRejected.append(_x)
                recjectedPeaks.append(_y)

        plotManager.plot(colIdx, rowIdx, x=xAccepted, y=acceptedPeaks,
                         name=f"{itemName} (accepted Peaks)", pen=None,
                         symbol="o", symbolBrush="g")

        plotManager.plot(colIdx, rowIdx, x=xRejected, y=recjectedPeaks,
                         name=f"{itemName} (rejected Peaks)", pen=None,
                         symbol="x", symbolBrush="r")

    @QtCore.pyqtSlot(object, dict, dict)
    def onFilterButtonPressed(self, plotManager, dataOptions, filterOptions):
        x, y = plotManager.getGlobalPlotItem(
            dataOptions["data source"]).getData()

        start, stop = dataOptions["data bounds"]

        if start is not None:
            start = next(idx for idx, v in enumerate(x) if v >= start)

        if stop is not None:
            stop = next(idx for idx, v in enumerate(x) if v >= stop)

        x, y = x[start:stop], y[start:stop]

        dataOptions["plot manager"] = plotManager

        self._analysisWorker.StartProcessing.emit(
            "HeartPyFilter",    # target Process
            (y, ),              # Process Args
            filterOptions,      # Process Kwargs
            dataOptions)        # meta Info

    def _onHeartPyFilterResults(self, results, metaInfo):
        plotManager = metaInfo["plot manager"]
        plotWidget = plotManager.plotWidgetFromTitle(metaInfo["data target"])
        colIdx, rowIdx = plotManager.indexOfPlotWidget(plotWidget)
        itemName = metaInfo["data source"]
        if plotWidget.containsItemWithName(itemName):
            x, _ = plotWidget.itemFromName(itemName).getData()

        else:
            x, _ = plotManager.getGlobalPlotItem(itemName).getData()

        plotManager.plot(colIdx, rowIdx, x=x, y=results,
                         pen=metaInfo["target color"],
                         name=f"{metaInfo['target name']} (filter)")

    def onDataManipulationButtonPressed(self, plotManager, dataOptions,
                                        manipulationOptions):
        x, y = plotManager.getGlobalPlotItem(
            dataOptions["data source"]).getData()

        if manipulationOptions.pop("factor"):
            manipulationOptions["num"] = len(x) * manipulationOptions["num"]

        start, stop = dataOptions["data bounds"]

        if start is not None:
            start = next(idx for idx, v in enumerate(x) if v >= start)

        if stop is not None:
            stop = next(idx for idx, v in enumerate(x) if v >= stop)

        x, y = x[start:stop], y[start:stop]

        dataOptions["plot manager"] = plotManager

        self._analysisWorker.StartProcessing.emit(
            manipulationOptions.pop("manipulation method"),  # target Process
            (x, y),                                          # Process Args
            manipulationOptions,                             # Process Kwargs
            dataOptions)                                     # meta Info

    def _onResampleResults(self, results, metaInfo):
        plotManager = metaInfo["plot manager"]
        plotWidget = plotManager.plotWidgetFromTitle(metaInfo["data target"])
        colIdx, rowIdx = plotManager.indexOfPlotWidget(plotWidget)

        x, y = results
        plotManager.plot(colIdx, rowIdx, x=x, y=y,
                         pen=metaInfo["target color"],
                         name=f"{metaInfo['target name']} (resampled)")
