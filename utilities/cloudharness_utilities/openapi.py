import os

import subprocess
import sys
import shutil
import json
import glob
import urllib.request
from cloudharness_utilities import HERE
from cloudharness_utilities.utils import copymergedir, replaceindir, movedircontent, replace_in_file
import logging

CODEGEN = os.path.join(HERE, 'bin', 'openapi-generator-cli.jar')
APPLICATIONS_SRC_PATH = os.path.join('applications')
LIB_NAME = 'cloudharness_cli'

OPENAPI_GEN_URL = 'https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/5.0.0/openapi-generator-cli-5.0.0.jar'



def generate_server(app_path):
    openapi_dir = os.path.join(app_path, 'api')
    openapi_file = glob.glob(os.path.join(openapi_dir, '*.yaml'))[0]
    out_name = f"backend" if not os.path.exists(f"{app_path}/server") else f"server"
    out_path=f"{app_path}/{out_name}"
    command = f"java -jar {CODEGEN} generate -i {openapi_file} -g python-flask -o {out_path} -c {openapi_dir}/config.json"
    os.system(command)



def generate_python_client(module, openapi_file, client_src_path, lib_name=LIB_NAME):
    config_path = os.path.join(os.path.dirname(openapi_file), 'config.json')

    module = module.replace('-', '_')
    with open(config_path, 'w') as f:
        f.write(json.dumps(dict(packageName=f"{lib_name}.{module}")))
    command = f"java -jar {CODEGEN} generate " \
              f"-i {openapi_file} " \
              f"-g python " \
              f"-o {client_src_path}/tmp-{module} " \
              f"-c {config_path}"
    os.system(command)

def generate_ts_client(openapi_file):
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
        logging.warning("Code generator client not found \n")
        cdir = os.path.dirname(CODEGEN)
        if not os.path.exists(cdir):
            os.makedirs(cdir)
        urllib.request.urlretrieve(OPENAPI_GEN_URL, CODEGEN)
