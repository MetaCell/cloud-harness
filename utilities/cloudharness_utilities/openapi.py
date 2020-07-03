import os

import subprocess
import sys
import json
import glob
import urllib.request
from cloudharness_utilities import HERE
import logging

CODEGEN = os.path.join(HERE, 'bin', 'openapi-generator-cli.jar')
APPLICATIONS_SRC_PATH = os.path.join('applications')
LIB_NAME = 'cloudharness_cli'

OPENAPI_GEN_URL = 'https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/4.3.0/openapi-generator-cli-4.3.0.jar'

def generate_server(app_path):
    openapi_dir = os.path.join(app_path, 'api')
    openapi_file = glob.glob(os.path.join(openapi_dir, '*.yaml'))[0]
    command = f"java -jar {CODEGEN} generate -i {openapi_file} -g python-flask -o {app_path}/server -c {openapi_dir}/config.json"
    os.system(command)


def generate_python_client(module, openapi_file, client_src_path, lib_name=LIB_NAME):
    with open('config-client.json', 'w') as f:
        f.write(json.dumps(dict(packageName=f"{lib_name}.{module}")))
    command = f"java -jar {CODEGEN} generate " \
        f"-i {openapi_file} " \
        f"-g python " \
        f"-o {client_src_path}/tmp-{module} " \
        f"-c config-client.json"
    os.system(command)
    os.remove('config-client.json')


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


get_dependencies()
