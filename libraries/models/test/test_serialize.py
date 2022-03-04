
import yaml
from os.path import join, dirname as dn, realpath
from cloudharness_model import HarnessMainConfig, ApplicationConfig, User, ApplicationHarnessConfig
from cloudharness import json

HERE = dn(realpath(__file__))

def test_json_serialize():
    with open(join(HERE, "resources/values.yaml")) as f:
        values = yaml.load(f)
    v = HarnessMainConfig.from_dict(values)
    dumped = json.dumps(v)
    cloned = json.loads(dumped)
    assert v["name"] == cloned["name"]