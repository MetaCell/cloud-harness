import glob
import json
import logging
import os
import shutil
import subprocess
import sys
import urllib.request
from os.path import dirname as dn, join

from . import HERE
from .utils import replaceindir, to_python_module

CODEGEN = os.path.join(HERE, 'bin', 'openapi-generator-cli.jar')
APPLICATIONS_SRC_PATH = os.path.join('applications')
LIB_NAME = 'cloudharness_cli'
ROOT = dn(dn(HERE))

OPENAPI_GEN_URL = 'https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/6.2.1/openapi-generator-cli-6.2.1.jar'


def generate_server(app_path, overrides_folder=""):
    get_dependencies()
    openapi_dir = os.path.join(app_path, 'api')
    openapi_file = glob.glob(os.path.join(openapi_dir, '*.yaml'))[0]
    out_name = f"backend" if not os.path.exists(
        f"{app_path}/server") else f"server"
    out_path = f"{app_path}/{out_name}"
    command = f"java -jar {CODEGEN} generate -i {openapi_file} -g python-flask -o {out_path} " \
              f"-c {openapi_dir}/config.json " + (f"-t {overrides_folder}" if overrides_folder else "")
    os.system(command)


def generate_fastapi_server(app_path):
    command = f"cd {app_path}/api && bash -c ./genapi.sh"
    os.system(command)


def generate_model(base_path=ROOT):
    get_dependencies()
    lib_path = f"{base_path}/libraries/models"

    # Generate model stuff: use python-flask generator
    command = f"java -jar {CODEGEN} generate -i {base_path}/libraries/api/openapi.yaml -g python-flask -o {lib_path}  --skip-validate-spec -c {base_path}/libraries/api/config.json"
    os.system(command)

    # Generate docs: use python generator
    tmp_path = f"{lib_path}/tmp"
    command = f"java -jar {CODEGEN} generate -i {base_path}/libraries/api/openapi.yaml -g python -o {tmp_path}  --skip-validate-spec -c {base_path}/libraries/api/config.json"
    os.system(command)
    try:
        source_dir = join(tmp_path, "docs")
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
    config_path = os.path.join(os.path.dirname(openapi_file), 'config.json')

    module = to_python_module(module)
    with open(config_path, 'w') as f:
        f.write(json.dumps(dict(packageName=f"{lib_name}.{module}")))
    command = f"java -jar {CODEGEN} generate " \
              f"-i {openapi_file} " \
              f"-g python " \
              f"-o {client_src_path}/tmp-{module} " \
              f"-c {config_path}"
    os.system(command)


def generate_ts_client(openapi_file):
    get_dependencies()
    config_path = os.path.join(os.path.dirname(openapi_file), 'config.json')
    out_dir = f"{os.path.dirname(os.path.dirname(openapi_file))}/frontend/src/rest"
    command = f"java -jar {CODEGEN} generate " \
              f"-i {openapi_file} " \
              f"-g typescript-axios " \
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
