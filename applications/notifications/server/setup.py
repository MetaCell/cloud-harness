# coding: utf-8

import sys
from setuptools import setup, find_packages

NAME = "notifications"
VERSION = "2.3.0"

# To install the library, run the following
#
# python setup.py install
#
# prerequisite: setuptools
# http://pypi.python.org/pypi/setuptools

REQUIRES = [
    "jinja2>=3"
    "python_dateutil>=2.6.0"
]

setup(
    name=NAME,
    version=VERSION,
    description="notifications",
    author_email="cloudharness@metacell.us",
    url="",
    keywords=["notifications"],
    install_requires=REQUIRES,
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': ['notifications=notifications.__main__:main']},
    long_description="""\
    notifications
    """
)

