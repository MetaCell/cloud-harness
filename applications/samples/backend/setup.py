# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "samples"
VERSION = "2.4.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion[swagger-ui,flask,uvicorn]>=3.0.0,<4.0.0",
    "Flask",
    "python_dateutil",
    "pyjwt",
    "swagger-ui-bundle",
    "cloudharness",

]

setup(
    name=NAME,
    version=VERSION,
    description="CloudHarness Sample API",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["OpenAPI", "CloudHarness Sample API"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['samples=samples.__main__:main']},
    long_description="""\
    CloudHarness Sample api
    """
)
