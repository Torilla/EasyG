import csv
from pathlib import Path
from scipy.misc import electrocardiogram
import numpy as np

from PyQt5.QtWidgets import QInputDialog


DEFAULTEXAMPLEPATH = Path.home() / "Projects/Python/EasyG/exampledata"


def getSciPyExample():
    y = electrocardiogram()
    # 5 Minute recording at 360Hz, we want millisecond timestamps
    x = np.linspace(start=0, stop=5 * 60 * 1000, num=5 * 60 * 360)

    return x, y


def load_csv_example(exampleName, sampleRateHz=250):
    x, y = [], []

    if not exampleName.endswith(".csv"):
        exampleName += ".csv"

    with open(DEFAULTEXAMPLEPATH / exampleName) as f:
        for line in csv.reader(f):
            assert len(line) == 1
            y.extend(line)

            # we want milliseconds, so multiply Hz (1/s) by 1000
            x.append(1000 / sampleRateHz * len(y))

    y = [float(_y) for _y in y]

    return x, y


NAMEDICT = {"SciPy": getSciPyExample,
            "HeartPy: e0103": lambda: load_csv_example("e0103"),
            "HeartPy: e0110": lambda: load_csv_example("e0110"),
            "HeartPy: e0124": lambda: load_csv_example("e0124")}


def openExample():
    exampleName, valid = QInputDialog.getItem(None, "Select Example Type",
                                              "List of Example Types",
                                              NAMEDICT, 0, False)

    if valid:
        x, y = NAMEDICT[exampleName]()

    else:
        x, y = None, None

    return x, y, exampleName
