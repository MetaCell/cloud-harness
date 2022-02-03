import os
import logging
import json
import time

from cloudharness_utilities.constants import HELM_CHART_PATH, DEPLOYMENT_CONFIGURATION_PATH, DEPLOYMENT_PATH, \
    BASE_IMAGES_PATH, STATIC_IMAGES_PATH
from cloudharness_utilities.helm import KEY_APPS, KEY_HARNESS, KEY_DEPLOYMENT, KEY_TASK_IMAGES
from cloudharness_utilities.utils import get_template, dict_merge, find_dockerfiles_paths, app_name_from_path, \
    find_file_paths, guess_build_dependencies_from_dockerfile, merge_to_yaml_file, get_json_template, get_image_name


def create_skaffold_configuration(root_paths, helm_values, output_path='.', manage_task_images=True):
    skaffold_conf = get_template('skaffold-template.yaml', True)
    apps = helm_values[KEY_APPS]
    base_image_name = helm_values['registry'].get('name', '') + helm_values['name']
    artifacts = {}
    overrides = {}
    release_config = skaffold_conf['deploy']['helm']['releases'][0]
    release_config['name'] = helm_values['namespace']
    release_config['namespace'] = helm_values['namespace']

    def remove_tag(image_name):
        return image_name[0:-len(str(helm_values['tag']))-1]

    def get_image_tag(name):
        return f"{get_image_name(name, base_image_name)}"

    def build_artifact(image_name, root_path, requirements=None, dockerfile_path=''):
        artifact_spec = {
            'image': image_name,
            'context': root_path,
            'docker': {
                'dockerfile': os.path.join(dockerfile_path, 'Dockerfile'),
                'buildArgs': {
                    'REGISTRY': helm_values["registry"]["name"],
                    'TAG': helm_values["tag"],
                    'NOCACHE': str(time.time())
                },
                'ssh': 'default'
            }
        }
        if requirements:
            artifact_spec['requires'] = [{'image': get_image_tag(req), 'alias': req.replace('-', '_').upper()} for req
                                         in requirements]
        return artifact_spec

    release_config['artifactOverrides'][KEY_APPS] = {}
    base_images = set()
    for root_path in root_paths:
        skaffold_conf = dict_merge(skaffold_conf, get_template(
            os.path.join(root_path, DEPLOYMENT_CONFIGURATION_PATH, 'skaffold-template.yaml')))
        

        base_dockerfiles = find_dockerfiles_paths(os.path.join(root_path, BASE_IMAGES_PATH))

        
        for dockerfile_path in base_dockerfiles:
            context_path = os.path.relpath(root_path, output_path)
            app_name = app_name_from_path(os.path.basename(dockerfile_path))
            if app_name in helm_values[KEY_TASK_IMAGES]:
                base_images.add(get_image_name(app_name))
                artifacts[app_name] = build_artifact(get_image_tag(app_name), context_path,
                                                    dockerfile_path=os.path.relpath(dockerfile_path, context_path))
    static_images = set()
    for root_path in root_paths:
        static_dockerfiles = find_dockerfiles_paths(os.path.join(root_path, STATIC_IMAGES_PATH))
        
        for dockerfile_path in static_dockerfiles:
            context_path = os.path.relpath(dockerfile_path, output_path)
            app_name = app_name_from_path(os.path.basename(context_path))
            if app_name in helm_values[KEY_TASK_IMAGES]:
                static_images.add(get_image_name(app_name))
                artifacts[app_name] = build_artifact(get_image_tag(app_name), context_path, guess_build_dependencies_from_dockerfile(dockerfile_path))

    for root_path in root_paths:
        apps_path = os.path.join(root_path, 'applications')
        app_dockerfiles = find_dockerfiles_paths(apps_path)
        
        release_config['artifactOverrides'][KEY_TASK_IMAGES] = {
            task_image: remove_tag(helm_values[KEY_TASK_IMAGES][task_image])
            for task_image in helm_values[KEY_TASK_IMAGES]
        }
        for dockerfile_path in app_dockerfiles:
            app_relative_to_skaffold = os.path.relpath(dockerfile_path, output_path)
            context_path = os.path.relpath(dockerfile_path, '.')
            app_relative_to_base = os.path.relpath(dockerfile_path, apps_path)
            app_name = app_name_from_path(app_relative_to_base)
            app_key = app_name.replace('-', '_')
            if app_key not in apps:
                if 'tasks' in app_relative_to_base and manage_task_images:
                    parent_app_name = app_name_from_path(app_relative_to_base.split('/tasks')[0])
                    parent_app_key = parent_app_name.replace('-', '_')

                    if parent_app_key in apps:
                        artifacts[app_key] = build_artifact(get_image_tag(app_name), app_relative_to_skaffold,
                                                            base_images.union(static_images))

                continue


            build_requirements = apps[app_key][KEY_HARNESS]['dependencies'].get('build', [])
            app_image_tag = remove_tag(apps[app_key][KEY_HARNESS][KEY_DEPLOYMENT]['image'])
            artifacts[app_key] = build_artifact(app_image_tag, app_relative_to_skaffold, build_requirements)

            app = apps[app_key]
            if app[KEY_HARNESS][KEY_DEPLOYMENT]['image']:
                release_config['artifactOverrides']['apps'][app_key] = \
                    {
                        KEY_HARNESS: {
                            KEY_DEPLOYMENT: {
                                'image': remove_tag(app[KEY_HARNESS][KEY_DEPLOYMENT]['image'])
                            }
                        }
                    }

            flask_main = find_file_paths(context_path, '__main__.py')

            if flask_main:
                release_config['overrides']['apps'][app_key] = \
                    {
                        'harness': {
                            'deployment': {
                                'command': ['python'],
                                'args': [f'/usr/src/app/{os.path.basename(flask_main[0])}/__main__.py']
                            }
                        }
                    }

        skaffold_conf['build']['artifacts'] = [v for v in artifacts.values()]
        merge_to_yaml_file(skaffold_conf, os.path.join(output_path, 'skaffold.yaml'))
    return skaffold_conf


