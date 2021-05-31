import os
import oyaml as yaml
import yaml.representer

import logging

from .constants import CF_STEP_INSTALL, HERE, CF_BUILD_STEP_BASE, CF_BUILD_STEP_STATIC, CF_BUILD_STEP_PARALLEL, CF_STEP_PUBLISH, \
    CODEFRESH_PATH, CF_BUILD_PATH, CF_TEMPLATE_PUBLISH_PATH, DEPLOYMENT_CONFIGURATION_PATH, \
    CF_TEMPLATE_PATH, APPS_PATH, STATIC_IMAGES_PATH, BASE_IMAGES_PATH, DEPLOYMENT_PATH, EXCLUDE_PATHS
from .helm import collect_helm_values
from .utils import find_dockerfiles_paths, image_name_from_dockerfile_path, \
    get_image_name, get_template, merge_to_yaml_file, dict_merge, app_name_from_path

logging.getLogger().setLevel(logging.INFO)

CLOUD_HARNESS_PATH = "cloud-harness"


# Codefresh variables may need quotes: adjust yaml dump accordingly
def literal_presenter(dumper, data):
    if isinstance(data, str) and "\n" in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    if isinstance(data, str) and data.startswith('${{'):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, literal_presenter)


def create_codefresh_deployment_scripts(root_paths, out_filename=CODEFRESH_PATH, include=(), exclude=(),
                                        template_name=CF_TEMPLATE_PATH, base_image_name=None,
                                        values_manual_deploy=None):
    """
    Entry point to create deployment scripts for codefresh: codefresh.yaml and helm chart
    """

    if include:
        logging.info('Including the following subpaths to the build: %s.', ', '.join(include))

    if exclude:
        logging.info('Excluding the following subpaths to the build: %s.', ', '.join(exclude))

    codefresh = get_template(os.path.join(HERE, template_name), True)

    if not codefresh:
        if template_name != CF_TEMPLATE_PATH:
            logging.warning("Template file %s not found", template_name)
            if os.path.exists(os.path.join(HERE, CF_TEMPLATE_PATH)):
                logging.info("Loading legacy template %s", CF_TEMPLATE_PATH)
                codefresh = get_template(os.path.join(HERE, CF_TEMPLATE_PATH), True)
        return

    if CF_BUILD_STEP_BASE in codefresh['steps']:
        codefresh['steps'][CF_BUILD_STEP_BASE]['steps'] = {}
        codefresh['steps'][CF_BUILD_STEP_STATIC]['steps'] = {}
        codefresh['steps'][CF_BUILD_STEP_PARALLEL]['steps'] = {}
    if CF_STEP_PUBLISH in codefresh['steps']:
        codefresh['steps'][CF_STEP_PUBLISH]['steps'] = {}

    for root_path in root_paths:
        template_path = os.path.join(root_path, DEPLOYMENT_CONFIGURATION_PATH, template_name)
        if os.path.exists(template_path):
            tpl = get_template(template_path, True)
            if CF_BUILD_STEP_BASE in codefresh['steps']:
                del tpl['steps'][CF_BUILD_STEP_BASE]
            if CF_BUILD_STEP_STATIC in codefresh['steps']:
                del tpl['steps'][CF_BUILD_STEP_STATIC]
            if CF_BUILD_STEP_PARALLEL in codefresh['steps']:
                del tpl['steps'][CF_BUILD_STEP_PARALLEL]
            if CF_STEP_PUBLISH in codefresh['steps']:
                del tpl['steps'][CF_STEP_PUBLISH]
            codefresh = dict_merge(codefresh, tpl)

        def codefresh_build_step_from_base_path(base_path, build_step, fixed_context=None, include=include):
            abs_base_path = os.path.join(os.getcwd(), base_path)
            for dockerfile_path in find_dockerfiles_paths(abs_base_path):
                app_relative_to_root = os.path.relpath(dockerfile_path, '.')
                app_relative_to_base = os.path.relpath(dockerfile_path, abs_base_path)
                app_name = app_name_from_path(app_relative_to_base)
                if include and not any(
                        f"/{inc}/" in dockerfile_path or dockerfile_path.endswith(f"/{inc}") for inc in include):
                    continue
                if any(inc in dockerfile_path for inc in (list(exclude) + EXCLUDE_PATHS)):
                    continue
                build = None
                if CF_BUILD_STEP_BASE in codefresh['steps']:
                    build = codefresh_app_build_spec(
                        app_name=app_name,
                        app_context_path=os.path.relpath(fixed_context, '.') if fixed_context else app_relative_to_root,
                        dockerfile_path=os.path.join(
                            os.path.relpath(dockerfile_path, fixed_context) if fixed_context else '',
                            "Dockerfile"),
                        base_name=base_image_name
                    )
                    codefresh['steps'][build_step]['steps'][app_name] = build
                if CF_STEP_PUBLISH in codefresh['steps']:
                    codefresh['steps'][CF_STEP_PUBLISH]['steps']['publish_' + app_name] = codefresh_app_publish_spec(
                        app_name=app_name,
                        build_tag=build and build['tag'],
                        base_name=base_image_name
                    )

        codefresh_build_step_from_base_path(os.path.join(root_path, BASE_IMAGES_PATH), CF_BUILD_STEP_BASE,
                                            fixed_context=root_path, include=None)
        codefresh_build_step_from_base_path(os.path.join(root_path, STATIC_IMAGES_PATH), CF_BUILD_STEP_STATIC,
                                            include=None)
        codefresh_build_step_from_base_path(os.path.join(root_path, APPS_PATH), CF_BUILD_STEP_PARALLEL)

    # Remove useless steps
    codefresh['steps'] = {k: step for k, step in codefresh['steps'].items() if
                          'type' not in step or step['type'] != 'parallel' or (
                              step['steps'] if 'steps' in step else [])}

    # Add custom secrets to the environment of the deployment step
    deployment_step = codefresh["steps"].get("deployment")
    if deployment_step:
        environment = deployment_step.get("environment")
        if environment:
            for app_name, app in values_manual_deploy["apps"].items():
                if app.get("harness") and app["harness"].get("secrets"):
                    app_name = app_name.replace("_", "__")
                    for secret in app["harness"].get("secrets"):
                        secret_name = secret.replace("_", "__")
                        environment.append(
                            "CUSTOM_apps_%s_harness_secrets_%s=${{%s}}" % (app_name, secret_name, secret_name.upper()))

    codefresh_abs_path = os.path.join(os.getcwd(), DEPLOYMENT_PATH, out_filename)
    codefresh_dir = os.path.dirname(codefresh_abs_path)
    if not os.path.exists(codefresh_dir):
        os.makedirs(codefresh_dir)
    with open(codefresh_abs_path, 'w') as f:
        yaml.dump(codefresh, f)


