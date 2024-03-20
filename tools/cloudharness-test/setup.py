# coding: utf-8

"""
    CloudHarness deploy

    OpenAPI spec version: 0.6.5
    Contact: cloudharness@metacell.us
"""


from setuptools import setup, find_packages


NAME = "cloudharness-test"
VERSION = "2.3.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIREMENTS = [
    'requests',
    'cloudharness_model',
    'cloudharness',
    'schemathesis',
]



setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness testing cli tool",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["Cloud", "Kubernetes", "Helm", "Deploy"],
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    scripts=['harness-test'],
    long_description="""\
    CloudHarness test library
    """
)
