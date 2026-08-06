import os
import re
from os.path import join, relpath, exists, dirname, basename, abspath
from cloudharness_model.models.git_dependency_config import GitDependencyConfig

import logging
from cloudharness_model.models.api_tests_config import ApiTestsConfig

import oyaml as yaml

from cloudharness_utils.testing.util import get_app_environment
from .models import HarnessMainConfig, ApplicationTestConfig, ApplicationHarnessConfig
from cloudharness_utils.constants import *
from .configurationgenerator import KEY_APPS, KEY_TASK_IMAGES, KEY_TEST_IMAGES
from .utils import check_image_exists_in_registry, find_dockerfiles_paths, get_app_relative_to_base_path, guess_build_dependencies_from_dockerfile, \
    get_template, dict_merge, app_name_from_path, clean_path, strip_registry_tag
from cloudharness_utils.testing.api import get_api_filename, get_schemathesis_command, get_urls_from_api_file

logging.getLogger().setLevel(logging.INFO)

CLOUD_HARNESS_PATH = "cloud-harness"
ROLLOUT_CMD_TPL = "kubectl rollout status deployment/%s"


def _to_codefresh_path(path: str) -> str:
    """Return the Codefresh-friendly path for any path pointing into the cloud-harness tree.

    In Codefresh pipelines cloud-harness is always cloned into ./cloud-harness.
    Resolves *path* to a relative path from CWD, then skips over any leading '..'
    components. If the first real directory name after those is 'cloud-harness',
    the path is rewritten to start with 'cloud-harness/' — regardless of how many
    levels up cloud-harness lives or whether an absolute path was passed.
    All other paths are returned unchanged (as their relpath from CWD).
    """
    rel = os.path.relpath(os.path.abspath(path), '.')
    parts = rel.replace('\\', '/').split('/')
    # Skip all leading '..' components
    i = 0
    while i < len(parts) and parts[i] == '..':
        i += 1
    # If we crossed at least one '..' and the next component is cloud-harness, rewrite
    if i > 0 and i < len(parts) and parts[i] == CLOUD_HARNESS_PATH:
        return '/'.join([CLOUD_HARNESS_PATH] + parts[i + 1:])
    return rel

# Codefresh variables may need quotes: adjust yaml dump accordingly


def literal_presenter(dumper, data):
    if isinstance(data, str) and "\n" in data:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    if isinstance(data, str) and data.startswith('${{'):
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style="'")
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)


yaml.add_representer(str, literal_presenter)


def clean_step_key(s: str) -> str:
    """Normalize a string to a valid Codefresh step key (alphanumeric + underscore)."""
    return re.sub(r'[^a-zA-Z0-9_]', '_', s)


def dockerfile_selector_candidates(base_path: str, dockerfile_path: str) -> set[str]:
    """Return stable identifiers that may be used with include/exclude selectors."""
    relative_to_base = get_app_relative_to_base_path(base_path, dockerfile_path)
    parent_name = relative_to_base.split("/")[0] if relative_to_base else ""
    return {
        candidate for candidate in (
            relative_to_base,
            app_name_from_path(relative_to_base),
            parent_name,
        ) if candidate
    }


def path_contains_excluded_segment(path: str, excluded_segments) -> bool:
    normalized_path = f"/{path.replace(os.path.sep, '/')}/"
    return any(f"/{segment}/" in normalized_path for segment in excluded_segments)


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


