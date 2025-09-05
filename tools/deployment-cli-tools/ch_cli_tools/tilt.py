import os
import logging
import json
import time

from os.path import join, relpath, basename, exists, abspath
from jinja2 import Environment, PackageLoader, select_autoescape
from cloudharness_model import ApplicationTestConfig, HarnessMainConfig, GitDependencyConfig

from cloudharness_utils.constants import APPS_PATH, DEPLOYMENT_CONFIGURATION_PATH, \
    BASE_IMAGES_PATH, STATIC_IMAGES_PATH, HELM_ENGINE, COMPOSE_ENGINE
from .helm import KEY_APPS, KEY_HARNESS, KEY_DEPLOYMENT, KEY_TASK_IMAGES
from .utils import get_template, dict_merge, find_dockerfiles_paths, app_name_from_path, yaml, \
    find_file_paths, guess_build_dependencies_from_dockerfile, get_json_template, get_image_name

from . import HERE, CH_ROOT


import os.path, pkgutil
import ch_cli_tools
pkgpath = os.path.dirname(ch_cli_tools.__file__)
print([name for _, name, _ in pkgutil.iter_modules([pkgpath])])


env = Environment(
    loader=PackageLoader(package_name="ch_cli_tools", package_path="templates/tilt"),
    autoescape=select_autoescape()
)


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


def create_tilt_configuration(root_paths, helm_values: HarnessMainConfig, manage_task_images=True, output_path='.', name='', namespace='', domain=''):
    template_name = 'tilt-template.tpl'
    tilt_template = env.get_template(template_name)
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
        is_app: bool = False
    ) -> dict:
        build_args = {
            'DEBUG': 'true' if helm_values.local or helm_values.debug else ''
        }

        if additional_build_args:
            build_args.update(additional_build_args)

        if requirements:
            for req in requirements:
                build_args.update({req.replace('-', '_').upper(): get_image_tag(req)})

        image_name = get_image_tag(app_name)

        artifact_spec = {
            'name': app_name,
            'image': image_name,
            'context': context_path,
            'is_app': is_app,
            'docker': {
                'dockerfile': join(dockerfile_path, 'Dockerfile'),
                'buildArgs': build_args
            }
        }
        return artifact_spec

    base_images = set()

    def process_build_dockerfile(
        dockerfile_path: str,
        root_path: str,
        global_context: bool = False,
        requirements: list[str] = None,
        app_name: str = None
    ) -> None:
        is_app = True
        if app_name is None:
            app_name = app_name_from_path(basename(dockerfile_path))
            is_app = False
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
                is_app=is_app
            )

            if app_key in helm_values.apps and helm_values.apps[app_key].harness.dependencies and helm_values.apps[app_key].harness.dependencies.git:
                artifacts[app_name]['hooks'] = {
                    'before': [git_clone_hook(conf, context_path) for conf in helm_values.apps[app_key].harness.dependencies.git]
                }

    images = set()
    for root_path in root_paths:
        base_dockerfiles = find_dockerfiles_paths(
            join(root_path, BASE_IMAGES_PATH))

        for dockerfile_path in base_dockerfiles:
            process_build_dockerfile(dockerfile_path, root_path, global_context=True)

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

            process_build_dockerfile(dockerfile_path, root_path, requirements=guess_build_dependencies_from_dockerfile(dockerfile_path), app_name=app_name)
            app = apps[app_key]
            if not app['build']:
                continue

    images = [artifact for artifact in artifacts.values() if artifact['image']]
    apps = [artifact for artifact in artifacts.values() if artifact['is_app']]
    with open(os.path.join(output_path, 'Tiltfile'), "w") as f:
        f.write(tilt_template.render(ch_root=CH_ROOT, name=name, namespace=namespace, images=images, apps=apps, domain=domain))
    return None


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


def get_additional_build_args(helm_values: HarnessMainConfig, app_key: str) -> dict[str, str]:
    if app_key not in helm_values.apps:
        return None

    if not (helm_values.apps[app_key].harness.dockerfile and helm_values.apps[app_key].harness.dockerfile.buildArgs):
        return None

    return helm_values.apps[app_key].harness.dockerfile.buildArgs
