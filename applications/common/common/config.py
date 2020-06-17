import os

from cloudharness.utils.config import CloudharnessConfig as conf

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SENTRY_POSTGRES_APP = conf.get_application_by_filter(name='sentry')[0].postgres
    SENTRY_APP = conf.get_application_by_filter(name='sentry')[0].name
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{SENTRY_POSTGRES_APP.user}:{SENTRY_POSTGRES_APP.password}@{SENTRY_POSTGRES_APP.name}:{SENTRY_POSTGRES_APP.port}/{SENTRY_POSTGRES_APP.initialdb}'


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True
