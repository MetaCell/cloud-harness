"""
Utilities to create a helm chart from a CloudHarness directory structure
"""
import yaml
import os
import shutil
import logging
import subprocess

from .constants import VALUES_MANUAL_PATH, VALUE_TEMPLATE_PATH, HELM_CHART_PATH, APPS_PATH, HELM_PATH, HERE, DEPLOYMENT_CONFIGURATION_PATH
from .utils import get_cluster_ip, get_image_name, env_variable, get_sub_paths, image_name_from_docker_path, \
    get_template, merge_configuration_directories, merge_to_yaml_file, dict_merge




def create_helm_chart(root_paths, tag='latest', registry='', local=True, domain=None, exclude=(), secured=True, output_path='./deployment'):
    """
    Creates values file for the helm chart
    """
    dest_deployment_path = os.path.join(output_path, HELM_CHART_PATH)

    # Initialize with default
    copy_merge_base_deployment(dest_deployment_path, os.path.join(HERE, DEPLOYMENT_CONFIGURATION_PATH, HELM_PATH))
    helm_values = collect_helm_values(HERE, tag=tag, registry=registry, exclude=exclude)

    # Override for every cloudharness scaffolding
    for root_path in root_paths:
        copy_merge_base_deployment(dest_helm_chart_path=dest_deployment_path, base_helm_chart=os.path.join(root_path, DEPLOYMENT_CONFIGURATION_PATH, HELM_PATH))
        collect_apps_helm_templates(root_path, exclude=exclude, dest_helm_chart_path=dest_deployment_path)
        helm_values = dict_merge(helm_values, collect_helm_values(root_path, tag=tag, registry=registry, exclude=exclude))

    finish_helm_values(values=helm_values, tag=tag, registry=registry, local=local, domain=domain, secured=secured)
    # Save values file for manual helm chart
    merged_values = merge_to_yaml_file(helm_values, os.path.join(dest_deployment_path, VALUES_MANUAL_PATH))
    return merged_values


def merge_helm_chart(source_templates_path, dest_helm_chart_path=HELM_CHART_PATH):
    pass


def collect_apps_helm_templates(search_root, dest_helm_chart_path, exclude=()):
    """
    Searches recursively for helm templates inside the applications and collects the templates in the destination

    :param search_root:
    :param dest_helm_chart_path: collected helm templates destination folder
    :param exclude:
    :return:
    """
    app_base_path = os.path.join(search_root, APPS_PATH)

    for app_path in get_sub_paths(app_base_path):
        app_name = image_name_from_docker_path(os.path.relpath(app_path, app_base_path))
        if app_name in exclude:
            continue
        template_dir = os.path.join(app_path, 'deploy/templates')
        if os.path.exists(template_dir):
            dest_dir = os.path.join(dest_helm_chart_path, 'templates', app_name)

            logging.info(f"Collecting templates for application {app_name} to {dest_dir}")
            if os.path.exists(dest_dir):
                logging.warning("Merging/overriding all files in directory " + dest_dir)
                merge_configuration_directories(template_dir, dest_dir)
            else:
                shutil.copytree(template_dir, dest_dir)
        resources_dir = os.path.join(app_path, 'deploy/resources')
        if os.path.exists(resources_dir):
            dest_dir = os.path.join(dest_helm_chart_path, 'resources', app_name)

            logging.info(f"Collecting resources for application {app_name} to {dest_dir}")
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            shutil.copytree(resources_dir, dest_dir)


def copy_merge_base_deployment(dest_helm_chart_path, base_helm_chart):
    if not os.path.exists(base_helm_chart):
        return
    if os.path.exists(dest_helm_chart_path):
        logging.info("Merging/overriding all files in directory {}".format(dest_helm_chart_path))
        merge_configuration_directories(base_helm_chart, dest_helm_chart_path)
    else:
        logging.info("Copying base deployment chart from {} to {}".format(base_helm_chart, dest_helm_chart_path))
        shutil.copytree(base_helm_chart, dest_helm_chart_path)


