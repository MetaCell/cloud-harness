# coding: utf-8

import sys
from setuptools import setup, find_packages
from os.path import join, dirname as dn, realpath


HERE = dn(realpath(__file__))

NAME = "cloudharness_model"
VERSION = "1.0.0"
REQUIREMENTS = [
    "swagger-ui-bundle >= 0.0.2",
    "python_dateutil >= 2.6.0",
    "setuptools >= 21.0.0",
    "pyhumps",
    "oyaml"
]
print(REQUIREMENTS)
setup(name=NAME, version=VERSION, install_requires=REQUIREMENTS)
