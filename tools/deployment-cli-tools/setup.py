# coding: utf-8

"""
    CloudHarness deploy

    OpenAPI spec version: 0.6.5
    Contact: cloudharness@metacell.us
"""


from setuptools import setup, find_packages


NAME = "cloudharness-cli-tools"
VERSION = "2.0.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIREMENTS = [
    'ruamel.yaml',
    'oyaml',
    'docker',
    'six',
    'cloudharness_model',
    'cloudharness_utils',
    'fastapi-code-generator'
]



setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness deploy and code generation tools",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["Cloud", "Kubernetes", "Helm", "Deploy"],
    install_requires=REQUIREMENTS,
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    scripts=['harness-deployment', 'harness-generate', 'harness-application'],
    long_description="""\
    CloudHarness deploy library
    """
)
