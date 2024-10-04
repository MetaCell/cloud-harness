import glob
import json
import logging
import os
import pathlib
import shutil
import subprocess
import sys
from typing import Optional
import urllib.request
from os.path import dirname as dn, join

from . import HERE
from .utils import replaceindir, to_python_module

CODEGEN = os.path.join(HERE, 'bin', 'openapi-generator-cli.jar')
APPLICATIONS_SRC_PATH = os.path.join('applications')
LIB_NAME = 'cloudharness_cli'
ROOT = dn(dn(dn(HERE)))

OPENAPI_GEN_URL = 'https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.7.0/openapi-generator-cli-7.7.0.jar'


def generate_server(app_path: pathlib.Path, overrides_folder: Optional[str]=None) -> None:
    get_dependencies()

    openapi_directory = app_path/'api'
    openapi_file = next(openapi_directory.glob('*.yaml'))

    server_path = app_path/'server'
    backend_path = app_path/'backend'
    out_path = server_path if server_path.exists() else backend_path

    command = [
        'java', '-jar', CODEGEN, 'generate',
        '-i', openapi_file,
        '-g', 'python-flask',
        '-o', out_path,
        '-c', openapi_directory/'config.json',
    ]
    if overrides_folder:
        command += ['-t', overrides_folder]

    subprocess.run(command)


def generate_fastapi_server(app_path: pathlib.Path) -> None:
    api_directory = app_path/'api'
    backend_directory = app_path/'backend'
    temp_directory = api_directory/'app'

    command = [
        'fastapi-codegen',
        '--input', api_directory/'openapi.yaml',
        '--output', temp_directory,
        '-t', api_directory/'templates',
    ]
    subprocess.run(command)

    source_main = temp_directory/'main.py'
    destination_main = backend_directory/'main.py'
    source_main.replace(destination_main)

    source_models = temp_directory/'models.py'
    destination_models = backend_directory/'openapi'/'models.py'
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
