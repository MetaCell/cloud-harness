import os
import oyaml as yaml
import logging

from .constants import HERE, BUILD_STEP_BASE, BUILD_STEP_STATIC, BUILD_STEP_PARALLEL, BUILD_STEP_INSTALL, \
    CODEFRESH_PATH, CODEFRESH_BUILD_PATH, \
    CODEFRESH_TEMPLATE_PATH, APPS_PATH, STATIC_IMAGES_PATH, BASE_IMAGES_PATH, DEPLOYMENT_PATH
from .helm import collect_helm_values
from .utils import find_dockerfiles_paths, app_name_from_path, \
    get_image_name, get_template, merge_to_yaml_file, dict_merge

logging.getLogger().setLevel(logging.INFO)

CLOUD_HARNESS_PATH = "cloud-harness"


def create_codefresh_deployment_scripts(root_paths, codefresh_path=CODEFRESH_PATH, include=()):
    """
    Entry point to create deployment scripts for codefresh: codefresh.yaml and helm chart
    """

    if include:
        logging.info('Including the following subpaths to the build: %s.', ', '.join(include))

    codefresh = get_template(os.path.join(HERE, CODEFRESH_TEMPLATE_PATH))

    codefresh['steps'][BUILD_STEP_BASE]['steps'] = {}
    codefresh['steps'][BUILD_STEP_STATIC]['steps'] = {}
    codefresh['steps'][BUILD_STEP_PARALLEL]['steps'] = {}

    for root_path in root_paths:
        template_path = os.path.join(root_path, CODEFRESH_TEMPLATE_PATH)
        if os.path.exists(template_path):
            tpl = get_template(template_path)
            del tpl['steps'][BUILD_STEP_BASE]
            del tpl['steps'][BUILD_STEP_STATIC]
            del tpl['steps'][BUILD_STEP_PARALLEL]
            codefresh = dict_merge(codefresh, tpl)

        def codefresh_build_step_from_base_path(base_path, build_step, fixed_context=None):
            abs_base_path = os.path.join(os.getcwd(), base_path)
            for dockerfile_path in find_dockerfiles_paths(abs_base_path):
                app_relative_to_root = os.path.relpath(dockerfile_path, '.')
                app_relative_to_base = os.path.relpath(dockerfile_path, abs_base_path)
                app_name = app_name_from_path(app_relative_to_base)
                if include and not any(inc in dockerfile_path for inc in include):
                    continue
                build = codefresh_app_build_spec(
                    app_name=app_name,
                    app_context_path=os.path.relpath(fixed_context, root_path) if fixed_context else app_relative_to_root,
                    dockerfile_path=os.path.join(os.path.relpath(dockerfile_path, '.') if fixed_context else '',
                                                 "Dockerfile"))
                codefresh['steps'][build_step]['steps'][app_name] = build

        codefresh_build_step_from_base_path(os.path.join(root_path, BASE_IMAGES_PATH), BUILD_STEP_BASE,
                                            fixed_context=root_path)
        codefresh_build_step_from_base_path(os.path.join(root_path, STATIC_IMAGES_PATH), BUILD_STEP_STATIC)
        codefresh_build_step_from_base_path(os.path.join(root_path, APPS_PATH), BUILD_STEP_PARALLEL)

    codefresh['steps'] = {k: step for k, step in codefresh['steps'].items() if
                          'type' not in step or step['type'] != 'parallel' or (
                              step['steps'] if 'steps' in step else [])}

    codefresh_abs_path = os.path.join(os.getcwd(), DEPLOYMENT_PATH, codefresh_path)
    codefresh_dir = os.path.dirname(codefresh_abs_path)
    if not os.path.exists(codefresh_dir):
        os.makedirs(codefresh_dir)
    with open(codefresh_abs_path, 'w') as f:
        yaml.dump(codefresh, f)


def codefresh_build_spec(**kwargs):
    """
    Create Codefresh build specification
    :return:
    """

    build = get_template(CODEFRESH_BUILD_PATH)

    build.update(kwargs)
    return build


def codefresh_app_build_spec(app_name, app_context_path, dockerfile_path="Dockerfile"):
    logging.info('Generating build script for ' + app_name)
    title = app_name.capitalize().replace('-', ' ').replace('/', ' ').replace('.', ' ').strip()
    build = codefresh_build_spec(image_name=get_image_name(app_name), title=title,
                                 working_directory='./' + app_context_path,
                                 dockerfile=dockerfile_path)

    specific_build_template_path = os.path.join(app_context_path, 'build.yaml')
    if os.path.exists(specific_build_template_path):
        logging.info("Specific build template found: %s" % (specific_build_template_path))
        with open(specific_build_template_path) as f:
            build_specific = yaml.safe_load(f)

        build_args = build_specific.pop('build_arguments') if 'build_arguments' in build_specific else []
        build.update(build_specific)
        build.update({'build_arguments': build['build_arguments'] + build_args})

    return build
