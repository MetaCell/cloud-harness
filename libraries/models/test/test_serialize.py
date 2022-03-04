
import json
from os.path import join, dirname as dn, realpath

import yaml

from cloudharness_model import HarnessMainConfig, ApplicationConfig, User, ApplicationHarnessConfig
from cloudharness_model.encoder import CloudHarnessJSONEncoder

HERE = dn(realpath(__file__))

def test_json_serialize():
    with open(join(HERE, "resources/values.yaml")) as f:
        values = yaml.safe_load(f)
    v = HarnessMainConfig.from_dict(values)
    dumped = json.dumps(v, cls=CloudHarnessJSONEncoder)
    cloned = json.loads(dumped)
    assert v["name"] == cloned["name"]

    values["apps"]["accounts"]["harness"] = ApplicationHarnessConfig(name="accounts2")
    v = HarnessMainConfig.from_dict(values)
    assert v["apps"]["accounts"]["harness"]["name"] == "accounts2"
    dumped = json.dumps(v, cls=CloudHarnessJSONEncoder)
    cloned = json.loads(dumped)
    assert v["name"] == cloned["name"]
    assert cloned["apps"]["accounts"]["harness"]["name"] == "accounts2"