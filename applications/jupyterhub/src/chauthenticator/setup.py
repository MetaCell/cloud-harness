from setuptools import setup, find_packages

setup(
    name='chauthenticator',
    version='0.1.0',
    install_requires=[
        'oauthenticator',
        'python-jose'
    ],
    description='Authenticator to use Jupyterhub with the keycloak gatekeeper.',
    url='',
    author='Zoran Sinnema',
    author_email='zoran@metacell.us',
    license='BSD',
    packages=['chauthenticator'],
)
