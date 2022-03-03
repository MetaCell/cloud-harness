import pytest
from os.path import join, dirname as dn, realpath
import yaml

from cloudharness_model import HarnessMainConfig

HERE = dn(realpath(__file__))

def test_helm_values_deserialize():
    with open(join(HERE, "resources/values.yaml")) as f:
        values = yaml.load(f)
    v = HarnessMainConfig.from_dict(values)

    assert v.domain
    assert v.apps["accounts"].harness.deployment.name == "accounts"
