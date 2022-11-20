from pathlib import Path
import pkgutil
from configparser import ConfigParser
import json

import PyQt5.QtWidgets
import PyQt5.QtGui
import PyQt5.QtCore
import PyQt5.QtNetwork

import pyqtgraph as pg

DEFAULTUSERCONFIGPATH = Path.home() / ".config/EasyG/easyg.ini"
ANALYZECONFIGPATH = "gui/plotmanager/datawidget/analyzewidget/analyzewidget.ini"


converters = {
    "HostAddress": PyQt5.QtNetwork.QHostAddress,
    "Geometry": lambda s: tuple(int(g) for g in s.split())
}


def writeConfigToFile(file, config):
    file = Path(file)

    file.parent.mkdir(exist_ok=True, parents=True)

    with file.open("w") as f:
        config.write(f)


def getConfig(configfile=DEFAULTUSERCONFIGPATH, section=None):
    config = ConfigParser(converters=converters)
    config.read(configfile)

    if section is not None:
        config = config[section]

    return config


_ANALYZECONFIG = None


def getAnalyzeWidgetConfig(configfile=ANALYZECONFIGPATH):
    def readConfig():
        converters = {"dict": json.loads,
                      "list": json.loads}

        global _ANALYZECONFIG
        _ANALYZECONFIG = ConfigParser(default_section=None,
                                      converters=converters)
        _ANALYZECONFIG.optionxform = str

        data = pkgutil.get_data(__name__, configfile).decode()
        _ANALYZECONFIG.read_string(data)
        _ANALYZECONFIG.file = configfile

    if _ANALYZECONFIG is None or _ANALYZECONFIG.file != configfile:
        readConfig()

    return _ANALYZECONFIG


def setPyqtgraphConfig(config=getConfig()):
    for k, v in config["plotting"].items():
        pg.setConfigOption(k, v)

    return config
