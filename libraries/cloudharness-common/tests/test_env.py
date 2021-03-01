import pytest
import os
import yaml
from cloudharness.utils.env import *
from cloudharness.utils.config import CloudharnessConfig as conf
HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')

def set_test_environment():
    with open(os.path.join(HERE, 'values.yaml')) as f:
        values = yaml.safe_load(f)
    conf.get_configuration().update(values)
    set_default_environment()


