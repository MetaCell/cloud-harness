# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "cloudharness_model"
VERSION = "1.0.0"
REQUIREMENTS = [l[0:-1].replace(" ", "") for l in open("requirements.txt") if "#" not in l]
print(REQUIREMENTS)
setup(name=NAME, version=VERSION, install_requires=REQUIREMENTS)