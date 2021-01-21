"""
Utilities to create a helm chart from a CloudHarness directory structure
"""
import yaml
import os
import shutil
import sys
import logging
import subprocess
import tarfile
from docker import from_env as DockerClient
from pathlib import Path
from .constants import VALUES_MANUAL_PATH, VALUE_TEMPLATE_PATH, HELM_CHART_PATH, APPS_PATH, HELM_PATH, HERE, \
    DEPLOYMENT_CONFIGURATION_PATH
from .utils import get_cluster_ip, get_image_name, env_variable, get_sub_paths, app_name_from_path, \
    get_template, merge_configuration_directories, merge_to_yaml_file, dict_merge

KEY_HARNESS = 'harness'
KEY_SERVICE = 'service'
KEY_DATABASE = 'database'
KEY_DEPLOYMENT = 'deployment'
KEY_APPS = 'apps'

def deploy(namespace, output_path='./deployment'):
    helm_path = os.path.join(output_path, HELM_CHART_PATH)
    logging.info('Deploying helm chart %s', helm_path)
    subprocess.run("helm dependency update".split(), cwd=helm_path)

    subprocess.run(
        f"helm upgrade ch {helm_path} -n {namespace} --install --reset-values".split())

def create_helm_chart(root_paths, tag='latest', registry='', local=True, domain=None, exclude=(), secured=True,
                      output_path='./deployment', include=None, registry_secret=None, tls=True):
    """
    Creates values file for the helm chart
    """
    dest_deployment_path = os.path.join(output_path, HELM_CHART_PATH)
    if registry and registry[-1] != '/':
        registry = registry + '/'
    if os.path.exists(dest_deployment_path):
        shutil.rmtree(dest_deployment_path)
    # Initialize with default
    copy_merge_base_deployment(dest_deployment_path, os.path.join(HERE, DEPLOYMENT_CONFIGURATION_PATH, HELM_PATH))
    helm_values = collect_helm_values(HERE, tag=tag, registry=registry, exclude=exclude, include=include)

    # Override for every cloudharness scaffolding
    for root_path in root_paths:
        copy_merge_base_deployment(dest_helm_chart_path=dest_deployment_path,
                                   base_helm_chart=os.path.join(root_path, DEPLOYMENT_CONFIGURATION_PATH, HELM_PATH))
        collect_apps_helm_templates(root_path, exclude=exclude, include=include,
                                    dest_helm_chart_path=dest_deployment_path)
        helm_values = dict_merge(helm_values,
                                 collect_helm_values(root_path, tag=tag, registry=registry, exclude=exclude,
                                                     include=include))

    create_tls_certificate(local, domain, tls, output_path, helm_values)

    finish_helm_values(values=helm_values, tag=tag, registry=registry, local=local, domain=domain, secured=secured,
                       registry_secret=registry_secret, tls=tls)
    # Save values file for manual helm chart
    merged_values = merge_to_yaml_file(helm_values, os.path.join(dest_deployment_path, VALUES_MANUAL_PATH))
    return merged_values


def merge_helm_chart(source_templates_path, dest_helm_chart_path=HELM_CHART_PATH):
    pass


def collect_apps_helm_templates(search_root, dest_helm_chart_path, exclude=(), include=None):
    """
    Searches recursively for helm templates inside the applications and collects the templates in the destination

    :param search_root:
    :param dest_helm_chart_path: collected helm templates destination folder
    :param exclude:
    :return:
    """
    app_base_path = os.path.join(search_root, APPS_PATH)

    for app_path in get_sub_paths(app_base_path):
        app_name = app_name_from_path(os.path.relpath(app_path, app_base_path))
        if app_name in exclude or (include and not any(inc in app_name for inc in include)):
            continue
        template_dir = os.path.join(app_path, 'deploy/templates')
        if os.path.exists(template_dir):
            dest_dir = os.path.join(dest_helm_chart_path, 'templates', app_name)

            logging.info("Collecting templates for application %s to %s", app_name, dest_dir)
            if os.path.exists(dest_dir):
                logging.warning("Merging/overriding all files in directory %s", dest_dir)
                merge_configuration_directories(template_dir, dest_dir)
            else:
                shutil.copytree(template_dir, dest_dir)
        resources_dir = os.path.join(app_path, 'deploy/resources')
        if os.path.exists(resources_dir):
            dest_dir = os.path.join(dest_helm_chart_path, 'resources', app_name)

            logging.info("Collecting resources for application  %s to %s", app_name, dest_dir)
            if os.path.exists(dest_dir):
                shutil.rmtree(dest_dir)
            shutil.copytree(resources_dir, dest_dir)

        subchart_dir = os.path.join(app_path, 'deploy/charts')
        if os.path.exists(subchart_dir):
            dest_dir = os.path.join(dest_helm_chart_path, 'charts', app_name)

            logging.info("Collecting templates for application %s to %s", app_name, dest_dir)
            if os.path.exists(dest_dir):
                logging.warning("Merging/overriding all files in directory %s", dest_dir)
                merge_configuration_directories(subchart_dir, dest_dir)
            else:
                shutil.copytree(subchart_dir, dest_dir)


