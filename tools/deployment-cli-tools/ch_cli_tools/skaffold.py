import os
import logging
import json
import time

from os.path import join, relpath, basename, exists, abspath
from cloudharness_model import ApplicationTestConfig, HarnessMainConfig, GitDependencyConfig

from cloudharness_utils.constants import APPS_PATH, DEPLOYMENT_CONFIGURATION_PATH, \
    BASE_IMAGES_PATH, STATIC_IMAGES_PATH, HELM_ENGINE, COMPOSE_ENGINE
from .helm import KEY_APPS, KEY_HARNESS, KEY_DEPLOYMENT, KEY_TASK_IMAGES
from .utils import get_template, dict_merge, find_dockerfiles_paths, app_name_from_path, yaml, \
    find_file_paths, guess_build_dependencies_from_dockerfile, get_json_template, get_image_name

from . import HERE


def relpath_if(p1, p2):
    if os.path.isabs(p1):
        return p1
    return relpath(p1, p2)


def get_all_images(helm_values: HarnessMainConfig) -> dict[str, str]:
    all_images = {**helm_values[KEY_TASK_IMAGES]}
    for app_name, app in helm_values.apps.items():
        if app.harness.deployment and app.harness.deployment.image:
            all_images[app_name] = app.harness.deployment.image
    return all_images


