import heartpy as hp


def heartPyProcess(x, y, processOpts):
    def correctSpelling():
        for m in dict(measures):
            if m == "breathingrate":
                _m = "Breathingrate"

            else:
                _m = m.upper()

            measures[_m] = f"{measures.pop(m):.3f}"

    def getPeakLists():
        x_accepted, x_rejected = [], []
        y_accepted, y_rejected = [], []

        for idx, xIdx in enumerate(data["peaklist"]):
            if data["binary_peaklist"][idx]:
                x_accepted.append(x[xIdx])
                y_accepted.append(y[xIdx])

            else:
                x_rejected.append(x[xIdx])
                y_rejected.append(y[xIdx])

        return (x_accepted, y_accepted), (x_rejected, y_rejected)

    data, measures = hp.process(y, **processOpts)

    correctSpelling()
    accepted_peaks, rejected_peaks = getPeakLists()

    resultDict = {"accepted_peaks": accepted_peaks,
                  "rejected_peaks": rejected_peaks}

    return measures, resultDict


PROCESSORDICT = {"HeartPy.process": heartPyProcess}


def getProcessor(name):
    return PROCESSORDICT[name]


def filterSignal(*args, **kwargs):
    return hp.filter_signal(*args, **kwargs)