def write_env_file(helm_values: HarnessMainConfig, filename, image_cache_endpoint_url=None):
    env = {}
    logging.info("Create env file with image info %s", filename)

    def extract_tag(image_name):
        return image_name.split(":")[1] if ":" in image_name else "latest"

    def check_image_exists(name, image):
        tag = extract_tag(image)
        chunks = image.split(":")[0].split("/")
        registry = chunks[0] if "." in chunks[0] else "docker.io"
        image_name = "/".join(chunks[1::] if "." in chunks[0] else chunks[0::])
        exists = check_image_exists_in_registry(registry, image_name, tag, endpoint_url=image_cache_endpoint_url)
        logging.info("Image %s exists check: %s", image, exists)
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

    if base_image_name is None:
        base_image_name = helm_values['name']

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

    for root_path in root_paths:
        for e in envs:
            template_name = f"codefresh-template-{e}.yaml"
            template_path = join(root_path, DEPLOYMENT_CONFIGURATION_PATH, template_name)
            tpl = get_template(template_path)
            if tpl:
                logging.info("Codefresh template found: %s", template_path)
                codefresh = dict_merge(codefresh, tpl)

    steps = {}
    build_steps = {}
    has_overrides = any(DEFAULT_MERGE_PATH in root_path for root_path in root_paths)

    if 'steps' in codefresh:
        steps = codefresh['steps']

    for i in range(len(root_paths)):

        root_path = root_paths[i]
        base_name = base_image_name

        if not steps:
            continue

        def get_app_domain(app_config: ApplicationHarnessConfig):
            base_domain = [c for c in codefresh['steps']['prepare_deployment']['commands'] if 'harness-deployment' in c][0].split("-d ")[1].split(" ")[0]
            return f"https://{app_config.subdomain}.{base_domain}"

        def e2e_test_environment(app_config: ApplicationHarnessConfig, app_domain: str = None):
            if app_domain is None:
                app_domain = get_app_domain(app_config)
            env = get_app_environment(app_config, app_domain, False)
            return [f"{k}={env[k]}" for k in env]

        def codefresh_app_build_spec(app_name, full_image_name, app_context_path, dockerfile_path="Dockerfile",
                                     helm_values: HarnessMainConfig = {}, dependencies=None, additional_tags=()):
            logging.info('Generating build script for ' + app_name)
            title = app_name.capitalize().replace(
                '-', ' ').replace('/', ' ').replace('.', ' ').strip()

            build = codefresh_template_spec(
                template_path=CF_BUILD_PATH,
                image_name=strip_registry_tag(
                    full_image_name, helm_values.registry.name
                ),
                title=title,
                working_directory='./' + _to_codefresh_path(app_context_path),
                dockerfile=dockerfile_path)

            tag = app_specific_tag_variable(app_name)
            build["tags"] = [
                "${{%s}}" % tag,
                "${{DEPLOYMENT_PUBLISH_TAG}}-dev",
                "${{CF_BRANCH_TAG_NORMALIZED_LOWER_CASE}}",
                *additional_tags,
            ]

            specific_build_template_path = join(app_context_path, 'build.yaml')
            if exists(specific_build_template_path):
                logging.info("Specific build template found: %s" %
                             (specific_build_template_path))
                with open(specific_build_template_path) as f:
                    build_specific = yaml.safe_load(f)

                build_specific.pop(
                    'build_arguments') if 'build_arguments' in build_specific else []

            build['dependencies'] = dependencies

            def get_other_image_name(app_name):
                full_image_name = helm_values.apps[app_name].image if app_name in helm_values.apps \
                    else helm_values[KEY_TASK_IMAGES][app_name] if app_name in helm_values[KEY_TASK_IMAGES] \
                    else f"{base_name}/{app_name}"
                return image_tag_with_variables(full_image_name, helm_values.registry.name, app_specific_tag_variable(app_name))

            def add_arg_dependencies(dependencies):
                arg_dependencies = [f"{d.upper().replace('-', '_')}={get_other_image_name(d)}"
                                    for d in dependencies]
                build['build_arguments'].extend(arg_dependencies)

            values_key = app_name
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

        def resolve_dockerfile_name(dockerfile_dir):
            """Return the dockerfile filename, preferring [env].Dockerfile over Dockerfile."""
            for env_name in envs:
                env_dockerfile = os.path.join(dockerfile_dir, f'{env_name}.Dockerfile')
                if exists(env_dockerfile):
                    return f'{env_name}.Dockerfile'
            return 'Dockerfile'

        def codefresh_steps_from_base_path(base_path, fixed_context=None, include=build_included, publish=True):
            found = False
            for dockerfile_path in find_dockerfiles_paths(base_path):
                dockerfile_relative_to_root = relpath(dockerfile_path, '.')
                dockerfile_relative_to_base = get_app_relative_to_base_path(base_path, dockerfile_path)
                selector_candidates = dockerfile_selector_candidates(base_path, dockerfile_path)
                app_name = app_name_from_path(dockerfile_relative_to_base)
                app_key = app_name
                app_config: ApplicationHarnessConfig = app_key in helm_values.apps and helm_values.apps[app_key].harness
                full_image_name = helm_values.apps[app_key].image if app_key in helm_values.apps\
                    else helm_values[KEY_TASK_IMAGES][app_key] if app_key in helm_values[KEY_TASK_IMAGES]\
                    else f"{base_name}/{app_name}"

                if include and not any(inc in selector_candidates for inc in include):
                    # Skip not included apps
                    continue

                if any(ex in selector_candidates for ex in exclude):
                    # Skip explicitly excluded apps/images
                    continue

                if path_contains_excluded_segment(dockerfile_relative_to_root, EXCLUDE_PATHS):
                    # Skip excluded apps
                    continue

                if app_config and not helm_values.apps[app_key].get('build', True):
                    continue

                if app_config and app_config.dependencies and app_config.dependencies.git and DEFAULT_MERGE_PATH not in root_path:
                    for dep in app_config.dependencies.git:
                        step_name = clean_step_key(f"clone_{basename(dep.url)}_{dep.branch_tag}_{basename(dockerfile_relative_to_root)}")
                        steps[CD_STEP_CLONE_DEPENDENCIES]['steps'][step_name] = clone_step_spec(dep, dockerfile_relative_to_root)

                build = None
                if CD_BUILD_STEP_PARALLEL in steps:
                    dockerfile_name = resolve_dockerfile_name(dockerfile_path)
                    dependencies = guess_build_dependencies_from_dockerfile(
                        join(dockerfile_path, dockerfile_name)
                    )
                    build = codefresh_app_build_spec(
                        app_name=app_name,
                        full_image_name=full_image_name,
                        app_context_path=relpath(
                            fixed_context, '.') if fixed_context else dockerfile_relative_to_root,
                        dockerfile_path=join(
                            relpath(
                                dockerfile_path, root_path) if fixed_context else '',
                            dockerfile_name),
                        helm_values=helm_values,
                        dependencies=dependencies,
                        additional_tags=('latest',) if not publish else ()
                    )

                    build_steps[app_name] = build
                    found = True

                if CD_STEP_PUBLISH in steps and steps[CD_STEP_PUBLISH] and publish:
                    if not type(steps[CD_STEP_PUBLISH]['steps']) == dict:
                        steps[CD_STEP_PUBLISH]['steps'] = {}
                    image_name = helm_values.apps[app_name].image if app_name in helm_values.apps else helm_values[KEY_TASK_IMAGES].get(app_name, None)
                    if app_name:
                        steps[CD_STEP_PUBLISH]['steps']['publish_' + app_name] = codefresh_app_publish_spec(
                            full_src_image=image_name,
                            build_tag=build and build['tags'][0],
                            registry=helm_values.registry.name,
                            app_name=app_name
                        )
                        found = True
                    else:
                        logging.warning("Detected image %s which is not part of the deployment", app_name)

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
                        found = True

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
                        found = True
            return found

        def add_unit_test_step(app_config: ApplicationHarnessConfig):
            # Create a run step for each application with tests/unit.yaml file using the corresponding image built at the previous step

            test_config: ApplicationTestConfig = app_config.test
            app_name = app_config.name
            full_image_name = helm_values.apps[app_name].image if app_name in helm_values.apps else helm_values[KEY_TASK_IMAGES][app_name]

            if test_config.unit.enabled and test_config.unit.commands:
                tag = app_specific_tag_variable(app_name)
                steps[CD_UNIT_TEST_STEP]['steps'][f"{app_name}_ut"] = dict(
                    title=f"Unit tests for {app_name}",
                    commands=test_config.unit.commands,
                    image=image_tag_with_variables(full_image_name, helm_values.registry.name, tag),
                )

        if helm_values[KEY_TASK_IMAGES]:
            codefresh_steps_from_base_path(join(root_path, BASE_IMAGES_PATH),
                                           fixed_context=relpath(root_path, os.getcwd()), include=helm_values[KEY_TASK_IMAGES].keys())
            codefresh_steps_from_base_path(join(root_path, STATIC_IMAGES_PATH),
                                           include=helm_values[KEY_TASK_IMAGES].keys())
            codefresh_steps_from_base_path(join(root_path, APPS_PATH), include=helm_values[KEY_TASK_IMAGES].keys())
        codefresh_steps_from_base_path(join(root_path, APPS_PATH), include=build_included)

    # Search all root_paths for test images after scale is fully populated from all apps.
    # Test images (test-e2e, test-api) may live in a different root_path than the apps that use them.
    if CD_E2E_TEST_STEP in steps and steps[CD_E2E_TEST_STEP].get("scale"):
        name = "test-e2e"
        for root_path in root_paths:
            if codefresh_steps_from_base_path(join(root_path, TEST_IMAGES_PATH), include=(name,), publish=False):
                steps[CD_E2E_TEST_STEP]["image"] = image_tag_with_variables(
                    f"{base_image_name}/{name}", helm_values.registry.name, app_specific_tag_variable(name))

    if CD_API_TEST_STEP in steps and steps[CD_API_TEST_STEP].get("scale"):
        name = "test-api"
        for root_path in root_paths:
            if codefresh_steps_from_base_path(join(root_path, TEST_IMAGES_PATH), include=(name,), fixed_context=relpath(root_path, os.getcwd()), publish=False):
                steps[CD_API_TEST_STEP]["image"] = image_tag_with_variables(
                    f"{base_image_name}/{name}", helm_values.registry.name, app_specific_tag_variable(name))

    if build_steps:

        def adjust_build_steps(index):
            """
            Adjust the build steps to be parallel
            """
            new_step = dict(**steps[CD_BUILD_STEP_PARALLEL])
            new_step['title'] = "Build parallel step %d" % (index + 1)
            new_step['steps'] = {}
            steps[f"{CD_BUILD_STEP_PARALLEL}_{index}"] = new_step
            remaining_steps = set(build_steps.keys())
            for step_name in remaining_steps:
                step = build_steps[step_name]
                if not step["dependencies"] or not any(d for d in step["dependencies"] if d in remaining_steps):
                    new_step['steps'][step_name] = step
                    del step["dependencies"]
                    del build_steps[step_name]

            if build_steps:
                adjust_build_steps(index + 1)
        adjust_build_steps(0)

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
                            'apps_%s_harness_secrets_%s="${{%s}}"' % (app_name.replace("_", "__"), secret_name, secret_name.upper())
                        )
            for app_name, app in helm_values.apps.items():
                if app.harness.database and app.harness.database.get("connect_string") == "":
                    var_name = f"{app_name.upper().replace('-', '_')}_DB_CONNECT_STRING"
                    arguments["custom_values"].append(
                        "apps_%s_harness_database_connect__string=\"${{%s}}\"" % (
                            app_name.replace("_", "__"), var_name)
                    )
            # Add registry secret value secret if registry secret name is set
            registry = getattr(helm_values, "registry", None)
            secret = getattr(registry, "secret", None)
            registry_secret_name = getattr(secret, "name", None)
            if registry_secret_name:
                arguments["custom_values"].append(
                    'registry_secret_value="${{K8S_SA_JSON}}"'
                )

    cmds = codefresh['steps']['prepare_deployment']['commands']

    params = [p for inc in include for p in ["-i", inc]] +\
        [p for ex in exclude for p in ["-i", ex]]

    for i in range(len(cmds)):
        cmds[i] = cmds[i].replace("$ENV", "-".join(envs))
        cmds[i] = cmds[i].replace("$PARAMS", " ".join(params))
        cmds[i] = cmds[i].replace("$PATHS", " ".join(
            _to_codefresh_path(root_path)
            for root_path in root_paths if DEFAULT_MERGE_PATH not in root_path))

    steps = codefresh["steps"]
    if CD_E2E_TEST_STEP in steps and not steps[CD_E2E_TEST_STEP]["scale"]:
        del steps[CD_E2E_TEST_STEP]

    if CD_API_TEST_STEP in steps and not steps[CD_API_TEST_STEP]["scale"]:
        del steps[CD_API_TEST_STEP]

    if CD_E2E_TEST_STEP not in steps and not CD_API_TEST_STEP not in steps and CD_WAIT_STEP in steps:
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
                    ROLLOUT_CMD_TPL % app.subdomain + "-gk")
        # some time to the certificates to settle
        rollout_commands.append("sleep 60")

    codefresh['steps'] = sort_parallel_steps(codefresh['steps'])

    if 'stages' in codefresh:
        codefresh['steps'] = order_steps_by_stage(codefresh['steps'], codefresh['stages'])

    if save:
        codefresh_abs_path = join(
            os.getcwd(), DEPLOYMENT_PATH, out_filename)
        codefresh_dir = dirname(codefresh_abs_path)
        if not exists(codefresh_dir):
            os.makedirs(codefresh_dir)
        from ruamel.yaml.scalarstring import SingleQuotedScalarString

        deployment_step = codefresh.get("steps", {}).get("deployment", {})
        arguments = deployment_step.get("arguments", {})
        if "custom_values" in arguments:
            arguments["custom_values"] = [
                SingleQuotedScalarString(v) if isinstance(v, str) else v
                for v in arguments["custom_values"]
            ]

        from ruamel.yaml import YAML
        ryaml = YAML()
        ryaml.default_flow_style = False
        with open(codefresh_abs_path, 'w') as f:
            ryaml.dump(codefresh, f)
    return codefresh


