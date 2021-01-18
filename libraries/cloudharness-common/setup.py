# coding: utf-8
from setuptools import setup, find_packages


NAME = "cloudharness"
VERSION = "0.2.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIREMENTS = [
    'kubernetes',
    'kafka-python',
    'pyaml',
    'jwt',
    'pyjwt>=1.7.1',
    'requests>=2.21.0',
    'sentry-sdk[flask]>=0.14.4',
    'python-keycloak==0.23.0',
    'argo-workflows'
]



setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness common library",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["cloudharness", "cloud"],
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    long_description="""\
    Cloudharness common library
    """
)