def create_skaffold_configuration(root_paths, helm_values: HarnessMainConfig, output_path='.', manage_task_images=True, backend_deploy=HELM_ENGINE):
    backend = backend_deploy or HELM_ENGINE
    template_name = 'skaffold-template.yaml'
    skaffold_conf = get_template(template_name, True)
    apps = helm_values.apps
    artifacts = {}
    overrides = {}

    all_images = get_all_images(helm_values)

    def remove_tag(image_name):
        return image_name.split(":")[0]

    def get_image_tag(name):
        return remove_tag(all_images[name])

    builds = {}

    def build_artifact(
        app_name: str,
        context_path: str,
        requirements: list[str] = None,
        dockerfile_path: str = '',
        additional_build_args: dict[str, str] = None,
    ) -> dict:
        build_args = {
            'DEBUG': 'true' if helm_values.local or helm_values.debug else ''
        }

        if additional_build_args:
            build_args.update(additional_build_args)

        image_name = get_image_tag(app_name)

        artifact_spec = {
            'image': image_name,
            'context': context_path,
            'docker': {
                'dockerfile': join(dockerfile_path, 'Dockerfile'),
                'buildArgs': build_args,
                'ssh': 'default'
            }
        }
        if requirements:
            artifact_spec['requires'] = [{'image': get_image_tag(req), 'alias': req.replace('-', '_').upper()} for req
                                         in requirements]

        return artifact_spec

    base_images = set()

    def process_build_dockerfile(
        dockerfile_path: str,
        root_path: str,
        global_context: bool = False,
        requirements: list[str] = None,
        app_name: str = None
    ) -> None:
        if app_name is None:
            app_name = app_name_from_path(basename(dockerfile_path))
        app_key = app_name
        if app_key in helm_values.apps and not helm_values.apps[app_key]['build']:
            return
        if app_name in helm_values[KEY_TASK_IMAGES] or app_key in helm_values.apps:
            context_path = relpath_if(root_path, output_path) if global_context else relpath_if(dockerfile_path, output_path)

            builds[app_name] = context_path
            base_images.add(get_image_name(app_name))

            artifacts[app_name] = build_artifact(
                app_name,
                context_path,
                dockerfile_path=relpath(dockerfile_path, output_path),
                requirements=requirements or guess_build_dependencies_from_dockerfile(dockerfile_path),
                additional_build_args=get_additional_build_args(helm_values, app_key),
            )

            if app_key in helm_values.apps and helm_values.apps[app_key].harness.dependencies and helm_values.apps[app_key].harness.dependencies.git:
                artifacts[app_name]['hooks'] = {
                    'before': [git_clone_hook(conf, context_path) for conf in helm_values.apps[app_key].harness.dependencies.git]
                }

    for root_path in root_paths:
        skaffold_conf = dict_merge(skaffold_conf, get_template(
            join(root_path, DEPLOYMENT_CONFIGURATION_PATH, template_name)))

        base_dockerfiles = find_dockerfiles_paths(
            join(root_path, BASE_IMAGES_PATH))

        for dockerfile_path in base_dockerfiles:
            process_build_dockerfile(dockerfile_path, root_path, global_context=True)

    release_config = skaffold_conf['deploy']['helm']['releases'][0]
    release_config['name'] = helm_values.namespace
    release_config['namespace'] = helm_values.namespace
    release_config['artifactOverrides'][KEY_APPS] = {}

    static_images = set()
    for root_path in root_paths:
        static_dockerfiles = find_dockerfiles_paths(
            join(root_path, STATIC_IMAGES_PATH))

        for dockerfile_path in static_dockerfiles:
            process_build_dockerfile(dockerfile_path, root_path)

    for root_path in root_paths:
        apps_path = join(root_path, APPS_PATH)

        # Get all dockerfiles in the applications directory, including those in subdirectories
        app_dockerfiles = find_dockerfiles_paths(apps_path)

        release_config['artifactOverrides'][KEY_TASK_IMAGES] = {
            task_image: remove_tag(helm_values[KEY_TASK_IMAGES][task_image])
            for task_image in helm_values[KEY_TASK_IMAGES]
        }
        for dockerfile_path in app_dockerfiles:
            app_relative_to_skaffold = os.path.relpath(
                dockerfile_path, output_path)
            context_path = os.path.relpath(dockerfile_path, '.')
            app_relative_to_base = os.path.relpath(dockerfile_path, apps_path)
            app_name = app_name_from_path(app_relative_to_base)
            app_key = app_name

            if app_key not in apps:
                if 'tasks' in app_relative_to_base and manage_task_images:
                    parent_app_name = app_name_from_path(
                        app_relative_to_base.split('/tasks')[0])
                    parent_app_key = parent_app_name

                    if parent_app_key in apps:
                        artifacts[app_key] = build_artifact(app_name, app_relative_to_skaffold,
                                                            guess_build_dependencies_from_dockerfile(dockerfile_path))
                elif app_name in helm_values[KEY_TASK_IMAGES]:
                    process_build_dockerfile(dockerfile_path, root_path,
                                             requirements=guess_build_dependencies_from_dockerfile(dockerfile_path), app_name=app_name)
                continue
            build_requirements = apps[app_key][KEY_HARNESS].dependencies.build

            # app_image_tag = remove_tag(
            #     apps[app_key][KEY_HARNESS][KEY_DEPLOYMENT]['image'])
            # artifacts[app_key] = build_artifact(
            #     app_image_tag, app_relative_to_skaffold, build_requirements)
            process_build_dockerfile(dockerfile_path, root_path, requirements=guess_build_dependencies_from_dockerfile(dockerfile_path), app_name=app_name)
            app = apps[app_key]
            if not app['build']:
                continue
            if app[KEY_HARNESS][KEY_DEPLOYMENT]['image']:
                release_config['artifactOverrides']['apps'][app_key] = \
                    {
                        KEY_HARNESS: {
                            KEY_DEPLOYMENT: {
                                'image': remove_tag(app[KEY_HARNESS][KEY_DEPLOYMENT]['image'])
                            }
                        }
                }

            mains_candidates = find_file_paths(context_path, '__main__.py')

            def identify_unicorn_based_main(candidates):
                import re
                gunicorn_pattern = re.compile(r"gunicorn")
                # sort candidates, shortest path first
                for candidate in sorted(candidates, key=lambda x: len(x.split("/"))):
                    dockerfile_path = f"{candidate}/.."
                    while not exists(f"{dockerfile_path}/Dockerfile") and abspath(dockerfile_path) != abspath(root_path):
                        dockerfile_path += "/.."
                    dockerfile = f"{dockerfile_path}/Dockerfile"
                    if not exists(dockerfile):
                        continue
                    with open(dockerfile, 'r') as file:
                        if re.search(gunicorn_pattern, file.read()):
                            return candidate
                    requirements = f"{candidate}/../requirements.txt"
                    if not exists(requirements):
                        continue
                    with open(requirements, 'r') as file:
                        if re.search(gunicorn_pattern, file.read()):
                            return candidate
                return None

            task_main_file = identify_unicorn_based_main(mains_candidates)

            if task_main_file:
                release_config['overrides']['apps'][app_key] = \
                    {
                        'harness': {
                            'deployment': {
                                'command': ['python'],
                                'args': [f'/usr/src/app/{os.path.basename(task_main_file)}/__main__.py']
                            }
                        }
                }

            test_config: ApplicationTestConfig = helm_values.apps[app_key].harness.test
            if test_config.unit.enabled and test_config.unit.commands:

                skaffold_conf['test'].append(dict(
                    image=get_image_tag(app_name),
                    custom=[dict(command="docker run $IMAGE " + cmd) for cmd in test_config.unit.commands]
                ))

    if backend == COMPOSE_ENGINE:
        del skaffold_conf['deploy']
        skaffold_conf['deploy'] = {
            'docker': {
                'useCompose': True,
                'images': [artifact['image'] for artifact in artifacts.values() if artifact['image']]
            }
        }
    if backend == COMPOSE_ENGINE or helm_values.tag and not helm_values.local:
        skaffold_conf['build']['tagPolicy'] = {
            'envTemplate': {
                'template': '"{{.TAG}}"'
            }
        }
    else:
        skaffold_conf['build']['tagPolicy'] = {"sha256": {}}

    skaffold_conf['build']['artifacts'] = [v for v in artifacts.values()]

    with open(os.path.join(output_path, 'skaffold.yaml'), "w") as f:
        yaml.dump(skaffold_conf, f)
    return skaffold_conf


