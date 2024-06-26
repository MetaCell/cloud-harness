# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "__APP_NAME__"
VERSION = "1.0.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "connexion>=2.0.2",
    "swagger-ui-bundle>=0.0.2",
    "python_dateutil>=2.6.0",
    "pyjwt>=2.6.0",
    "cloudharness"
]

setup(
    name=NAME,
    version=VERSION,
    description="__APP_NAME__",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["OpenAPI", "__APP_NAME__"],
    install_requires=REQUIRES,
    packages=find_packages(),
    package_data={'': ['openapi/openapi.yaml']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['__APP_NAME__=__APP_NAME__.__main__:main']},
    long_description="""\
    __APP_NAME__
    """
)

