# coding: utf-8

"""
    CloudHarness utils

    Contact: cloudharness@metacell.us
"""


from setuptools import setup, find_packages


NAME = "cloudharness_utils"
VERSION = "2.4.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIREMENTS = [
    'ruamel.yaml',
    'cloudharness_model',
    'docker'
]


setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness utils and constants",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["Cloud", "Kubernetes", "Helm", "Deploy"],
    install_requires=REQUIREMENTS,
    packages=find_packages(
        exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    long_description="""\
    CloudHarness utils library
    """
)
