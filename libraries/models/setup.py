# coding: utf-8

import sys
from setuptools import setup, find_packages
from os.path import join, dirname as dn, realpath


HERE = dn(realpath(__file__))

NAME = "cloudharness_model"
VERSION = "3.0.0"
REQUIREMENTS = [
    "pydantic >= 2",
    "typing-extensions >= 4.7.1",
    "pyhumps >= 3.8.0"
]

setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness model definitions",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["CloudHarness", "models", "pydantic"],
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={'cloudharness_model': ['py.typed']},
    long_description="""\
    CloudHarness model library - Pure model definitions and utilities
    """,
    python_requires=">=3.7",
)