def collect_helm_values(deployment_root, exclude=(), tag='latest', registry=''):
    """
    Creates helm values from a cloudharness deployment scaffolding
    """

    values_template_path = os.path.join(deployment_root, DEPLOYMENT_CONFIGURATION_PATH, 'values-template.yaml')
    value_spec_template_path = os.path.join(deployment_root, DEPLOYMENT_CONFIGURATION_PATH, 'value-template.yaml')
    if not os.path.exists(values_template_path):
        values = {}
    else:
        values = get_template(values_template_path)

    values['apps'] = {}

    app_base_path = os.path.join(deployment_root, APPS_PATH)
    for app_path in get_sub_paths(app_base_path):
        app_name = image_name_from_docker_path(os.path.relpath(app_path, app_base_path))

        if app_name in exclude:
            continue

        app_values = create_values_spec(app_name, app_path, tag=tag, registry=registry, template_path=value_spec_template_path)
        values['apps'][app_name.replace('-', '_')] = app_values

    return values


def finish_helm_values(values, tag='latest', registry='', local=True, domain=None, secured=True):
    """
    Sets default overridden values
    """
    if registry:
        logging.info(f"Registry set: {registry}")
    if local:
        values['registry']['secret'] = ''
    values['registry']['name'] = registry  # Otherwise leave default for codefresh
    values['tag'] = tag  # Otherwise leave default for codefresh
    values['secured_gatekeepers'] = secured

    if domain:
        values['domain'] = domain

    values['local'] = local
    if local:
        try:
            values['localIp'] = get_cluster_ip()
        except subprocess.TimeoutExpired:
            logging.warning("Minikube not available")

    # Create environment variables
    create_env_variables(values)
    return values

def create_values_spec(app_name, app_path, tag=None, registry='', template_path=VALUE_TEMPLATE_PATH):
    logging.info('Generating values script for ' + app_name)

    values = get_template(template_path)
    if registry and registry[-1] != '/':
        registry = registry + '/'
    values['name'] = app_name

    values['image'] = registry + get_image_name(app_name) + f':{tag}' if tag else ''

    specific_template_path = os.path.join(app_path, 'deploy', 'values.yaml')
    if os.path.exists(specific_template_path):
        logging.info("Specific values template found: " + specific_template_path)
        with open(specific_template_path) as f:
            values_specific = yaml.safe_load(f)
        values.update(values_specific)
    return values


def extract_env_variables_from_values(values, envs=tuple(), prefix=''):
    if isinstance(values, dict):
        newenvs = list(envs)
        for key, value in values.items():
            v = extract_env_variables_from_values(value, envs, f"{prefix}_{key}".replace('-', '_').upper())
            if key in ('name', 'port', 'subdomain'):
                newenvs.extend(v)
        return newenvs
    else:
        return [env_variable(prefix, values)]


def create_env_variables(values):
    for app_name, value in values['apps'].items():
        values['env'].extend(extract_env_variables_from_values(value, prefix='CH_' + app_name))
    values['env'].append(env_variable('CH_DOMAIN', values['domain']))
    values['env'].append(env_variable('CH_IMAGE_REGISTRY', values['registry']['name']))
    values['env'].append(env_variable('CH_IMAGE_TAG', values['tag']))


def hosts_info(values):

    domain = values['domain']
    namespace = values['namespace']
    subdomains = (app['subdomain'] for app in values['apps'].values() if 'subdomain' in app and app['subdomain'])
    try:
        ip = get_cluster_ip()
    except:
        return
    logging.info("\nTo test locally, update your hosts file" + f"\n{ip}\t{' '.join(sd + '.' + domain for sd in subdomains)}")

    services = (app['name'].replace("-", "_") for app in values['apps'].values() if 'name' in app)

    logging.info("\nTo run locally some apps, also those references may be needed")
    for appname in values['apps']:
        app = values['apps'][appname]
        if 'name' not in app or 'port' not in app: continue
        print(
            "kubectl port-forward -n {namespace} deployment/{app} {port}:{port}".format(
                app=appname, port=app['port'], namespace=namespace))

    print(f"127.0.0.1\t{' '.join(s + '.cloudharness' for s in services)}")
