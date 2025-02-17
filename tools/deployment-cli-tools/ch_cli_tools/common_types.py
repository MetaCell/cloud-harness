import copy
from dataclasses import dataclass
from typing import Union


try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum


class TemplateType(StrEnum):
    BASE = 'base'
    FLASK_SERVER = 'flask-server'
    WEBAPP = 'webapp'
    DB_POSTGRES = 'db-postgres'
    DB_NEO4J = 'db-neo4j'
    DB_MONGO = 'db-mongo'
    DJANGO_FASTAPI = 'django-fastapi'
    DJANGO_NINJA = 'django-ninja'
    SERVER = 'server'

    @classmethod
    def database_templates(cls):
        return [cls.DB_POSTGRES, cls.DB_NEO4J, cls.DB_MONGO]

    @classmethod
    def django_templates(cls) -> list[str]:
        return [cls.DJANGO_FASTAPI, cls.DJANGO_NINJA]


@dataclass
class CloudHarnessManifest():
    app_name: str
    inferred: bool
    templates: list[str]
    version: str = '2'

    @classmethod
    def from_dict(cls, data: dict) -> 'CloudHarnessManifest':
        return cls(
            app_name=data['app-name'],
            version=data['version'],
            inferred=data['inferred'],
            templates=data['templates'],
        )

    def to_dict(self) -> dict:
        return {
            'app-name': self.app_name,
            'version': self.version,
            'inferred': self.inferred,
            'templates': [str(template) for template in self.templates],
        }
