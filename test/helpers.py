import os
import yaml
import pprint


def get_root_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


class FixtureHelper:
    def __init__(self):
        pass

    @classmethod
    def get_spec_fixture(cls):
        root_path = get_root_path()
        with open(f"{root_path}/balance-projector.dist.yml", "r") as stream:
            return yaml.safe_load(stream)


class DebugHelper:
    def __init__(self):
        pass

    @classmethod
    def pprint(cls, msg):
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(msg)
