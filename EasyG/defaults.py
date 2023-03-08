import yaml
from importlib import resources

with resources.path("EasyG", "defaults.yaml") as config_path:
    with open(config_path) as config_file:
        Config = yaml.safe_load(config_file)
