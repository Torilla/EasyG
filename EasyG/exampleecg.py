from scipy.misc import electrocardiogram

from PyQt5.QtWidgets import QInputDialog


def getSciPyExample():
    y = electrocardiogram()
    x = list(range(len(y)))

    return x, y


NAMEDICT = {"SciPy": getSciPyExample}


def openExample():
    example, valid = QInputDialog.getItem(None, "Select Example Type",
                                          "List of Example Types",
                                          NAMEDICT, 0, False)

    if valid:
        x, y = NAMEDICT[example]()

    else:
        x, y = None, None

    return x, y
