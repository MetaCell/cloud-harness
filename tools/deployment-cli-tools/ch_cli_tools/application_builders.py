import abc
import json
import logging
import pathlib
import shutil
import subprocess
import tempfile
from .common_types import TemplateType
from .openapi import generate_fastapi_server, generate_server, generate_ts_client
from .utils import copymergedir, get_json_template, merge_configuration_directories, replace_in_dict, replace_in_file, replaceindir, to_python_module
from . import CH_ROOT
from cloudharness_utils.constants import APPLICATION_TEMPLATE_PATH


class ApplicationBuilder(abc.ABC):
    APP_NAME_PLACEHOLDER = '__APP_NAME__'

    def __init__(self, app_name: str, app_path: pathlib.Path):
        self.app_name = app_name
        self.app_path = app_path

    @abc.abstractmethod
    def handles(self, templates: list[str]) -> bool:
        pass

    @abc.abstractmethod
    def handle_pre_merge(self) -> None:
        pass

    @abc.abstractmethod
    def handle_merge(self) -> None:
        pass

    @abc.abstractmethod
    def handle_post_merge(self) -> None:
        pass

    def run_command(self, *command: str, cwd: pathlib.Path = None) -> None:
        if not cwd:
            cwd = self.app_path

        logging.info(f'Running command: {" ".join(map(str, command))}')
        subprocess.run(command, cwd=cwd)

    def merge_template_directories(self, template_name: str) -> None:
        for base_path in (self.ch_root, pathlib.Path.cwd()):
            template_path = base_path / APPLICATION_TEMPLATE_PATH / template_name
            if template_path.exists():
                merge_configuration_directories(template_path, self.app_path)

    @property
    def frontend_path(self):
        return self.app_path / 'frontend'

    @property
    def backend_path(self):
        return self.app_path / 'backend'

    @property
    def api_path(self):
        return self.app_path / 'api'

    @property
    def ch_root(self):
        return pathlib.Path(CH_ROOT)

    @property
    def app_template_path(self):
        return self.ch_root / APPLICATION_TEMPLATE_PATH


class WebAppBuilder(ApplicationBuilder):
    def handles(self, templates):
        return TemplateType.WEBAPP in templates

    def handle_pre_merge(self):
        if self.frontend_path.exists():
            shutil.rmtree(self.frontend_path)

        self.create_vite_skaffold(self.frontend_path)

    def handle_merge(self):
        self.merge_template_directories(TemplateType.WEBAPP)

    def handle_post_merge(self):
        backend_dockerfile_path = self.backend_path / 'Dockerfile'
        backend_dockerfile_path.unlink(missing_ok=True)

        self.install_frontend_dependencies()
        generate_ts_client(self.api_path / 'openapi.yaml')

    def create_vite_skaffold(self, frontend_path: pathlib.Path) -> None:
        self.run_command(
            'yarn', 'create', 'vite', self.app_name,
            '--template', 'react-ts',
        )
        shutil.move(self.app_path / self.app_name, frontend_path)

    def install_frontend_dependencies(self) -> None:
        self.run_command('yarn', 'install', cwd=self.frontend_path)


class ServerAppBuilder(ApplicationBuilder):
    def handles(self, templates):
        return TemplateType.SERVER in templates

    def handle_pre_merge(self):
        with tempfile.TemporaryDirectory() as tmp_dirname:
            tmp_path = pathlib.Path(tmp_dirname)
            server_template_path = self.app_template_path / TemplateType.SERVER

            copymergedir(server_template_path, tmp_path)
            merge_configuration_directories(self.app_path, tmp_path)
            generate_server(self.app_name, tmp_path)

    def handle_merge(self):
        self.merge_template_directories(TemplateType.SERVER)

    def handle_post_merge(self):
        pass


class FlaskServerAppBuilder(ApplicationBuilder):
    def handles(self, templates):
        return TemplateType.FLASK_SERVER in templates

    def handle_pre_merge(self):
        pass

    def handle_merge(self):
        self.merge_template_directories(TemplateType.FLASK_SERVER)

    def handle_post_merge(self):
        generate_server(self.app_path)


