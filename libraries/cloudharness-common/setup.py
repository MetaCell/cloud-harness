# coding: utf-8
from setuptools import setup, find_packages


NAME = "cloudharness"
VERSION = "2.0.0"
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
    'pyjwt>=2.6.0',
    'cryptography',
    'requests>=2.21.0',
    'sentry-sdk[flask]>=0.14.4',
    'python-keycloak',
    'cloudharness_model',
    'argo-workflows==5.0.0',
    'cachetools'
]



setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness common runtime library",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["cloudharness", "cloud"],
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    package_data={'': ['*.yaml']},
    long_description="""\
    Cloudharness common library
    """
)
