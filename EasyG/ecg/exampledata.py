from importlib import resources
import csv
from scipy.misc import electrocardiogram
import numpy as np

from PyQt5.QtWidgets import QInputDialog

from EasyG import defaults


def discover_examples():
    examples = {}

    # get builtin examples:
    cfg = defaults.Config["Examples"]["builtin"]

    # get file examples
    for rname, rpatterns in cfg["resources"]:
        path = resources.as_file(f"EasyG.resources.{rname}")
        for pattern in rpatterns:
            examples.extend(list(path.glob(pattern)))

    #

    return


def getSciPyExample():
    y = electrocardiogram()
    # 5 Minute recording at 360Hz, we want millisecond timestamps
    x = np.linspace(start=0, stop=5 * 60 * 1000, num=5 * 60 * 360)

    return x, y


def load_csv_example(fn, sampleRateHz=250):
    x, y = [], []

    with open(fn) as f:
        for line in csv.reader(f):
            assert len(line) == 1
            y.extend(line)

            # we want milliseconds, so multiply Hz (1/s) by 1000
            x.append(1000 / sampleRateHz * len(y))

    y = [float(_y) for _y in y]

    return x, y


def openExample():
    if not DynamicExamples:
        discover_examples()

    exampleName, valid = QInputDialog.getItem(
        None, "Select Example Type", "List of Example Types",
        list(DynamicExamples) + list(BuiltinExamples), 0, False)

    if valid:
        if exampleName in BuiltinExamples:
            x, y = BuiltinExamples[exampleName]()

        else:
            x, y = load_csv_example(DynamicExamples[exampleName])

    else:
        x, y = None, None

    return x, y, exampleName


DynamicExamples = {}
BuiltinExamples = {"SciPy": getSciPyExample}
