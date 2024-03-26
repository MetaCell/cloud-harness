from setuptools import setup, find_packages

REQUIREMENTS = [
    'jupyterhub-kubespawner',
    'kubernetes==20.13.0'
]

setup(
    name='harness_jupyter',
    version='0.1',
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    url='',
    license='MIT',
    install_requires=REQUIREMENTS,
    author='Filippo Ledda',
    author_email='filippo@metacell.us',
    description='Utilities to integrate Cloud Harness functionalities with Jupyter applications'
)
