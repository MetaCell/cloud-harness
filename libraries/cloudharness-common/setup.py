# coding: utf-8
from setuptools import setup, find_packages


NAME = "cloudharness"
VERSION = "2.3.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIREMENTS = [
    'kubernetes >= 29.0.0',
    'PyYAML >= 6.0.1',
    'oyaml >= 1.0',
    'pyjwt>=2.6.0',
    'cryptography',
    'requests>=2.21.0',
    'sentry-sdk[flask]>=0.14.4',
    'python-keycloak >= 3.7.0',
    'cloudharness_model',
    'argo-workflows==5.0.0',
    'cachetools >= 5.3.2',
    'blinker >= 1.7.0',
    'jinja2 >= 3.1.4',
    'kafka-python >= 2.0.2',
    'requests >= 2.31.0',
    'python-dateutil >= 2.8.2',
    'sentry-sdk >= 1.39.2',
]


setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness common runtime library",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["cloudharness", "cloud"],
    install_requires=REQUIREMENTS,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={'': ['*.yaml']},
    long_description="""\
    Cloudharness common library
    """
)
