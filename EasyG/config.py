from importlib import resources
import configparser


DEFAULT_CONFIG = {
    "Examples": {
        "path_context_manager": resources.path("EasyG.ressources", "examples")
    }
}


Config = configparser.ConfigParser(defaults=DEFAULT_CONFIG)
