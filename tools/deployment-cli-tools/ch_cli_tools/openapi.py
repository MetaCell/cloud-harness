import enum
import functools
import glob
import json
import logging
import operator
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Callable, Optional
import urllib.request
from os.path import dirname as dn, join

from ch_cli_tools.common_types import TemplateType
from ch_cli_tools.manifest import get_manifest

from . import HERE
from .utils import copymergedir, replaceindir, to_python_module

CODEGEN = os.path.join(HERE, 'bin', 'openapi-generator-cli.jar')
APPLICATIONS_SRC_PATH = os.path.join('applications')
LIB_NAME = 'cloudharness_cli'
ROOT = dn(dn(dn(HERE)))

OPENAPI_GEN_URL = 'https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.7.0/openapi-generator-cli-7.7.0.jar'


class ClientType(enum.Flag):
    TS_CLIENT = enum.auto()
    PYTHON_CLIENT = enum.auto()

    @classmethod
    def all(cls):
        return functools.reduce(operator.or_, cls)


def generate_flask_server(app_path: pathlib.Path, overrides_folder: Optional[pathlib.Path] = None) -> None:
    get_dependencies()

    openapi_directory = app_path / 'api'
    openapi_file = next(openapi_directory.glob('*.yaml'))

    server_path = app_path / 'server'
    backend_path = app_path / 'backend'
    out_path = server_path if server_path.exists() else backend_path

    command = [
        'java', '-jar', CODEGEN, 'generate',
        '-i', openapi_file,
        '-g', 'python-flask',
        '-o', out_path,
        '-c', openapi_directory / 'config.json',
    ]
    if overrides_folder:
        command += ['-t', overrides_folder]

    subprocess.run(command)


def generate_fastapi_server(app_path: pathlib.Path) -> None:
    # Install the fastapi code generator here as it comes with potential problematic dependencies
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fastapi-code-generator"])
    api_directory = app_path / 'api'
    backend_directory = app_path / 'backend'
    temp_directory = api_directory / 'app'

    command = [
        'fastapi-codegen',
        '--input', api_directory / 'openapi.yaml',
        '--output', temp_directory,
        '-t', api_directory / 'templates',
    ]
    subprocess.run(command)

    source_main = temp_directory / 'main.py'
    destination_main = backend_directory / 'main.py'
    source_main.replace(destination_main)

    source_models = temp_directory / 'models.py'
    destination_models = backend_directory / 'openapi' / 'models.py'
    source_models.replace(destination_models)

    temp_directory.rmdir()

    logging.info('Generated new models and main.py')


def generate_model(base_path=ROOT):
    get_dependencies()
    lib_path = f"{base_path}/libraries/models"

    # Generate model stuff: use python-flask generator
    command = f"java -jar {CODEGEN} generate -i {base_path}/libraries/models/api/openapi.yaml -g python-flask -o \
          {lib_path}  --skip-validate-spec -c {base_path}/libraries/models/api/config.json"
    os.system(command)

    # Generate docs: use python generator
    tmp_path = f"{lib_path}/tmp"
    command = f"java -jar {CODEGEN} generate -i {base_path}/libraries/models/api/openapi.yaml -g python -o \
        {tmp_path}  --skip-validate-spec -c {base_path}/libraries/models/api/config.json"
    os.system(command)
    try:
        source_dir = join(tmp_path, "docs")
        if not os.path.exists(source_dir):
            os.makedirs(source_dir)

        dest = join(base_path, "docs/model")
        if os.path.exists(dest):
            shutil.rmtree(dest)
        os.makedirs(dest)
        file_names = os.listdir(source_dir)
        for file_name in file_names:
            shutil.move(join(source_dir, file_name), dest)
        shutil.rmtree(tmp_path)
    except:
        logging.error(
            "An error occurred while moving generated resources", exc_info=True)


def generate_python_client(module, openapi_file, client_src_path, lib_name=LIB_NAME):
    get_dependencies()

    module = to_python_module(module)
    command = f"java -jar {CODEGEN} generate -i {openapi_file} -g python" \
        f" -o {client_src_path}/tmp-{module} " \
        f"--additional-properties packageName={lib_name}.{module}"
    os.system(command)


def generate_ts_client(openapi_file):
    get_dependencies()
    out_dir = f"{os.path.dirname(os.path.dirname(openapi_file))}/frontend/src/rest"
    command = f"java -jar {CODEGEN} generate " \
        f"-i {openapi_file} " \
        f"-g typescript-fetch " \
        f"-o {out_dir}"
    os.system(command)

    replaceindir(out_dir, "http://localhost", '')


def generate_openapi_from_ninja_schema(app_name: str, app_path: pathlib.Path) -> None:
    subprocess.check_call(["sh", "dev-setup.sh"], cwd=app_path)
    out_path = app_path / 'api' / 'openapi.yaml'

    manage_path = app_path / 'backend' / 'manage.py'
    command = [
        'python', manage_path, 'export_openapi_schema',
        '--settings', 'django_baseapp.settings',
        '--api', f'{to_python_module(app_name)}.api.api',
        '--output', out_path,
        '--indent', '2',
    ]

    subprocess.run(command)


