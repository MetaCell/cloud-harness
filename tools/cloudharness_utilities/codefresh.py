import os
from re import template

from .models import HarnessMainConfig, ApplicationHarnessConfig
import oyaml as yaml
import yaml.representer

import logging

from .constants import *
from .helm import KEY_APPS, KEY_TASK_IMAGES, collect_helm_values
from .utils import find_dockerfiles_paths, image_name_from_dockerfile_path, \
    get_image_name, get_template, merge_to_yaml_file, dict_merge, app_name_from_path

logging.getLogger().setLevel(logging.INFO)

CLOUD_HARNESS_PATH = "cloud-harness"
ROLLOUT_CMD_TPL = "kubectl -n test-${{CF_REPO_NAME}}-${{CF_SHORT_REVISION}} rollout status deployment/%s"

# Codefresh variables may need quotes: adjust yaml dump accordingly


def literal_presenter(dumper, data):
    if isinstance(data, str) and "\n" in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    if isinstance(data, str) and data.startswith('${{'):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, literal_presenter)


def create_codefresh_deployment_scripts(root_paths, envs=(), include=(), exclude=(),
                                        template_name=CF_TEMPLATE_PATH, base_image_name=None,
                                        helm_values: HarnessMainConfig = None, save=True):
    """
    Entry point to create deployment scripts for codefresh: codefresh.yaml and helm chart
    """

    out_filename = f"codefresh-{'-'.join(envs)}.yaml"

    if include:
        logging.info(
            'Including the following subpaths to the build: %s.', ', '
            .join(include)
        )

    if exclude:
        logging.info(
            'Excluding the following subpaths to the build: %s.', ', '
            .join(exclude)
        )

    codefresh = {}

    for root_path in root_paths:
        for e in envs:
            template_name = f"codefresh-template-{e}.yaml"
            template_path = os.path.join(
                root_path, DEPLOYMENT_CONFIGURATION_PATH, template_name)

            tpl = get_template(template_path, True)
            if tpl:
                logging.info("Codefresh template found: %s", template_path)
                tpl = get_template(template_path, True)
                codefresh = dict_merge(codefresh, tpl)

            if not 'steps' in codefresh:
                continue

            steps = codefresh['steps']

            def codefresh_steps_from_base_path(base_path, build_step, fixed_context=None, include=include):

                for dockerfile_path in find_dockerfiles_paths(base_path):
                    app_relative_to_root = os.path.relpath(
                        dockerfile_path, '.')
                    app_relative_to_base = os.path.relpath(
                        dockerfile_path, base_path)
                    app_name = app_name_from_path(app_relative_to_base)

                    if include and not any(
                            f"/{inc}/" in dockerfile_path or dockerfile_path.endswith(f"/{inc}") for inc in include):
                        # Skip not included apps
                        continue

                    if any(inc in dockerfile_path for inc in (list(exclude) + EXCLUDE_PATHS)):
                        # Skip excluded apps
                        continue

                    build = None
                    if CD_BUILD_STEP_BASE in steps:
                        build = codefresh_app_build_spec(
                            app_name=app_name,
                            app_context_path=os.path.relpath(
                                fixed_context, '.') if fixed_context else app_relative_to_root,
                            dockerfile_path=os.path.join(
                                os.path.relpath(
                                    dockerfile_path, root_path) if fixed_context else '',
                                "Dockerfile"),
                            base_name=base_image_name,
                            helm_values=helm_values
                        )

                        if not type(steps[build_step]['steps']) == dict:
                            steps[build_step]['steps'] = {}

                        steps[build_step]['steps'][app_name] = build

                    if CD_UNIT_TEST_STEP in steps:
                        add_unit_test_step(base_path, app_relative_to_base, app_name)


                    if CD_E2E_TEST_STEP in steps:
                        # Create a run step for each application with tests/unit.yaml file using the corresponding image built at the previous step
                        tests_path = os.path.join(
                            base_path, app_relative_to_base, "test", E2E_TESTS_DIRNAME)
                        if os.path.exists(tests_path) and helm_values.apps[app_name].harness.subdomain:
                            
                            steps[CD_E2E_TEST_STEP]['scale'][f"{app_name}_e2e_test"] = dict(
                                volumes=e2e_test_volumes(app_relative_to_root, app_name),
                                environment=e2e_test_environment(helm_values.apps[app_name].harness.subdomain)
                            )

                    if CD_API_TEST_STEP in steps :
                        # Create a run step for each application with tests/unit.yaml file using the corresponding image built at the previous step
                        tests_path = os.path.join(
                            base_path, app_relative_to_base, "test", API_TESTS_DIRNAME)
                        if os.path.exists(tests_path) and helm_values.apps[app_name].harness.subdomain:

                            
                            steps[CD_API_TEST_STEP]['scale'][f"{app_name}_api_test"] = dict(
                                volumes=e2e_test_volumes(app_relative_to_root, app_name),
                                environment=e2e_test_environment(helm_values.apps[app_name].harness.subdomain)
                            )                        

                    if CD_STEP_PUBLISH in steps and steps[CD_STEP_PUBLISH]:
                        if not type(steps[CD_STEP_PUBLISH]['steps']) == dict:
                            steps[CD_STEP_PUBLISH]['steps'] = {}
                        steps[CD_STEP_PUBLISH]['steps']['publish_' + app_name] = codefresh_app_publish_spec(
                            app_name=app_name,
                            build_tag=build and build['tag'],
                            base_name=base_image_name
                        )

            def add_unit_test_step(base_path, app_relative_to_base, app_name):
                # Create a run step for each application with tests/unit.yaml file using the corresponding image built at the previous step
                unittests_spec_path = os.path.join(base_path, app_relative_to_base, "test", UNITTEST_FNAME)
                if os.path.exists(unittests_spec_path):
                    unittest_config = get_template(unittests_spec_path)
                    steps[CD_UNIT_TEST_STEP]['steps'][f"{app_name}_ut"] = dict(
                                title=f"Unit tests for {app_name}",
                                commands=unittest_config['commands'],
                                image=r"${{%s}}" % app_name
                            )
            
            def create_k8s_rollout_commands():
                rollout_commands = steps[CD_WAIT_STEP]['commands']
                for app_key in helm_values[KEY_APPS]:
                    app: ApplicationHarnessConfig = helm_values[KEY_APPS][app_key].harness
                    if app.deployment.auto:
                        rollout_commands.append(
                                        ROLLOUT_CMD_TPL % app.deployment.name)
                    if app.secured and helm_values.secured_gatekeepers:
                        rollout_commands.append(
                                        ROLLOUT_CMD_TPL % app.service.name + "-gk")

            codefresh_steps_from_base_path(os.path.join(root_path, BASE_IMAGES_PATH), CD_BUILD_STEP_BASE,
                                           fixed_context=os.path.relpath(root_path, os.getcwd()), include=helm_values[KEY_TASK_IMAGES].keys())
            codefresh_steps_from_base_path(os.path.join(root_path, STATIC_IMAGES_PATH), CD_BUILD_STEP_STATIC,
                                           include=helm_values[KEY_TASK_IMAGES].keys())
            codefresh_steps_from_base_path(os.path.join(
                root_path, APPS_PATH), CD_BUILD_STEP_PARALLEL)

            if CD_WAIT_STEP in steps:
                create_k8s_rollout_commands()
            if CD_E2E_TEST_STEP in steps or CD_API_TEST_STEP in steps:
                codefresh_steps_from_base_path(os.path.join(
                    root_path, TEST_IMAGES_PATH), CD_BUILD_STEP_STATIC, include=())

    if not codefresh:
        logging.warning(
            "No template file found. Codefresh script not created.")
        return

    # Remove useless steps
    codefresh['steps'] = {k: step for k, step in steps.items() if step and
                          ('type' not in step or step['type'] != 'parallel' or (
                              step['steps'] if 'steps' in step else []))}

    # Add custom secrets to the environment of the deployment step
    deployment_step = codefresh["steps"].get("deployment")
    if deployment_step:
        arguments = deployment_step.get("arguments")
        if arguments:
            if "custom_values" not in arguments:
                arguments["custom_values"] = []
            for app_name, app in helm_values.apps.items():
                if app.harness.secrets:
                    
                    for secret in [secret[0] for secret in app.harness.secrets.items() if secret[1]]:
                        secret_name = secret
                        arguments["custom_values"].append(
                            "apps.%s.harness.secrets.%s=${{%s}}" % (app_name, secret_name, secret_name.upper()))

    cmds = steps['prepare_deployment']['commands']
    for i in range(len(cmds)):
        cmds[i] = cmds[i].replace("$ENV", "-".join(envs))
        if include:
            cmds[i] = cmds[i].replace("$INCLUDE", "-i " + " -i ".join(include))

    if save:
        codefresh_abs_path = os.path.join(
            os.getcwd(), DEPLOYMENT_PATH, out_filename)
        codefresh_dir = os.path.dirname(codefresh_abs_path)
        if not os.path.exists(codefresh_dir):
            os.makedirs(codefresh_dir)
        with open(codefresh_abs_path, 'w') as f:
            yaml.dump(codefresh, f)
    return codefresh