def git_clone_hook(conf: GitDependencyConfig, context_path: str):
    return {
        'command': [
            'sh',
            join(os.path.dirname(os.path.dirname(HERE)), 'clone.sh'),
            conf.branch_tag,
            conf.url,
            join(context_path, "dependencies", conf.path or os.path.basename(conf.url).split('.')[0])
        ]
    }


def create_vscode_debug_configuration(root_paths, helm_values):
    logging.info("Creating VS code cloud build configuration.\nCloud build extension is needed to debug.")

    vscode_launch_path = '.vscode/launch.json'
    all_images = get_all_images(helm_values)
    vs_conf = get_json_template(vscode_launch_path, True)

    debug_conf = get_json_template('vscode-debug-template.json', True)

    def get_image_tag(name):
        return all_images[name]

    for i in range(len(vs_conf['configurations'])):
        conf = vs_conf['configurations'][i]
        if conf['name'] == debug_conf['name']:
            del vs_conf['configurations'][i]
            break
    vs_conf['configurations'].append(debug_conf)

    apps = helm_values.apps

    for root_path in root_paths:
        apps_path = os.path.join(root_path, 'applications')

        src_root_paths = find_file_paths(apps_path, 'setup.py')

        for path in src_root_paths:
            app_relative_to_base = os.path.relpath(path, apps_path)
            app_relative_to_root = os.path.relpath(path, '.')
            app_name = app_name_from_path(app_relative_to_base.split('/')[0])
            app_key = app_name
            if app_key in apps.keys():
                debug_conf["debug"].append({
                    "image": get_image_tag(app_name),
                    "sourceFileMap": {
                        "justMyCode": False,
                        f"${{workspaceFolder}}/{app_relative_to_root}": apps[app_key].harness.get('sourceRoot',
                                                                                                  "/usr/src/app"),
                    }
                })

    if not os.path.exists(os.path.dirname(vscode_launch_path)):
        os.makedirs(os.path.dirname(vscode_launch_path))
    with open(vscode_launch_path, 'w') as f:
        json.dump(vs_conf, f, indent=2, sort_keys=True)


def get_additional_build_args(helm_values: HarnessMainConfig, app_key: str) -> dict[str, str]:
    if app_key not in helm_values.apps:
        return None

    if not (helm_values.apps[app_key].harness.dockerfile and helm_values.apps[app_key].harness.dockerfile.buildArgs):
        return None

    return helm_values.apps[app_key].harness.dockerfile.buildArgs
