import os
from os.path import join, relpath, exists, dirname, basename
from cloudharness_model.models.git_dependency_config import GitDependencyConfig
import requests
import logging
from cloudharness_model.models.api_tests_config import ApiTestsConfig

import oyaml as yaml
import yaml.representer

from cloudharness_utils.testing.util import get_app_environment
from .models import HarnessMainConfig, ApplicationTestConfig, ApplicationHarnessConfig
from cloudharness_utils.constants import *
from .configurationgenerator import KEY_APPS, KEY_TASK_IMAGES, KEY_TEST_IMAGES
from .utils import check_docker_manifest_exists, find_dockerfiles_paths, get_app_relative_to_base_path, guess_build_dependencies_from_dockerfile, \
    get_image_name, get_template, dict_merge, app_name_from_path, clean_path
from cloudharness_utils.testing.api import get_api_filename, get_schemathesis_command, get_urls_from_api_file

logging.getLogger().setLevel(logging.INFO)

CLOUD_HARNESS_PATH = "cloud-harness"
ROLLOUT_CMD_TPL = "kubectl rollout status deployment/%s"

# Codefresh variables may need quotes: adjust yaml dump accordingly


def literal_presenter(dumper, data):
    if isinstance(data, str) and "\n" in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    if isinstance(data, str) and data.startswith('${{'):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, literal_presenter)


def get_main_domain(url):
    try:
        url = url.split("//")[1].split("/")[0]
        if "gitlab" in url:
            return "gitlab"
        if "bitbucket" in url:
            return "bitbucket"
        return "github"
    except:
        return "${{ DEFAULT_REPO }}"


def clone_step_spec(conf: GitDependencyConfig, context_path: str):
    return {
        "title": f"Cloning {os.path.basename(conf.url)} repository...",
        "type": "git-clone",
        "repo": conf.url,
        "revision": conf.branch_tag,
        "working_directory": join(context_path, "dependencies", conf.path or ""),
        "git": get_main_domain(conf.url)  # Cannot really tell what's the git config name, usually the name of the repo
    }


def write_env_file(helm_values: HarnessMainConfig, filename, registry_secret=None):
    env = {}
    logging.info("Create env file with image info %s", filename)

    def extract_tag(image_name):
        return image_name.split(":")[1] if ":" in image_name else "latest"

    def check_image_exists(name, image):
        tag = extract_tag(image)
        chunks = image.split(":")[0].split("/")
        registry = chunks[0] if "." in chunks[0] else "docker.io"
        image_name = "/".join(chunks[1::] if "." in chunks[0] else chunks[0::])
        exists = check_docker_manifest_exists(registry, image_name, tag, registry_secret=registry_secret)
        if exists:
            # TODO the hash might be the same but not the parent's hash
            env[app_specific_tag_variable(name) + "_EXISTS"] = 1
        else:
            env[app_specific_tag_variable(name) + "_NEW"] = 1

    for app in helm_values.apps.values():
        if app.harness and app.harness.deployment.image:
            env[app_specific_tag_variable(app.name)] = extract_tag(app.harness.deployment.image)
            check_image_exists(app.name, app.harness.deployment.image)

    for k, task_image in helm_values[KEY_TASK_IMAGES].items():
        env[app_specific_tag_variable(k)] = extract_tag(task_image)
        check_image_exists(k, task_image)

    for k, task_image in helm_values[KEY_TEST_IMAGES].items():
        env[app_specific_tag_variable(k)] = extract_tag(task_image)
        check_image_exists(k, task_image)

    logging.info("Writing env file %s", filename)
    with open(filename, 'w') as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")


