import pytest
import os
import yaml

HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')
os.environ["CH_VALUES_PATH"] = os.path.join(HERE, "values.yaml")

from cloudharness.utils.env import *
from cloudharness.utils.config import CloudharnessConfig as conf

def set_test_environment():

    if not os.path.exists(os.path.join(HERE, 'values.yaml')):
        raise Exception(os.path.join(HERE, 'values.yaml'))
    with open(os.path.join(HERE, 'values.yaml')) as f:
        values = yaml.safe_load(f)
    from pprint import pprint

    pprint(values)
    conf.get_configuration().update(values)
    set_default_environment()


