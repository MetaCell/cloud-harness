from cloudharness.utils.config import CloudharnessConfig as conf
from cloudharness.utils.env import set_default_environment
import pytest
import os
import yaml

HERE = os.path.dirname(os.path.realpath(__file__))
os.environ["CH_VALUES_PATH"] = os.path.join(HERE, "values.yaml")


def set_test_environment():

    values_file = os.environ["CH_VALUES_PATH"]
    if not os.path.exists(values_file):

        raise Exception("Test values file not found: " + values_file)
    with open(values_file) as f:
        values = yaml.safe_load(f)
    from pprint import pprint

    pprint(values)
    conf.get_configuration().update(values)
    set_default_environment()