def create_codefresh_deployment_scripts(root_paths, envs=(), include=(), exclude=(),
                                        template_name=CF_TEMPLATE_PATH, base_image_name=None,
                                        helm_values: HarnessMainConfig = None, save=True):
    """
    Entry point to create deployment scripts for codefresh: codefresh.yaml and helm chart
    """
    build_included = [app['harness']['name']
                      for app in helm_values['apps'].values() if 'harness' in app]
    out_filename = f"codefresh-{'-'.join(envs)}.yaml"

    if build_included:
        logging.info(
            'Including the following subpaths to the build: %s.', ', '
            .join(build_included)
        )

    if exclude:
        logging.info(
            'Excluding the following subpaths to the build: %s.', ', '
            .join(exclude)
        )

    codefresh = {}
    for e in envs:
        template_name = f"codefresh-template-{e}.yaml"
        codefresh = dict_merge(codefresh, get_template(template_name, True))

    steps = {}

    for root_path in root_paths:
        for e in envs:

            template_name = f"codefresh-template-{e}.yaml"
            template_path = join(
                root_path, DEPLOYMENT_CONFIGURATION_PATH, template_name)

            tpl = get_template(template_path)
            if tpl:
                logging.info("Codefresh template found: %s", template_path)
                codefresh = dict_merge(codefresh, tpl)

            if not 'steps' in codefresh:
                continue

            steps = codefresh['steps']

            def get_app_domain(app_config: ApplicationHarnessConfig):
                base_domain = [c for c in codefresh['steps']['prepare_deployment']['commands'] if 'harness-deployment' in c][0].split("-d ")[1].split(" ")[0]
                return f"https://{app_config.subdomain}.{base_domain}"

            def e2e_test_environment(app_config: ApplicationHarnessConfig, app_domain: str = None):
                if app_domain is None:
                    app_domain = get_app_domain(app_config)
                env = get_app_environment(app_config, app_domain, False)
                return [f"{k}={env[k]}" for k in env]

            def codefresh_steps_from_base_path(base_path, build_step, fixed_context=None, include=build_included, publish=True):

                for dockerfile_path in find_dockerfiles_paths(base_path):
                    dockerfile_relative_to_root = relpath(dockerfile_path, '.')
                    dockerfile_relative_to_base = get_app_relative_to_base_path(base_path, dockerfile_path)
                    app_name = app_name_from_path(dockerfile_relative_to_base)
                    app_key = app_name.replace("-", "_")
                    app_config: ApplicationHarnessConfig = app_key in helm_values.apps and helm_values.apps[
                        app_key].harness

                    if include and not any(
                        f"/{inc}/" in dockerfile_path or
                        dockerfile_path.endswith(f"/{inc}")
                            for inc in include):
                        # Skip not included apps
                        continue

                    if any(inc in dockerfile_path for inc in (list(exclude) + EXCLUDE_PATHS)):
                        # Skip excluded apps
                        continue

                    if app_config and not helm_values.apps[app_key].get('build', True):
                        continue

                    if app_config and app_config.dependencies and app_config.dependencies.git:
                        for dep in app_config.dependencies.git:
                            step_name = f"clone_{basename(dep.url).replace('.', '_')}_{basename(dockerfile_relative_to_root).replace('.', '_')}"
                            steps[CD_BUILD_STEP_DEPENDENCIES]['steps'][step_name] = clone_step_spec(dep, dockerfile_relative_to_root)

                    build = None
                    if build_step in steps:
                        build = codefresh_app_build_spec(
                            app_name=app_name,
                            app_context_path=relpath(
                                fixed_context, '.') if fixed_context else dockerfile_relative_to_root,
                            dockerfile_path=join(
                                relpath(
                                    dockerfile_path, root_path) if fixed_context else '',
                                "Dockerfile"),
                            base_name=base_image_name,
                            helm_values=helm_values,
                            dependencies=guess_build_dependencies_from_dockerfile(
                                join(dockerfile_path, "Dockerfile")
                            )
                        )

                        if not type(steps[build_step]['steps']) == dict:
                            steps[build_step]['steps'] = {}

                        steps[build_step]['steps'][app_name] = build

                    if CD_STEP_PUBLISH in steps and steps[CD_STEP_PUBLISH] and publish:
                        if not type(steps[CD_STEP_PUBLISH]['steps']) == dict:
                            steps[CD_STEP_PUBLISH]['steps'] = {}
                        steps[CD_STEP_PUBLISH]['steps']['publish_' + app_name] = codefresh_app_publish_spec(
                            app_name=app_name,
                            build_tag=build and build['tag'],
                            base_name=base_image_name
                        )

                    if CD_UNIT_TEST_STEP in steps and app_config:
                        add_unit_test_step(app_config)

                    if CD_API_TEST_STEP in steps and app_config and app_config.test.api.enabled:
                        tests_path = join(
                            base_path, dockerfile_relative_to_base, "test", API_TESTS_DIRNAME)
                        api_filename = get_api_filename(dockerfile_relative_to_base)
                        if app_config.subdomain:
                            server_urls = get_urls_from_api_file(
                                os.path.join(root_path, APPS_PATH, api_filename))
                            for app_domain in server_urls:
                                if "http" not in app_domain:
                                    app_domain = get_app_domain(
                                        app_config) + app_domain
                                steps[CD_API_TEST_STEP]['scale'][f"{app_name}_api_test"] = dict(
                                    title=f"{app_name} api test",
                                    volumes=api_test_volumes(clean_path(
                                        dockerfile_relative_to_root)),
                                    environment=e2e_test_environment(
                                        app_config, app_domain),
                                    commands=api_tests_commands(
                                        app_config, exists(tests_path), app_domain)
                                )

                    if CD_E2E_TEST_STEP in steps and app_config and app_config.test.e2e.enabled:
                        tests_path = join(
                            base_path, dockerfile_relative_to_base, "test", E2E_TESTS_DIRNAME)

                        if app_config.subdomain:

                            steps[CD_E2E_TEST_STEP]['scale'][f"{app_name}_e2e_test"] = dict(
                                title=f"{app_name} e2e test",
                                volumes=e2e_test_volumes(
                                    clean_path(dockerfile_relative_to_root), app_name),
                                environment=e2e_test_environment(app_config)
                            )

            def add_unit_test_step(app_config: ApplicationHarnessConfig):
                # Create a run step for each application with tests/unit.yaml file using the corresponding image built at the previous step

                test_config: ApplicationTestConfig = app_config.test
                app_name = app_config.name

                if test_config.unit.enabled and test_config.unit.commands:
                    tag = app_specific_tag_variable(app_name)
                    steps[CD_UNIT_TEST_STEP]['steps'][f"{app_name}_ut"] = dict(
                        title=f"Unit tests for {app_name}",
                        commands=test_config.unit.commands,
                        image=image_tag_with_variables(app_name, tag, base_image_name),
                    )

            if helm_values[KEY_TASK_IMAGES]:
                codefresh_steps_from_base_path(join(root_path, BASE_IMAGES_PATH), CD_BUILD_STEP_BASE,
                                               fixed_context=relpath(root_path, os.getcwd()), include=helm_values[KEY_TASK_IMAGES].keys())
                codefresh_steps_from_base_path(join(root_path, STATIC_IMAGES_PATH), CD_BUILD_STEP_STATIC,
                                               include=helm_values[KEY_TASK_IMAGES].keys())

                codefresh_steps_from_base_path(join(
                    root_path, APPS_PATH), CD_BUILD_STEP_PARALLEL)

            if CD_E2E_TEST_STEP in steps:
                name = "test-e2e"
                codefresh_steps_from_base_path(join(
                    root_path, TEST_IMAGES_PATH), CD_BUILD_STEP_TEST, include=(name,), publish=False)
                steps[CD_E2E_TEST_STEP]["image"] = image_tag_with_variables(name, app_specific_tag_variable(name), base_name=base_image_name)

            if CD_API_TEST_STEP in steps:
                name = "test-api"
                codefresh_steps_from_base_path(join(
                    root_path, TEST_IMAGES_PATH), CD_BUILD_STEP_TEST, include=(name,), fixed_context=relpath(root_path, os.getcwd()), publish=False)
                steps[CD_API_TEST_STEP]["image"] = image_tag_with_variables(name, app_specific_tag_variable(name), base_name=base_image_name)

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
                    for secret in [secret[0] for secret in app.harness.secrets.items() if secret[1] != ""]:
                        secret_name = secret.replace("_", "__")
                        arguments["custom_values"].append(
                            "apps_%s_harness_secrets_%s=${{%s}}" % (app_name.replace("_", "__"), secret_name, secret_name.upper()))

    cmds = codefresh['steps']['prepare_deployment']['commands']

    params = [p for inc in include for p in ["-i", inc]] +\
        [p for ex in exclude for p in ["-i", ex]]

    for i in range(len(cmds)):
        cmds[i] = cmds[i].replace("$ENV", "-".join(envs))
        cmds[i] = cmds[i].replace("$PARAMS", " ".join(params))
        cmds[i] = cmds[i].replace("$PATHS", " ".join(os.path.relpath(
            root_path, '.') for root_path in root_paths if DEFAULT_MERGE_PATH not in root_path))

    steps = codefresh["steps"]
    if CD_E2E_TEST_STEP in steps and not steps[CD_E2E_TEST_STEP]["scale"]:
        del steps[CD_E2E_TEST_STEP]
        if CD_BUILD_STEP_TEST in steps and 'test-e2e' in steps[CD_BUILD_STEP_TEST]["steps"]:
            del steps[CD_BUILD_STEP_TEST]["steps"]["test-e2e"]

    if CD_API_TEST_STEP in steps and not steps[CD_API_TEST_STEP]["scale"]:
        del steps[CD_API_TEST_STEP]
        if CD_BUILD_STEP_TEST in steps and 'test-api' in steps[CD_BUILD_STEP_TEST]["steps"]:
            del steps[CD_BUILD_STEP_TEST]["steps"]["test-api"]

    if CD_BUILD_STEP_TEST in steps and not steps[CD_BUILD_STEP_TEST]["steps"]:
        del steps[CD_BUILD_STEP_TEST]
        del steps[CD_WAIT_STEP]
    if CD_WAIT_STEP in steps:
        rollout_commands = steps[CD_WAIT_STEP]['commands']
        for app_key in helm_values[KEY_APPS]:
            app: ApplicationHarnessConfig = helm_values[KEY_APPS][app_key].harness
            if app.deployment.auto:
                rollout_commands.append(
                    ROLLOUT_CMD_TPL % app.deployment.name)
            if app.secured and helm_values.secured_gatekeepers:
                rollout_commands.append(
                    ROLLOUT_CMD_TPL % app.service.name + "-gk")
        # some time to the certificates to settle
        rollout_commands.append("sleep 60")

    if save:
        codefresh_abs_path = join(
            os.getcwd(), DEPLOYMENT_PATH, out_filename)
        codefresh_dir = dirname(codefresh_abs_path)
        if not exists(codefresh_dir):
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


