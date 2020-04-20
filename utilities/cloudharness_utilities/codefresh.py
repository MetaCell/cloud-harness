import os
import pyaml
import yaml
import logging

from .constants import HERE, BUILD_STEP_BASE, BUILD_STEP_STATIC, BUILD_STEP_PARALLEL, BUILD_STEP_INSTALL, \
    CODEFRESH_REGISTRY, K8S_IMAGE_EXCLUDE, CODEFRESH_PATH, CODEFRESH_BUILD_PATH, \
    CODEFRESH_TEMPLATE_PATH, APPS_PATH, STATIC_IMAGES_PATH, BASE_IMAGES_PATH
from .helm import collect_helm_values
from .utils import find_dockerfiles_paths, image_name_from_docker_path, \
    get_image_name, get_template, merge_to_yaml_file

logging.getLogger().setLevel(logging.INFO)

def create_codefresh_deployment_scripts(deployment_root, tag="${{CF_REVISION}}", codefresh_path=CODEFRESH_PATH):
    """
    Entry point to create deployment scripts for codefresh: codefresh.yaml and helm chart
    """

    codefresh = get_template(CODEFRESH_TEMPLATE_PATH)

    codefresh['steps'][BUILD_STEP_BASE]['steps'] = {}
    codefresh['steps'][BUILD_STEP_STATIC]['steps'] = {}
    codefresh['steps'][BUILD_STEP_PARALLEL]['steps'] = {}

    def codefresh_build_step_from_base_path(base_path, build_step, root_context=None):
        abs_base_path = os.path.join(deployment_root, base_path)
        for dockerfile_path in find_dockerfiles_paths(abs_base_path):
            app_relative_to_root = os.path.relpath(dockerfile_path, deployment_root)
            app_relative_to_base = os.path.relpath(dockerfile_path, abs_base_path)
            app_name = image_name_from_docker_path(app_relative_to_base)
            if app_name in K8S_IMAGE_EXCLUDE:
                continue
            build = codefresh_app_build_spec(app_name, os.path.relpath(root_context, deployment_root) if root_context else app_relative_to_root,
                                             dockerfile_path=os.path.join(os.path.relpath(dockerfile_path, root_context) if root_context else '', "Dockerfile"))
            codefresh['steps'][build_step]['steps'][app_name] = build

    codefresh_build_step_from_base_path(BASE_IMAGES_PATH, BUILD_STEP_BASE, root_context=deployment_root)
    codefresh_build_step_from_base_path(STATIC_IMAGES_PATH, BUILD_STEP_STATIC)
    codefresh_build_step_from_base_path(APPS_PATH, BUILD_STEP_PARALLEL)

    codefresh['steps'] = {k:step for k, step in codefresh['steps'].items() if 'type' not in step or step['type'] != 'parallel' or step['steps']}

    with open(codefresh_path, 'w') as f:
        pyaml.dump(codefresh, f)


def codefresh_build_spec(**kwargs):
    """
    Create Codefresh build specification
    :return:
    """

    build = get_template(CODEFRESH_BUILD_PATH)

    build.update(kwargs)
    return build


def codefresh_app_build_spec(app_name, app_path, dockerfile_path="Dockerfile"):
    logging.info('Generating build script for ' + app_name)
    title = app_name.capitalize().replace('-', ' ').replace('/', ' ').replace('.', ' ').strip()
    build = codefresh_build_spec(image_name=get_image_name(app_name), title=title, working_directory= './' + app_path, dockerfile=dockerfile_path)

    specific_build_template_path = os.path.join(app_path, 'build.yaml')
    if os.path.exists(specific_build_template_path):
        logging.info("Specific build template found:", specific_build_template_path)
        with open(specific_build_template_path) as f:
            build_specific = yaml.safe_load(f)
        build.update(build_specific)
    return build