def copy_merge_base_deployment(dest_helm_chart_path, base_helm_chart):
    if not os.path.exists(base_helm_chart):
        return
    if os.path.exists(dest_helm_chart_path):
        logging.info("Merging/overriding all files in directory %s", dest_helm_chart_path)
        merge_configuration_directories(base_helm_chart, dest_helm_chart_path)
    else:
        logging.info("Copying base deployment chart from %s to %s", base_helm_chart, dest_helm_chart_path)
        shutil.copytree(base_helm_chart, dest_helm_chart_path)


def collect_helm_values(deployment_root, exclude=(), include=None, tag='latest', registry=''):
    """
    Creates helm values from a cloudharness deployment scaffolding
    """

    values_template_path = os.path.join(deployment_root, DEPLOYMENT_CONFIGURATION_PATH, 'values-template.yaml')
    value_spec_template_path = os.path.join(deployment_root, DEPLOYMENT_CONFIGURATION_PATH, 'value-template.yaml')
    if not os.path.exists(values_template_path):
        values = {}
    else:
        values = get_template(values_template_path)

    values[KEY_APPS] = {}

    app_base_path = os.path.join(deployment_root, APPS_PATH)
    for app_path in get_sub_paths(app_base_path):
        app_name = app_name_from_path(os.path.relpath(app_path, app_base_path))

        if app_name in exclude or (include and not any(inc in app_name for inc in include)):
            continue

        app_values = create_values_spec(app_name, app_path, tag=tag, registry=registry,
                                        template_path=value_spec_template_path)
        values[KEY_APPS][app_name.replace('-', '_')] = app_values

    return values


def finish_helm_values(values, tag='latest', registry='', local=True, domain=None, secured=True, registry_secret=None, tls=True):
    """
    Sets default overridden values
    """
    if registry:
        logging.info(f"Registry set: {registry}")
    if local:
        values['registry']['secret'] = ''
    if registry_secret:
        logging.info(f"Registry secret set")
    values['registry']['name'] = registry
    values['registry']['secret'] = registry_secret
    values['tag'] = tag
    values['secured_gatekeepers'] = secured
    values['ingress']['ssl_redirect'] = values['ingress']['ssl_redirect'] and tls

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


def values_from_legacy(values):
    harness = values[KEY_HARNESS]

    if 'name' in values:
        harness['name'] = values['name']
    if 'subdomain' in values:
        harness['subdomain'] = values['subdomain']
    if 'autodeploy' in values:
        harness[KEY_DEPLOYMENT]['auto'] = values['autodeploy']
    if 'autoservice' in values:
        harness[KEY_SERVICE]['auto'] = values['autoservice']
    if 'secureme' in values:
        harness['secured'] = values['secureme']
    if 'resources' in values:
        harness[KEY_DEPLOYMENT]['resources'].update(values['resources'])
    if 'replicas' in values:
        harness[KEY_DEPLOYMENT]['replicas'] = values['replicas']
    if 'image' in values:
        harness[KEY_DEPLOYMENT]['image'] = values['image']
    if 'port' in values:
        harness[KEY_DEPLOYMENT]['port'] = values['port']
        harness[KEY_SERVICE]['port'] = values['port']


def values_set_legacy(values):
    harness = values[KEY_HARNESS]
    if harness[KEY_DEPLOYMENT]['image']:
        values['image'] = harness[KEY_DEPLOYMENT]['image']

    values['name'] = harness['name']
    if harness[KEY_DEPLOYMENT]['port']:
        values['port'] = harness[KEY_DEPLOYMENT]['port']
    values['resources'] = harness[KEY_DEPLOYMENT]['resources']


