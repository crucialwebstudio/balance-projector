import os
import yaml
import pprint


class FixtureHelper:
    def __init__(self):
        pass

    @classmethod
    def get_yaml(cls, filename):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        with open(f"{dir_path}/fixtures/{filename}", "r") as stream:
            return yaml.safe_load(stream)


class DebugHelper:
    def __init__(self):
        pass

    @classmethod
    def pprint(cls, msg):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(msg)
