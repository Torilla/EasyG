import yaml
from importlib import resources

with resources.path("EasyG.ressources", "defaults.yaml") as path:
    with open(path) as file:
        Config = yaml.safe_load(file)