def create_values_spec(app_name, app_path, tag=None, registry='', template_path=VALUE_TEMPLATE_PATH):
    logging.info('Generating values script for ' + app_name)

    values_default = get_template(template_path)

    specific_template_path = os.path.join(app_path, 'deploy', 'values.yaml')
    if os.path.exists(specific_template_path):
        logging.info("Specific values template found: " + specific_template_path)
        with open(specific_template_path) as f:
            values_specific = yaml.safe_load(f)
        values = dict_merge(values_default, values_specific)
    else:
        values = values_default

    values_from_legacy(values)
    harness = values[KEY_HARNESS]

    if not harness['name']:
        harness['name'] = app_name
    if not harness[KEY_SERVICE]['name']:
        harness[KEY_SERVICE]['name'] = app_name
    if not harness[KEY_DEPLOYMENT]['name']:
        harness[KEY_DEPLOYMENT]['name'] = app_name
    if not harness[KEY_DATABASE]['name']:
        harness[KEY_DATABASE]['name'] = app_name.strip() + '-db'
    if not harness[KEY_DEPLOYMENT]['image']:

        harness[KEY_DEPLOYMENT]['image'] = registry + get_image_name(app_name) + f':{tag}' if tag else ''

    values_set_legacy(values)

    for k in values:
        if isinstance(values[k], dict) and KEY_HARNESS in values[k]:
            values[k][KEY_HARNESS] = dict_merge(values[k][KEY_HARNESS], values_default[KEY_HARNESS])

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
    for app_name, value in values[KEY_APPS].items():
        if KEY_HARNESS in value:
            values['env'].extend(extract_env_variables_from_values(value[KEY_HARNESS], prefix='CH_' + app_name))
    values['env'].append(env_variable('CH_DOMAIN', values['domain']))
    values['env'].append(env_variable('CH_IMAGE_REGISTRY', values['registry']['name']))
    values['env'].append(env_variable('CH_IMAGE_TAG', values['tag']))


def hosts_info(values):
    domain = values['domain']
    namespace = values['namespace']
    subdomains = (app[KEY_HARNESS]['subdomain'] for app in values[KEY_APPS].values() if
                  KEY_HARNESS in app and app[KEY_HARNESS]['subdomain'])
    try:
        ip = get_cluster_ip()
    except:
        logging.warning('Cannot get cluster ip')
        return
    logging.info(
        "\nTo test locally, update your hosts file" + f"\n{ip}\t{domain + ' ' + ' '.join(sd + '.' + domain for sd in subdomains)}")

    deployments = (app[KEY_HARNESS][KEY_DEPLOYMENT]['name'] for app in values[KEY_APPS].values() if KEY_HARNESS in app)

    logging.info("\nTo run locally some apps, also those references may be needed")
    for appname in values[KEY_APPS]:
        app = values[KEY_APPS][appname]['harness']
        if 'deployment' not in app: continue
        print(
            "kubectl port-forward -n {namespace} deployment/{app} {port}:{port}".format(
                app=app['deployment']['name'], port=app['deployment']['port'], namespace=namespace))

    print(f"127.0.0.1\t{' '.join(s + '.cloudharness' for s in deployments)}")


def create_tls_certificate(local, domain, tls, output_path, helm_values):

    if not tls:
        helm_values['tls'] = None
        return
    helm_values['tls'] = domain.replace(".", "-") + "-tls"
    if not local:
        return

    HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')
    ROOT = os.path.dirname(os.path.dirname(HERE)).replace(os.path.sep, '/')

    bootstrap_file_path = os.path.join(ROOT, 'utilities', 'cloudharness_utilities', 'scripts')
    bootstrap_file = 'bootstrap.sh'
    certs_parent_folder_path = os.path.join(output_path, 'helm', 'resources')
    certs_folder_path = os.path.join(certs_parent_folder_path, 'certs')

    if os.path.exists(os.path.join(certs_folder_path)):
        # don't overwrite the certificate if it exists
        return

    try:
        client = DockerClient()
        client.ping()
    except:
        raise ConnectionRefusedError(
            '\n\nIs docker running? Run "eval(minikube docker-env)" if you are using minikube...')

    # Create CA and sign cert for domain
    container = client.containers.run(image='frapsoft/openssl',
                                      command=f'sleep 60',
                                      entrypoint="",
                                      detach=True,
                                      environment=[f"DOMAIN={domain}"],
                                      )

    container.exec_run('mkdir -p /mnt/vol1')
    container.exec_run('mkdir -p /mnt/certs')

    # copy bootstrap file
    cur_dir = os.getcwd()
    os.chdir(bootstrap_file_path)
    tar = tarfile.open(bootstrap_file + '.tar', mode='w')
    try:
        tar.add(bootstrap_file)
    finally:
        tar.close()
    data = open(bootstrap_file + '.tar', 'rb').read()
    container.put_archive('/mnt/vol1', data)
    os.chdir(cur_dir)
    container.exec_run(f'tar x {bootstrap_file}.tar', workdir='/mnt/vol1')

    # exec bootstrap file
    container.exec_run(f'/bin/ash /mnt/vol1/{bootstrap_file}')

    # retrieve the certs from the container
    bits, stat = container.get_archive('/mnt/certs')
    if not os.path.exists(certs_folder_path):
        os.makedirs(certs_folder_path)
    f = open(f'{certs_parent_folder_path}/certs.tar', 'wb')
    for chunk in bits:
        f.write(chunk)
    f.close()
    cf = tarfile.open(f'{certs_parent_folder_path}/certs.tar')
    cf.extractall(path=certs_parent_folder_path)

    logs = container.logs()
    logging.info(f'openssl container logs: {logs}')

    # stop the container
    container.kill()

    logging.info("Created certificates for local deployment")
