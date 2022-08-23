import heartpy as hp


def process(*args, **kwargs):
    data, measures = hp.process(*args, **kwargs)

    for m in dict(measures):
        if m == "breathingrate":
            _m = "Breathingrate"

        else:
            _m = m.upper()

        measures[_m] = f"{measures.pop(m):.3f}"

    return data, measures


PROCESSORDICT = {"HeartPy.process": process}


def getProcessor(name):
    return PROCESSORDICT[name]


def filterSignal(*args, **kwargs):
    return hp.filter_signal(*args, **kwargs)