def codefresh_template_spec(template_path, **kwargs):
    """
    Create Codefresh build specification
    :return:
    """

    build = get_template(template_path, True)

    build.update(kwargs)
    return build


def e2e_test_volumes(app_relative_to_root, app_name):
    return [r"${{CF_REPO_NAME}}/" + f"{app_relative_to_root}/test/{E2E_TESTS_DIRNAME}:/home/test/__tests__/{app_name}"]


def e2e_test_environment(app_subdomain):
    return [
        f"APP_URL=https://{app_subdomain}." + r"${{CF_SHORT_REVISION}}.${{DOMAIN}}"
    ]


def codefresh_app_publish_spec(app_name, build_tag, base_name=None):
    title = app_name.capitalize().replace(
        '-', ' ').replace('/', ' ').replace('.', ' ').strip()

    step_spec = codefresh_template_spec(
        template_path=CF_TEMPLATE_PUBLISH_PATH,
        candidate="${{REGISTRY}}/%s:%s" % (get_image_name(
            app_name, base_name), build_tag or '${{DEPLOYMENT_TAG}}'),
        title=title,
    )
    if not build_tag:
        # if not build tag we are reusing old images and deploying on a production env
        step_spec['tags'].append('latest')
    return step_spec


def app_specific_tag_variable(app_name):
    return "${{ %s }}_${{DEPLOYMENT_PUBLISH_TAG}}" % app_name.replace('-', '_').upper()


