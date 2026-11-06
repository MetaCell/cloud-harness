# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "test"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion[swagger-ui]<3.0.0",
    "Flask>=2.2.5",
    "python_dateutil>=2.6.0",
    "pyjwt>=2.6.0",
    "swagger-ui-bundle>=0.0.2",
    "cloudharness",
]

setup(
    name=NAME,
    version=VERSION,
    description="test",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["OpenAPI", "test"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['test=test.__main__:main']},
    long_description="""\
    test
    """
)
