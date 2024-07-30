# coding: utf-8

import sys
from setuptools import setup, find_packages
from os.path import join, dirname as dn, realpath


HERE = dn(realpath(__file__))

NAME = "cloudharness_model"
VERSION = "2.3.0"
REQUIREMENTS = [
    "Jinja2 >= 3.1.3",
    "oyaml >= 1.0",
    "psutil >= 5.9.4",
    "pyhumps >= 3.8.0",
    "python-dateutil >= 2.8.2",
    "PyYAML >= 6.0.1",
    "six >= 1.16.0",
    "swagger_ui_bundle >= 1.1.0",
]
print(REQUIREMENTS)
setup(name=NAME, version=VERSION,
      install_requires=REQUIREMENTS, packages=find_packages(),)