def codefresh_app_build_spec(app_name, app_context_path, dockerfile_path="Dockerfile", base_name=None, helm_values: HarnessMainConfig = {}):
    logging.info('Generating build script for ' + app_name)
    title = app_name.capitalize().replace(
        '-', ' ').replace('/', ' ').replace('.', ' ').strip()
    build = codefresh_template_spec(
        template_path=CF_BUILD_PATH,
        image_name=get_image_name(app_name, base_name),
        title=title,
        working_directory='./' + app_context_path,
        dockerfile=dockerfile_path)

    specific_build_template_path = os.path.join(app_context_path, 'build.yaml')
    if os.path.exists(specific_build_template_path):
        logging.info("Specific build template found: %s" %
                     (specific_build_template_path))
        with open(specific_build_template_path) as f:
            build_specific = yaml.safe_load(f)

        build_args = build_specific.pop(
            'build_arguments') if 'build_arguments' in build_specific else []

    build['build_arguments'].append('REGISTRY=${{REGISTRY}}/%s/' % base_name)

    values_key = app_name.replace('-', '_')
    try:
        dep_list = helm_values.apps[values_key].harness.dependencies.build
        dependencies = [f"{d.upper().replace('-', '_')}=${{{{REGISTRY}}}}/{get_image_name(d, base_name)}:{build['tag']}" for
                        d in dep_list]
    except (KeyError, AttributeError):
        dependencies = [f"{d.upper().replace('-', '_')}=${{{{REGISTRY}}}}/{get_image_name(d, base_name)}:{build['tag']}" for
                        d in helm_values['task-images']]
    build['build_arguments'].extend(dependencies)

    return build
