import os
import logging
import json

from cloudharness_utilities.constants import HELM_CHART_PATH, DEPLOYMENT_CONFIGURATION_PATH, DEPLOYMENT_PATH
from cloudharness_utilities.helm import KEY_APPS, KEY_HARNESS, KEY_DEPLOYMENT
from cloudharness_utilities.utils import get_template, dict_merge, find_dockerfiles_paths, app_name_from_path, \
    find_file_paths, merge_to_yaml_file, get_json_template


def create_skaffold_configuration(root_paths, helm_values, output_path='.'):
    skaffold_conf = get_template('skaffold-template.yaml', True)
    apps = helm_values[KEY_APPS]
    artifacts = {}
    overrides = {}
    release_config = skaffold_conf['deploy']['helm']['releases'][0]
    release_config['name'] = helm_values['namespace']

    for root_path in root_paths:
        skaffold_conf = dict_merge(skaffold_conf, get_template(
            os.path.join(root_path, DEPLOYMENT_CONFIGURATION_PATH, 'skaffold-template.yaml')))
        apps_path = os.path.join(root_path, 'applications')
        app_dockerfiles = (path for path in find_dockerfiles_paths(apps_path) if 'tasks' not in path)

        release_config['artifactOverrides'][KEY_APPS] = {}
        for app_key in apps:
            app = apps[app_key]
            if app[KEY_HARNESS][KEY_DEPLOYMENT]['auto']:
                release_config['artifactOverrides']['apps'][app_key] = \
                    {
                        'harness': {
                            'deployment': {
                                'image': app['harness']['name']
                            }
                        }
                    }

        for dockerfile_path in app_dockerfiles:
            app_relative_to_skaffold = os.path.relpath(dockerfile_path, output_path)
            app_relative_to_root = os.path.relpath(dockerfile_path, '.')
            app_relative_to_base = os.path.relpath(dockerfile_path, apps_path)
            app_name = app_name_from_path(app_relative_to_base)
            app_key = app_name.replace('-', '_')
            if app_key not in apps.keys():
                continue
            artifacts[app_key] = {
                'image': app_name,
                'context': app_relative_to_skaffold,
                'docker': {
                    'dockerfile': 'Dockerfile',
                    'buildArgs': {
                        'REGISTRY': helm_values["registry"]["name"],
                        'TAG': helm_values["tag"]
                    }
                }
            }

            flask_main = find_file_paths(app_relative_to_root, '__main__.py')

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


def create_vscode_debug_configuration(root_paths, values_manual_deploy):
    logging.info("Creating VS code cloud build configuration.\nCloud build extension is needed to debug.")

    vscode_launch_path = '.vscode/launch.json'

    vs_conf = get_json_template(vscode_launch_path, True)

    debug_conf = get_json_template('vscode-debug-template.json', True)

    if values_manual_deploy['registry'].get('name', None):
        debug_conf["imageRegistry"] = values_manual_deploy['registry']['name'][:-1] # remove trailing /
    for i in range(len(vs_conf['configurations'])):
        conf = vs_conf['configurations'][i]
        if conf['name'] == debug_conf['name']:
            del vs_conf['configurations'][i]
            break
    vs_conf['configurations'].append(debug_conf)

    apps = values_manual_deploy[KEY_APPS]

    for root_path in root_paths:
        apps_path = os.path.join(root_path, 'applications')

        flask_main_paths = find_file_paths(apps_path, '__main__.py')

        for path in flask_main_paths:
            app_relative_to_base = os.path.relpath(os.path.dirname(path), apps_path)
            app_relative_to_root = os.path.relpath(os.path.dirname(path), '.')
            app_name = app_name_from_path(app_relative_to_base.split('/')[0])
            app_key = app_name.replace('-', '_')
            if app_key in apps.keys():
                debug_conf["debug"].append({
                    "image": app_name,
                    "sourceFileMap": {
                        f"${{workspaceFolder}}/{app_relative_to_root}": "/usr/src/app",
                        "${workspaceFolder}/cloud-harness/libraries": "/libraries"
                    }
                })

    if not os.path.exists(os.path.dirname(vscode_launch_path)):
        os.makedirs(os.path.dirname(vscode_launch_path))
    with open(vscode_launch_path, 'w') as f:
        json.dump(vs_conf, f, indent=2, sort_keys=True)