def api_tests_commands(app_config: ApplicationHarnessConfig, run_custom_tests, api_url):
    api_config: ApiTestsConfig = app_config.test.api
    commands = []
    if api_config.autotest:
        commands.append(" ".join(get_schemathesis_command(
            get_api_filename(""), app_config, api_url)))
    if run_custom_tests:
        commands.append(f"pytest -v test/api")
    return commands


def e2e_test_volumes(app_relative_to_root, app_name, dirname=E2E_TESTS_DIRNAME):
    return [r"${{CF_REPO_NAME}}/" + f"{app_relative_to_root}/test/{dirname}:/home/test/__tests__/{app_name}"]


def api_test_volumes(app_relative_to_root):
    return [
        r"${{CF_REPO_NAME}}/" + f"{app_relative_to_root}:/home/test",
        "${{CF_REPO_NAME}}/deployment/helm/values.yaml:/opt/cloudharness/resources/allvalues.yaml"
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


def image_tag_with_variables(app_name, build_tag, base_name=""):
    return "${{REGISTRY}}/%s:${{%s}}" % (get_image_name(
        app_name, base_name), build_tag or '${{DEPLOYMENT_TAG}}')


def app_specific_tag_variable(app_name):
    return "%s_TAG" % app_name.replace('-', '_').upper().strip()


def codefresh_app_build_spec(app_name, app_context_path, dockerfile_path="Dockerfile", base_name=None, helm_values: HarnessMainConfig = {}, dependencies=None):
    logging.info('Generating build script for ' + app_name)
    title = app_name.capitalize().replace(
        '-', ' ').replace('/', ' ').replace('.', ' ').strip()
    build = codefresh_template_spec(
        template_path=CF_BUILD_PATH,
        image_name=get_image_name(app_name, base_name),
        title=title,
        working_directory='./' + app_context_path,
        dockerfile=dockerfile_path)

    tag = app_specific_tag_variable(app_name)
    build["tag"] = "${{%s}}" % tag

    specific_build_template_path = join(app_context_path, 'build.yaml')
    if exists(specific_build_template_path):
        logging.info("Specific build template found: %s" %
                     (specific_build_template_path))
        with open(specific_build_template_path) as f:
            build_specific = yaml.safe_load(f)

        build_specific.pop(
            'build_arguments') if 'build_arguments' in build_specific else []

    build['build_arguments'].append('REGISTRY=${{REGISTRY}}/%s/' % base_name)

    def add_arg_dependencies(dependencies):
        arg_dependencies = [f"{d.upper().replace('-', '_')}={image_tag_with_variables(d, app_specific_tag_variable(d), base_name)}" for
                            d in dependencies]
        build['build_arguments'].extend(arg_dependencies)

    values_key = app_name.replace('-', '_')
    if dependencies is not None:
        add_arg_dependencies(dependencies)
    elif values_key in helm_values.apps:
        try:
            add_arg_dependencies(
                helm_values.apps[values_key].harness.dependencies.build)
        except (KeyError, AttributeError):
            add_arg_dependencies(helm_values['task-images'])

    when_condition = existing_build_when_condition(tag)
    build["when"] = when_condition
    return build


def existing_build_when_condition(tag):
    """
    See https://codefresh.io/docs/docs/pipelines/conditional-execution-of-steps/#execute-steps-according-to-the-presence-of-a-variable
    the _EXISTS variable is added in the preparation step
    the _FORCE_BUILD variable may be added manually by the user to force the build of a specific image
    """
    is_built = tag + "_EXISTS"
    force_build = tag + "_FORCE_BUILD"
    when_condition = {
        "condition": {
            "any": {
                "buildDoesNotExist": "includes('${{%s}}', '{{%s}}') == true" % (is_built, is_built),
                "forceNoCache": "includes('${{%s}}', '{{%s}}') == false" % (force_build, force_build),
            }
        }
    }

    return when_condition