def codefresh_template_spec(template_path, **kwargs):
    """
    Create Codefresh build specification
    :return:
    """

    build = get_template(template_path, True)

    build.update(kwargs)
    return build


def codefresh_app_publish_spec(app_name, build_tag, base_name=None):
    title = app_name.capitalize().replace('-', ' ').replace('/', ' ').replace('.', ' ').strip()

    step_spec = codefresh_template_spec(
        template_path=CF_TEMPLATE_PUBLISH_PATH,
        candidate="${{REGISTRY}}/%s:%s" % (get_image_name(app_name, base_name), build_tag or '${{DEPLOYMENT_TAG}}'),
        title=title,
    )
    if not build_tag:
        # if not build tag we are reusing old images and deploying on a production env
        step_spec['tags'].append('latest')
    return step_spec


def app_specific_tag_variable(app_name):
    return "${{ %s }}_${{DEPLOYMENT_PUBLISH_TAG}}" % app_name.replace('-', '_').upper()


def codefresh_app_build_spec(app_name, app_context_path, dockerfile_path="Dockerfile", base_name=None):
    logging.info('Generating build script for ' + app_name)
    title = app_name.capitalize().replace('-', ' ').replace('/', ' ').replace('.', ' ').strip()
    build = codefresh_template_spec(
        template_path=CF_BUILD_PATH,
        image_name=get_image_name(app_name, base_name),
        title=title,
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
    build['build_arguments'].append('REGISTRY=${{REGISTRY}}/%s/' % base_name)
    return build
