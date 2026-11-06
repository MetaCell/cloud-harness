# coding: utf-8
from setuptools import setup, find_packages


NAME = "cloudharness"
VERSION = "3.0.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIREMENTS = [
    'PyYAML >= 6.0.1',
    'pyjwt[crypto] >= 2.6.0',
    'requests >= 2.31.0',
    'sentry-sdk >= 1.39.2',
    'cloudharness_model',
]


setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness common runtime library (Microsoft Entra edition)",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["cloudharness", "cloud", "entra"],
    install_requires=REQUIREMENTS,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={'': ['*.yaml']},
    long_description="""\
    Cloudharness common library
    """
)
