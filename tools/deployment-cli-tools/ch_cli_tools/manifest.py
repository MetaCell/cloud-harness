import abc
import copy
import logging
import pathlib
from typing import Iterable
from ruamel.yaml.error import YAMLError
from .common_types import CloudHarnessManifest, TemplateType
from .utils import load_yaml, save_yaml


def get_manifest(app_path: pathlib.Path) -> CloudHarnessManifest:
    manifest_file = app_path / '.ch-manifest'

    try:
        manifest_data = load_yaml(manifest_file)
        return CloudHarnessManifest.from_dict(manifest_data)
    except (FileNotFoundError, YAMLError):
        logging.info(f'Could not load manifest file {manifest_file}, inferring manifest from app structure...')
        manifest = CloudHarnessManifest(
            app_name=app_path.name,
            inferred=True,
            templates=infer_templates(app_path),
        )
        save_yaml(manifest_file, manifest.to_dict())
        return manifest


def load_manifest(manifest_file: pathlib.Path) -> dict:
    manifest_data = load_yaml(manifest_file)
    migrated_data = migrate_manifest_data(manifest_data)

    if manifest_data != migrated_data:
        save_yaml(manifest_file, migrated_data)

    return migrated_data


def migrate_manifest_data(data: dict) -> dict:
    data = copy.deepcopy(data)
    data_version = data['version']
    migrations = [
        migration for migration in _MIGRATIONS_LIST
        if data_version < migration.change_version
    ]

    for migration in migrations:
        migration.migrate(data)

    return data


def infer_templates(app_path: pathlib.Path) -> list[str]:
    return [
        TemplateType.BASE,
        *infer_webapp_template(app_path),
        *infer_server_template(app_path),
        *infer_database_template(app_path),
    ]


def infer_webapp_template(app_path: pathlib.Path) -> Iterable[str]:
    frontend_path = app_path / 'frontend'
    if frontend_path.exists():
        yield TemplateType.WEBAPP


def infer_server_template(app_path: pathlib.Path) -> Iterable[str]:
    backend_path = app_path / 'backend'
    manage_path = backend_path / 'manage.py'

    if manage_path.exists():
        yield from infer_django_template(backend_path)
        return

    server_path = app_path / 'server'
    if server_path.exists() or backend_path.exists():
        yield TemplateType.FLASK_SERVER


def infer_django_template(backend_path: pathlib.Path) -> Iterable[str]:
    requirements_path = backend_path / 'requirements.txt'
    requirements = requirements_path.read_text()

    if 'django-ninja' in requirements:
        yield TemplateType.DJANGO_NINJA
    else:
        yield TemplateType.DJANGO_FASTAPI


def infer_database_template(app_path: pathlib.Path) -> Iterable[str]:
    values_file = app_path / 'deploy' / 'values.yaml'

    try:
        values_data = load_yaml(values_file)
        database_config = values_data['harness']['database']
        if not database_config['auto']:
            return

        database_type = database_config['type']
        database_type_to_template_map = {
            'mongo': TemplateType.DB_MONGO,
            'neo4j': TemplateType.DB_NEO4J,
            'postgres': TemplateType.DB_POSTGRES,
        }

        if database_type in database_type_to_template_map:
            yield database_type_to_template_map[database_type]

    except (FileNotFoundError, YAMLError, KeyError):
        pass


class ManifestMigration(abc.ABC):
    @property
    @abc.abstractmethod
    def change_version(self) -> str:
        ...

    @abc.abstractmethod
    def migrate(data: dict) -> None:
        ...


class NameChangeFromDjangoAppToDjangoFastapi(ManifestMigration):
    change_version = '2'

    def migrate(data):
        data['templates'] = [
            template if template != 'django-app' else 'django-fastapi'
            for template in data['templates']
        ]


_MIGRATIONS_LIST: list[ManifestMigration] = [
    NameChangeFromDjangoAppToDjangoFastapi(),
]
