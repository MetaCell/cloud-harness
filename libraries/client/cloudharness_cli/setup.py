# coding: utf-8

"""
    CloudHarness Sample API

    CloudHarness Sample api  # noqa: E501

    The version of the OpenAPI document: 0.1.0
    Contact: cloudharness@metacell.us
    Generated by: https://openapi-generator.tech
"""


from setuptools import setup, find_packages  # noqa: H301

NAME = "cloudharness-cli"
VERSION = "0.4.0"
# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = ["urllib3 >= 1.15", "six >= 1.10", "certifi", "python-dateutil"]

setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness Python API Client",
    author="OpenAPI Generator community",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["OpenAPI", "CloudHarness Sample API"],
    install_requires=REQUIRES,
    packages=find_packages(exclude=["test", "tests"]),
    include_package_data=True,
    license="UNLICENSED",
    long_description="""\
    CloudHarness Python API Client  # noqa: E501
    """,
    python_requires='>=3.10, <=3.10'

)