def sort_parallel_steps(steps: dict) -> dict:
    """Sort the sub-steps of every parallel step alphabetically by name.

    Top-level step order is not affected; only the inner ``steps`` dict of each
    parallel step is sorted.
    """
    result = {}
    for name, step in steps.items():
        if step and isinstance(step, dict) and step.get('type') == 'parallel' and 'steps' in step:
            step = dict(step)
            step['steps'] = dict(sorted(step['steps'].items()))
        result[name] = step
    return result


def order_steps_by_stage(steps: dict, stages: list) -> dict:
    """Re-order a flat steps dict so that steps belonging to earlier stages appear first.

    Relative order within each stage is preserved (stable sort). Steps that have no
    recognised stage are moved to the end, keeping their relative order.
    """
    stage_order = {stage: i for i, stage in enumerate(stages)}
    no_stage_index = len(stages)

    def stage_key(item):
        step = item[1]
        if step and isinstance(step, dict):
            stage = step.get('stage')
            if stage is not None:
                return stage_order.get(stage, no_stage_index)
        return no_stage_index

    return dict(sorted(steps.items(), key=stage_key))


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


def codefresh_app_publish_spec(app_name, full_src_image, build_tag, registry):
    title = app_name.capitalize().replace(
        '-', ' ').replace('/', ' ').replace('.', ' ').strip()

    step_spec = codefresh_template_spec(
        template_path=CF_TEMPLATE_PUBLISH_PATH,
        candidate="${{REGISTRY}}/%s:%s" % (strip_registry_tag(
            full_src_image, registry), build_tag or '${{DEPLOYMENT_TAG}}'),
        title=title,
    )
    step_spec["when"] = existing_publish_when_condition(
        app_specific_publish_skip_variable(app_name)
    )
    step_spec['tags'].append('latest')
    return step_spec


def image_tag_with_variables(app_name, registry_name, build_tag):
    return "${{REGISTRY}}/%s:${{%s}}" % (strip_registry_tag(
        app_name, registry_name), build_tag or '${{DEPLOYMENT_TAG}}')


def app_specific_tag_variable(app_name):
    return "%s_TAG" % app_name.replace('-', '_').upper().strip()


def app_specific_publish_skip_variable(app_name):
    return "%s_PUBLISH_SKIP" % app_name.replace('-', '_').upper().strip()


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


def existing_publish_when_condition(skip_publish_variable):
    return {
        "condition": {
            "all": {
                "skipPublish": "includes('${{%s}}', '{{%s}}') == true" % (
                    skip_publish_variable, skip_publish_variable
                ),
            }
        }
    }
