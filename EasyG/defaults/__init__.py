import yaml
from importlib import resources


class InvalidConfigurationFile(yaml.scanner.ScannerError):

    """Raised when loading a configuration file failes"""


Config_T = dict[str, str | dict | list]


def parse_default_configurations():
    Config = Config_T()

    with resources.path("EasyG", "defaults") as path:
        for file in path.rglob("*.y*ml"):
            with open(file) as f:
                errmsg = None
                try:
                    cfg = yaml.safe_load(f)
                except yaml.scanner.ScannerError as err:
                    errmsg = f"Failed to parse configuration file:\n{file}\n{err}"

                if len(cfg) > 1:
                    errmsg = f"{file}\nExpected single key, found {list(cfg)}"

                elif not isinstance(cfg, dict):
                    errmsg = f"{file}:\nExpected mapping, found {type(cfg)}"

                if errmsg is not None:
                    raise InvalidConfigurationFile(errmsg)

                del errmsg
                name, cfg = next(iter(cfg.items()))
                Config[name] = cfg

    return Config


Config = parse_default_configurations()
