# coding: utf-8
from setuptools import setup, find_packages


NAME = "cloudharness"
VERSION = "0.1.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

def _get_requirements(requirement_file):
    with open(requirement_file) as f:
        reqs = []
        for l in f.read().splitlines():
            reqs.append(l)
        return reqs

REQUIREMENTS = _get_requirements("requirements.txt")

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