def create_vscode_debug_configuration(root_paths, helm_values):
    logging.info("Creating VS code cloud build configuration.\nCloud build extension is needed to debug.")

    vscode_launch_path = '.vscode/launch.json'

    vs_conf = get_json_template(vscode_launch_path, True)
    base_image_name = helm_values['name']
    debug_conf = get_json_template('vscode-debug-template.json', True)

    def get_image_tag(name):
        return f"{get_image_name(name, base_image_name)}"

    if helm_values['registry'].get('name', None):
        base_image_name = helm_values['registry']['name'] + helm_values['name']
    for i in range(len(vs_conf['configurations'])):
        conf = vs_conf['configurations'][i]
        if conf['name'] == debug_conf['name']:
            del vs_conf['configurations'][i]
            break
    vs_conf['configurations'].append(debug_conf)

    apps = helm_values[KEY_APPS]

    for root_path in root_paths:
        apps_path = os.path.join(root_path, 'applications')

        src_root_paths = find_file_paths(apps_path, 'setup.py')

        for path in src_root_paths:
            app_relative_to_base = os.path.relpath(path, apps_path)
            app_relative_to_root = os.path.relpath(path, '.')
            app_name = app_name_from_path(app_relative_to_base.split('/')[0])
            app_key = app_name.replace('-', '_')
            if app_key in apps.keys():
                debug_conf["debug"].append({
                    "image": get_image_tag(app_name),
                    # the double source map doesn't work at the moment. Hopefully will be fixed in future skaffold updates
                    "sourceFileMap": {
                        f"${{workspaceFolder}}/{app_relative_to_root}": apps[app_key][KEY_HARNESS].get('sourceRoot',
                                                                                                       "/usr/src/app"),
                    }
                })
                debug_conf["debug"].append({
                    "image": get_image_tag(app_name),
                    "sourceFileMap": {
                        "${workspaceFolder}/cloud-harness/libraries": "/libraries"
                    }
                })

    if not os.path.exists(os.path.dirname(vscode_launch_path)):
        os.makedirs(os.path.dirname(vscode_launch_path))
    with open(vscode_launch_path, 'w') as f:
        json.dump(vs_conf, f, indent=2, sort_keys=True)