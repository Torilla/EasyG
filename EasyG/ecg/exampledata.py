import importlib
import csv
from scipy.misc import electrocardiogram
import numpy as np

from PyQt5.QtWidgets import QInputDialog

from EasyG import defaults


def discover_examples():
    # get builtin examples
    cfg = defaults.Config["Examples"]["builtin"]
    examples = {}

    for path, file_patterns in cfg["files"].items():
        for file_pattern in file_patterns:
            with importlib.resources.path(path, file_pattern) as path:
                examples["files"] = list(path.parent.glob(path.name))

    methdict = examples["methods"] = {}
    for module, methods in cfg["modules"].items():
        module = importlib.import_module(module)
        for name, method in methods.items():
            methdict[name.replace("_", " ")] = getattr(module, method)

    return examples


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
            y.append(float(line[0]))

            # we want milliseconds, so multiply Hz (1/s) by 1000
            x.append(1000 / sampleRateHz * len(y))

    return x, y


def openExample():
    methods, files = Examples["methods"], Examples["files"]

    exampleName, valid = QInputDialog.getItem(
        None,
        "Select Example Type",
        "List of Example Types",
        list(methods) + [f.name for f in files],
        0,
        False,
    )

    if valid:
        if exampleName in methods:
            x, y = methods[exampleName]()

        else:
            for f in files:
                if f.name == exampleName:
                    x, y = load_csv_example(f)
                    break
            else:
                raise AssertionError(f"Example data not found!: {f}")

    else:
        x, y = None, None

    return x, y, exampleName


Examples = discover_examples()
