from pathlib import Path
from configparser import ConfigParser

from PyQt5.QtNetwork import QHostAddress

import pyqtgraph as pg

DEFAULTUSERCONFIGPATH = Path.home() / ".config/EasyG/easyg.ini"
converters = {
    "HostAddress": QHostAddress,
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


def setPyqtgraphConfig(config=getConfig()):
    for k, v in config["plotting"].items():
        pg.setConfigOption(k, v)

    return config