class BaseDjangoAppBuilder(ApplicationBuilder):
    @abc.abstractmethod
    def handle_merge(self):
        self.merge_template_directories('django-base')

    @abc.abstractmethod
    def handle_post_merge(self):
        replace_in_file(
            self.app_path / 'deploy' / 'values.yaml',
            f'{self.APP_NAME_PLACEHOLDER}:{self.APP_NAME_PLACEHOLDER}',
            f'{self.python_app_name}:{self.python_app_name}',
        )
        replace_in_file(self.app_path / 'dev-setup.sh', self.APP_NAME_PLACEHOLDER, self.app_name)

        self.create_django_app_vscode_debug_configuration()

    def create_django_app_vscode_debug_configuration(self):
        vscode_launch_path = pathlib.Path('.vscode/launch.json')
        configuration_name = f'{self.app_name} backend'

        launch_config = get_json_template(vscode_launch_path, True)

        launch_config['configurations'] = [
            configuration for configuration in launch_config['configurations']
            if configuration['name'] != configuration_name
        ]

        debug_config = get_json_template(self.debug_template_file, True)
        debug_config = replace_in_dict(debug_config, self.APP_NAME_PLACEHOLDER, self.app_name)

        launch_config['configurations'].append(debug_config)

        vscode_launch_path.parent.mkdir(parents=True, exist_ok=True)
        with vscode_launch_path.open('w') as f:
            json.dump(launch_config, f, indent=2, sort_keys=True)

    @property
    def python_app_name(self):
        return to_python_module(self.app_name)

    @property
    @abc.abstractmethod
    def debug_template_file(self) -> str:
        raise NotImplementedError()


class DjangoFastApiBuilder(BaseDjangoAppBuilder):
    debug_template_file = 'vscode-django-fastapi-debug-template.json'

    def handles(self, templates):
        return TemplateType.DJANGO_FASTAPI in templates

    def handle_pre_merge(self):
        pass

    def handle_merge(self):
        super().handle_merge()
        self.merge_template_directories(TemplateType.DJANGO_FASTAPI)

    def handle_post_merge(self):
        super().handle_post_merge()

        replace_in_file(
            self.api_path / 'templates' / 'main.jinja2',
            self.APP_NAME_PLACEHOLDER,
            self.python_app_name,
        )
        replace_in_file(self.api_path / 'genapi.sh', self.APP_NAME_PLACEHOLDER, self.app_name)
        generate_fastapi_server(self.app_path)

        (self.backend_path / self.APP_NAME_PLACEHOLDER / '__main__.py').unlink(missing_ok=True)


class DjangoNinjaBuilder(BaseDjangoAppBuilder):
    debug_template_file = 'vscode-django-ninja-debug-template.json'

    def handles(self, templates):
        return TemplateType.DJANGO_NINJA in templates

    def handle_pre_merge(self):
        pass

    def handle_merge(self):
        super().handle_merge()
        self.merge_template_directories(TemplateType.DJANGO_NINJA)

    def handle_post_merge(self):
        super().handle_post_merge()


class AppBuilderPipeline(ApplicationBuilder):
    def __init__(self, app_name: str, app_path: pathlib.Path, templates: list[str]):
        super().__init__(app_name, app_path)
        self.templates = templates
        self.app_builders: dict[str, ApplicationBuilder] = {
            TemplateType.WEBAPP: WebAppBuilder(app_name, app_path),
            TemplateType.SERVER: ServerAppBuilder(app_name, app_path),
            TemplateType.FLASK_SERVER: FlaskServerAppBuilder(app_name, app_path),
            TemplateType.DJANGO_FASTAPI: DjangoFastApiBuilder(app_name, app_path),
            TemplateType.DJANGO_NINJA: DjangoNinjaBuilder(app_name, app_path),
        }

    def handles(self, templates):
        return templates == self.templates

    def handle_pre_merge(self):
        pre_merge_template_order = [
            TemplateType.FLASK_SERVER,
            TemplateType.DJANGO_FASTAPI,
            TemplateType.DJANGO_NINJA,
            TemplateType.WEBAPP,
            TemplateType.SERVER,
        ]

        app_builders = [
            self.app_builders[template] for template in pre_merge_template_order
            if self.app_builders[template].handles(self.templates)
        ]

        for app_builder in app_builders:
            app_builder.handle_pre_merge()

    def handle_merge(self):
        for template in self.templates:
            run_merge = (
                app_builder.handle_merge
                if (app_builder := self.app_builders.get(template, None))
                else lambda: self.merge_template_directories(template)
            )
            run_merge()

    def handle_post_merge(self):
        post_merge_template_order = [
            TemplateType.FLASK_SERVER,
            TemplateType.DJANGO_FASTAPI,
            TemplateType.DJANGO_NINJA,
            TemplateType.WEBAPP,
            TemplateType.SERVER,
        ]

        app_builders = [
            self.app_builders[template] for template in post_merge_template_order
            if self.app_builders[template].handles(self.templates)
        ]

        for app_builder in app_builders:
            app_builder.handle_post_merge()
