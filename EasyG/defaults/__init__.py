import yaml
from importlib import resources


class InvalidConfigurationFile(yaml.scanner.ScannerError):

    """Raised when load a config file failes"""


Config = {}

with resources.path("EasyG", "defaults") as path:
    for file in path.rglob("*.y*ml"):
        with open(file) as f:
            try:
                cfg = yaml.safe_load(f)
            except yaml.scanner.ScannerError as err:
                msg = f"Failed to load configuration file!\n{err}"
                raise InvalidConfigurationFile(msg) from None

            if len(cfg.items()) > 1:
                msg = f"{file}\nExpected single key, found {list(cfg.keys())}"
                raise InvalidConfigurationFile(msg)

            name, cfg = next(iter(cfg.items()))
            Config[name] = cfg