def get_dependencies():
    """
    Checks if java is installed
    Checks if swagger-codegen-cli.jar exists
    File paths assume script is ran from the script directory
    swagger-codegen-cli version should be 2.4.6 or higher
    """
    try:
        subprocess.check_output(['java', '-version'])
    except Exception as e:
        sys.exit('java not found')

    if not os.path.exists(CODEGEN):
        logging.warning("Code generator client not found: downloading \n")
        cdir = os.path.dirname(CODEGEN)
        if not os.path.exists(cdir):
            os.makedirs(cdir)
        urllib.request.urlretrieve(OPENAPI_GEN_URL, CODEGEN)


def generate_models(
        root_path: pathlib.Path,
        should_generate: Callable[[str], bool],
) -> None:
    """
    Generates the main model
    """
    library_models_path = root_path / 'libraries' / 'models'

    if not library_models_path.exists():
        return

    if not should_generate('the main model'):
        return

    generate_model()


def generate_servers(
        root_path: pathlib.Path,
        should_generate: Callable[[str], bool],
        app_name: Optional[str],
) -> None:
    """
    Generates server stubs
    """
    openapi_files = [path for path in root_path.glob('applications/*/api/*.yaml')]

    for openapi_file in openapi_files:
        app_path = openapi_file.parent.parent
        manifest = get_manifest(app_path)

        if app_name and manifest.app_name != app_name:
            continue

        if not should_generate(f'server stubs for {openapi_file}'):
            continue

        if TemplateType.DJANGO_FASTAPI in manifest.templates:
            generate_fastapi_server(app_path)

        if TemplateType.FLASK_SERVER in manifest.templates:
            generate_flask_server(app_path)


def generate_clients(
        root_path: pathlib.Path,
        should_generate: Callable[[str], bool],
        app_name: Optional[str],
        client_lib_name: str,
        client_types: ClientType,
) -> None:
    """
    Generates client stubs
    """
    if not should_generate('client libraries'):
        return

    client_src_path = root_path / 'libraries' / 'client' / client_lib_name
    apps_path = root_path / 'applications'
    apps = (app for app in apps_path.iterdir() if app.is_dir())

    for app_path in apps:
        manifest = get_manifest(app_path)

        if app_name and manifest.app_name != app_name:
            continue

        if TemplateType.DJANGO_NINJA in manifest.templates:
            generate_openapi_from_ninja_schema(manifest.app_name, app_path)

        for openapi_file in app_path.glob('api/*.yaml'):
            if ClientType.PYTHON_CLIENT in client_types:
                generate_python_client(manifest.app_name, openapi_file, client_src_path, lib_name=client_lib_name)

            if TemplateType.WEBAPP in manifest.templates and ClientType.TS_CLIENT in client_types:
                generate_ts_client(openapi_file)

    aggregate_packages(client_src_path, client_lib_name)


def aggregate_packages(client_source_path: pathlib.Path, lib_name=LIB_NAME):
    client_source_path.mkdir(parents=True, exist_ok=True)

    client_docs_path = client_source_path / 'docs'
    client_docs_path.mkdir(exist_ok=True)

    client_test_path = client_source_path / 'test'
    client_test_path.mkdir(exist_ok=True)

    client_readme_file = client_source_path / 'README.md'
    client_readme_file.unlink(missing_ok=True)

    client_requirements_file = client_source_path / 'requirements.txt'
    client_requirements_file.unlink(missing_ok=True)

    client_test_requirements_file = client_source_path / 'test-requirements.txt'
    client_test_requirements_file.unlink(missing_ok=True)

    requirements_lines_seen = set()
    test_requirements_lines_seen = set()

    for temp_module_path in client_source_path.glob('tmp-*/'):
        module = (
            temp_module_path
            .name
            .removeprefix('tmp-')
            .replace('-', '_')
        )

        code_destination_directory = client_source_path / lib_name / module
        copymergedir(temp_module_path / lib_name / module, code_destination_directory)
        copymergedir(temp_module_path / f'{lib_name}.{module}', code_destination_directory)  # Fixes a bug with nested packages

        module_docs_path = client_docs_path / module
        module_docs_path.mkdir(parents=True, exist_ok=True)
        copymergedir(client_source_path / temp_module_path.name / 'docs', module_docs_path)

        module_tests_path = client_source_path / 'test' / module
        copymergedir(temp_module_path / 'test', module_tests_path)

        readme_file = temp_module_path / 'README.md'
        if not readme_file.exists():
            logging.warning(f'Readme file not found: {readme_file}.')
            continue

        with client_readme_file.open('+a') as out_file, readme_file.open('r') as in_file:
            file_data = in_file.read()
            updated_file_data = file_data.replace('docs/', f'docs/{module}/')
            out_file.write(updated_file_data)

        # FIXME: Different package versions will remain in the output file
        requirements_file = temp_module_path / 'requirements.txt'
        with requirements_file.open('r') as in_file, client_requirements_file.open('+a') as out_file:
            unseen_lines = [line for line in in_file if line not in requirements_lines_seen]
            requirements_lines_seen.update(unseen_lines)
            out_file.writelines(unseen_lines)

        # FIXME: Different package versions will remain in the output file
        test_requirements_file = temp_module_path / 'test-requirements.txt'
        with test_requirements_file.open('r') as in_file, client_test_requirements_file.open('+a') as out_file:
            unseen_lines = [line for line in in_file if line not in test_requirements_lines_seen]
            test_requirements_lines_seen.update(unseen_lines)
            out_file.writelines(unseen_lines)

        shutil.rmtree(temp_module_path)
