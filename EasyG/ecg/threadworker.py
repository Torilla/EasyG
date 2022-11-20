from PyQt5 import QtCore


class ProxyECGWorkerSignals(QtCore.QObject):
    WorkerFinished = QtCore.pyqtSignal(object)
    WorkerFailed = QtCore.pyqtSignal(Exception)


class ECGWorker(QtCore.QRunnable):
    _Signals = ProxyECGWorkerSignals()

    def __init__(self, fn, fnArgs, fnKwargs):
        self.fn = fn
        self.fnArgs = fnArgs
        self.fnKwargs = fnKwargs

    def __getattr__(self, attr):
        # defer signal lookup to the ProxySignal class
        return getattr(self._Signals, attr)

    def run(self):
        try:
            result = self.fn(*self.fnArgs, **self.fnKwargs)

        except Exception as err:
            self.WorkerFailed.emit(err)

        else:
            self.WorkerFinished.emit(result)
