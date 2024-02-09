"""
Utilities to create a helm chart from a CloudHarness directory structure
"""
import yaml
import os
import shutil
import logging
from hashlib import sha1
import subprocess
from functools import cache
import tarfile
from docker import from_env as DockerClient


from . import HERE, CH_ROOT
from cloudharness_utils.constants import TEST_IMAGES_PATH, VALUES_MANUAL_PATH, HELM_CHART_PATH, APPS_PATH, HELM_PATH, \
    DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH
from .utils import get_cluster_ip, get_image_name, env_variable, get_sub_paths, guess_build_dependencies_from_dockerfile, image_name_from_dockerfile_path, \
    get_template, merge_configuration_directories, merge_to_yaml_file, dict_merge, app_name_from_path, \
    find_dockerfiles_paths

from .models import HarnessMainConfig

KEY_HARNESS = 'harness'
KEY_SERVICE = 'service'
KEY_DATABASE = 'database'
KEY_DEPLOYMENT = 'deployment'
KEY_APPS = 'apps'
KEY_TASK_IMAGES = 'task-images'
KEY_TEST_IMAGES = 'test-images'

DEFAULT_IGNORE = ('/tasks', '.dockerignore', '.hypothesis', "__pycache__", '.node_modules', 'dist', 'build', '.coverage')


def deploy(namespace, output_path='./deployment'):
    helm_path = os.path.join(output_path, HELM_CHART_PATH)
    logging.info('Deploying helm chart %s', helm_path)
    subprocess.run("helm dependency update".split(), cwd=helm_path)

    subprocess.run(
        f"helm upgrade {namespace} {helm_path} -n {namespace} --install --reset-values".split())


def create_helm_chart(root_paths, tag='latest', registry='', local=True, domain=None, exclude=(), secured=True,
                      output_path='./deployment', include=None, registry_secret=None, tls=True, env=None,
                      namespace=None) -> HarnessMainConfig:
    if (type(env)) == str:
        env = [env]
    return CloudHarnessHelm(root_paths, tag=tag, registry=registry, local=local, domain=domain, exclude=exclude, secured=secured,
                            output_path=output_path, include=include, registry_secret=registry_secret, tls=tls, env=env,
                            namespace=namespace).process_values()


class CloudHarnessHelm:
    def __init__(self, root_paths, tag='latest', registry='', local=True, domain=None, exclude=(), secured=True,
                 output_path='./deployment', include=None, registry_secret=None, tls=True, env=None,
                 namespace=None):
        assert domain, 'A domain must be specified'
        self.root_paths = root_paths
        self.tag = tag
        if registry and registry[-1] != '/':
            self.registry = registry + '/'
        else:
            self.registry = registry
        self.local = local
        self.domain = domain
        self.exclude = exclude
        self.secured = secured
        self.output_path = output_path
        self.include = include
        self.registry_secret = registry_secret
        self.tls = tls
        self.env = env
        self.namespace = namespace

        self.dest_deployment_path = os.path.join(
            self.output_path, HELM_CHART_PATH)
        self.helm_chart_path = os.path.join(
            self.dest_deployment_path, 'Chart.yaml')
        self.__init_deployment()

        self.static_images = set()
        self.base_images = {}
        self.all_images = {}

    def __init_deployment(self):
        """
        Create the base helm chart
        """
        if os.path.exists(self.dest_deployment_path):
            shutil.rmtree(self.dest_deployment_path)
        # Initialize with default
        copy_merge_base_deployment(self.dest_deployment_path, os.path.join(
            CH_ROOT, DEPLOYMENT_CONFIGURATION_PATH, HELM_PATH))

        # Override for every cloudharness scaffolding
        for root_path in self.root_paths:
            copy_merge_base_deployment(dest_helm_chart_path=self.dest_deployment_path,
                                       base_helm_chart=os.path.join(root_path, DEPLOYMENT_CONFIGURATION_PATH, HELM_PATH))
            collect_apps_helm_templates(root_path, exclude=self.exclude, include=self.include,
                                        dest_helm_chart_path=self.dest_deployment_path)

    def __adjust_missing_values(self, helm_values):
        if 'name' not in helm_values:
            with open(self.helm_chart_path) as f:
                chart_idx_content = yaml.safe_load(f)
            helm_values['name'] = chart_idx_content['name'].lower()

    def process_values(self) -> HarnessMainConfig:
        """
        Creates values file for the helm chart
        """
        helm_values = self.__get_default_helm_values()

        self.__adjust_missing_values(helm_values)

        helm_values = self.__merge_base_helm_values(helm_values)

        helm_values[KEY_APPS] = {}

        base_image_name = helm_values['name']

        helm_values[KEY_TASK_IMAGES] = {}

        self.__init_base_images(base_image_name)
        self.__init_static_images(base_image_name)
        helm_values[KEY_TEST_IMAGES] = self.__init_test_images(base_image_name)

        self.__process_applications(helm_values, base_image_name)

        self.create_tls_certificate(helm_values)

        values, include = self.__finish_helm_values(values=helm_values)

        # Adjust dependencies from static (common) images
        self.__assign_static_build_dependencies(helm_values)

        for root_path in self.root_paths:
            collect_apps_helm_templates(root_path, exclude=self.exclude, include=self.include,
                                        dest_helm_chart_path=self.dest_deployment_path)

        # Save values file for manual helm chart
        merged_values = merge_to_yaml_file(helm_values, os.path.join(
            self.dest_deployment_path, VALUES_MANUAL_PATH))
        if self.namespace:
            merge_to_yaml_file({'metadata': {'namespace': self.namespace},
                                'name': helm_values['name']}, self.helm_chart_path)
        validate_helm_values(merged_values)
        return HarnessMainConfig.from_dict(merged_values)

    def __process_applications(self, helm_values, base_image_name):
        for root_path in self.root_paths:
            app_values = init_app_values(
                root_path, exclude=self.exclude, values=helm_values[KEY_APPS])
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS],
                                               app_values)

            app_base_path = os.path.join(root_path, APPS_PATH)
            app_values = self.collect_app_values(
                app_base_path, base_image_name=base_image_name)
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS],
                                               app_values)

    def collect_app_values(self, app_base_path, base_image_name=None):
        values = {}

        for app_path in get_sub_paths(app_base_path):
            app_name = app_name_from_path(
                os.path.relpath(app_path, app_base_path))

            if app_name in self.exclude:
                continue
            app_key = app_name.replace('-', '_')

            app_values = self.create_app_values_spec(app_name, app_path, base_image_name=base_image_name)

            values[app_key] = dict_merge(
                values[app_key], app_values) if app_key in values else app_values

        return values

    def __init_static_images(self, base_image_name):
        for static_img_dockerfile in self.static_images:
            img_name = image_name_from_dockerfile_path(os.path.basename(
                static_img_dockerfile), base_name=base_image_name)
            self.base_images[os.path.basename(static_img_dockerfile)] = self.image_tag(
                img_name, build_context_path=static_img_dockerfile)

    def __assign_static_build_dependencies(self, helm_values):
        for static_img_dockerfile in self.static_images:
            key = os.path.basename(static_img_dockerfile)
            if key in helm_values[KEY_TASK_IMAGES]:
                dependencies = guess_build_dependencies_from_dockerfile(
                    static_img_dockerfile)
                for dep in dependencies:
                    if dep in self.base_images and dep not in helm_values[KEY_TASK_IMAGES]:
                        helm_values[KEY_TASK_IMAGES][dep] = self.base_images[dep]

        for image_name in list(helm_values[KEY_TASK_IMAGES].keys()):
            if image_name in self.exclude:
                del helm_values[KEY_TASK_IMAGES][image_name]

    def __init_base_images(self, base_image_name):

        for root_path in self.root_paths:
            for base_img_dockerfile in self.__find_static_dockerfile_paths(root_path):
                img_name = image_name_from_dockerfile_path(
                    os.path.basename(base_img_dockerfile), base_name=base_image_name)
                self.base_images[os.path.basename(base_img_dockerfile)] = self.image_tag(
                    img_name, build_context_path=root_path)

            self.static_images.update(find_dockerfiles_paths(
                os.path.join(root_path, STATIC_IMAGES_PATH)))
        return self.base_images

    def __init_test_images(self, base_image_name):
        test_images = {}
        for root_path in self.root_paths:
            for base_img_dockerfile in find_dockerfiles_paths(os.path.join(root_path, TEST_IMAGES_PATH)):
                img_name = image_name_from_dockerfile_path(
                    os.path.basename(base_img_dockerfile), base_name=base_image_name)
                test_images[os.path.basename(base_img_dockerfile)] = self.image_tag(
                    img_name, build_context_path=base_img_dockerfile)

        return test_images


    def __find_static_dockerfile_paths(self, root_path):
        return find_dockerfiles_paths(os.path.join(root_path, BASE_IMAGES_PATH)) + find_dockerfiles_paths(os.path.join(root_path, STATIC_IMAGES_PATH))

    def __merge_base_helm_values(self, helm_values):
        # Override for every cloudharness scaffolding
        for root_path in self.root_paths:
            helm_values = dict_merge(
                helm_values,
                collect_helm_values(root_path, env=self.env)
            )

        return helm_values

    def __get_default_helm_values(self):
        helm_values = get_template(os.path.join(
            CH_ROOT, DEPLOYMENT_CONFIGURATION_PATH, HELM_PATH, 'values.yaml'))
        helm_values = dict_merge(helm_values,
                                 collect_helm_values(CH_ROOT, env=self.env))

        return helm_values

    def create_tls_certificate(self, helm_values):
        if not self.tls:
            helm_values['tls'] = None
            return
        if not self.local:
            return
        helm_values['tls'] = self.domain.replace(".", "-") + "-tls"

        bootstrap_file = 'bootstrap.sh'
        certs_parent_folder_path = os.path.join(
            self.output_path, 'helm', 'resources')
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
                                          environment=[
                                              f"DOMAIN={self.domain}"],
                                          )

        container.exec_run('mkdir -p /mnt/vol1')
        container.exec_run('mkdir -p /mnt/certs')

        # copy bootstrap file
        cur_dir = os.getcwd()
        os.chdir(os.path.join(HERE, 'scripts'))
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

    def __finish_helm_values(self, values):
        """
        Sets default overridden values
        """
        if self.registry:
            logging.info(f"Registry set: {self.registry}")
        if self.local:
            values['registry']['secret'] = ''
        if self.registry_secret:
            logging.info(f"Registry secret set")
        values['registry']['name'] = self.registry
        values['registry']['secret'] = self.registry_secret
        values['tag'] = self.tag
        if self.namespace:
            values['namespace'] = self.namespace
        values['secured_gatekeepers'] = self.secured
        values['ingress']['ssl_redirect'] = values['ingress']['ssl_redirect'] and self.tls
        values['tls'] = self.tls
        if self.domain:
            values['domain'] = self.domain

        values['local'] = self.local
        if self.local:
            try:
                values['localIp'] = get_cluster_ip()
            except subprocess.TimeoutExpired:
                logging.warning("Minikube not available")
            except:
                logging.warning("Kubectl not available")

        apps = values[KEY_APPS]

        for app_key in apps:
            v = apps[app_key]

            values_from_legacy(v)
            assert KEY_HARNESS in v, 'Default app value loading is broken'

            app_name = app_key.replace('_', '-')
            harness = v[KEY_HARNESS]
            harness['name'] = app_name

            if not harness[KEY_SERVICE].get('name', None):
                harness[KEY_SERVICE]['name'] = app_name
            if not harness[KEY_DEPLOYMENT].get('name', None):
                harness[KEY_DEPLOYMENT]['name'] = app_name

            if harness[KEY_DATABASE] and not harness[KEY_DATABASE].get('name', None):
                harness[KEY_DATABASE]['name'] = app_name.strip() + '-db'

            self.__clear_unused_db_configuration(harness)
            values_set_legacy(v)

        if self.include:
            self.include = get_included_with_dependencies(
                values, set(self.include))
            logging.info('Selecting included applications')

            for v in [v for v in apps]:
                if apps[v]['harness']['name'] not in self.include:
                    del apps[v]
                    continue
                values[KEY_TASK_IMAGES].update(apps[v][KEY_TASK_IMAGES])
                # Create environment variables
        else:
            for v in [v for v in apps]:
                values[KEY_TASK_IMAGES].update(apps[v][KEY_TASK_IMAGES])
        create_env_variables(values)
        return values, self.include

    def __clear_unused_db_configuration(self, harness_config):
        database_config = harness_config[KEY_DATABASE]
        database_type = database_config.get('type', None)
        if database_type is None:
            del harness_config[KEY_DATABASE]
            return
        db_specific_keys = [k for k, v in database_config.items()
                            if isinstance(v, dict) and 'image' in v and 'ports' in v]
        for db in db_specific_keys:
            if database_type != db:
                del database_config[db]

    def image_tag(self, image_name, build_context_path=None, dependencies=()):
        tag = self.tag
        if tag is None and not self.local:
            logging.info(f"Generating tag for {image_name} from {build_context_path} and {dependencies}")
            ignore_path = os.path.join(build_context_path, '.dockerignore')
            ignore = set(DEFAULT_IGNORE)
            if os.path.exists(ignore_path):
                with open(ignore_path) as f:
                    ignore = ignore.union({line.strip() for line in f})
            logging.info(f"Ignoring {ignore}")
            tag = generate_tag_from_content(build_context_path, ignore)
            logging.info(f"Content hash: {tag}")
            dependencies = dependencies or guess_build_dependencies_from_dockerfile(build_context_path)
            tag = sha1((tag + "".join(self.all_images.get(n , '') for n in dependencies)).encode("utf-8")).hexdigest()
            logging.info(f"Generated tag: {tag}")
            app_name = image_name.split("/")[-1] # the image name can have a prefix
            self.all_images[app_name] = tag
        return self.registry + image_name + (f':{tag}' if tag else '')

    def create_app_values_spec(self, app_name, app_path, base_image_name=None):
        logging.info('Generating values script for ' + app_name)

        specific_template_path = os.path.join(app_path, 'deploy', 'values.yaml')
        if os.path.exists(specific_template_path):
            logging.info("Specific values template found: " +
                        specific_template_path)
            values = get_template(specific_template_path)
        else:
            values = {}

        for e in self.env:
            specific_template_path = os.path.join(
                app_path, 'deploy', f'values-{e}.yaml')
            if os.path.exists(specific_template_path):
                logging.info(
                    "Specific environment values template found: " + specific_template_path)
                with open(specific_template_path) as f:
                    values_env_specific = yaml.safe_load(f)
                values = dict_merge(values, values_env_specific)

        if KEY_HARNESS in values and 'name' in values[KEY_HARNESS] and values[KEY_HARNESS]['name']:
            logging.warning('Name is automatically set in applications: name %s will be ignored',
                            values[KEY_HARNESS]['name'])

        image_paths = [path for path in find_dockerfiles_paths(
            app_path) if 'tasks/' not in path and 'subapps' not in path]
        if len(image_paths) > 1:
            logging.warning('Multiple Dockerfiles found in application %s. Picking the first one: %s', app_name,
                            image_paths[0])
        if KEY_HARNESS in values and 'dependencies' in values[KEY_HARNESS] and 'build' in values[KEY_HARNESS]['dependencies']:
            build_dependencies = values[KEY_HARNESS]['dependencies']['build']
        else:
            build_dependencies = []

        if len(image_paths) > 0:
            image_name = image_name_from_dockerfile_path(os.path.relpath(
                image_paths[0], os.path.dirname(app_path)), base_image_name)

            values['image'] = self.image_tag(
                image_name, build_context_path=app_path, dependencies=build_dependencies)
        elif KEY_HARNESS in values and not values[KEY_HARNESS].get(KEY_DEPLOYMENT, {}).get('image', None) and values[
                KEY_HARNESS].get(KEY_DEPLOYMENT, {}).get('auto', False):
            raise Exception(f"At least one Dockerfile must be specified on application {app_name}. "
                            f"Specify harness.deployment.image value if you intend to use a prebuilt image.")

        task_images_paths = [path for path in find_dockerfiles_paths(
            app_path) if 'tasks/' in path]
        values[KEY_TASK_IMAGES] = values.get(KEY_TASK_IMAGES, {})

        if build_dependencies:
            for build_dependency in values[KEY_HARNESS]['dependencies']['build']:
                if build_dependency in self.base_images:
                    values[KEY_TASK_IMAGES][build_dependency] = self.base_images[build_dependency]

        for task_path in task_images_paths:
            task_name = app_name_from_path(os.path.relpath(
                task_path, os.path.dirname(app_path)))
            img_name = image_name_from_dockerfile_path(task_name, base_image_name)

            values[KEY_TASK_IMAGES][task_name] = self.image_tag(
                img_name, build_context_path=task_path, dependencies=values[KEY_TASK_IMAGES].keys())

        return values


def get_included_with_dependencies(values, include):
    app_values = values['apps'].values()
    directly_included = [app for app in app_values if any(
        inc == app[KEY_HARNESS]['name'] for inc in include)]

    dependent = set(include)
    for app in directly_included:
        if app['harness']['dependencies'].get('hard', None):
            dependent.update(set(app[KEY_HARNESS]['dependencies']['hard']))
        if app['harness']['dependencies'].get('soft', None):
            dependent.update(set(app[KEY_HARNESS]['dependencies']['soft']))
        if values['secured_gatekeepers'] and app[KEY_HARNESS]['secured']:
            dependent.add('accounts')
    if len(dependent) == len(include):
        return dependent
    return get_included_with_dependencies(values, dependent)


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
        template_dir = os.path.join(app_path, 'deploy', 'templates')
        if os.path.exists(template_dir):
            dest_dir = os.path.join(
                dest_helm_chart_path, 'templates', app_name)

            logging.info(
                "Collecting templates for application %s to %s", app_name, dest_dir)
            if os.path.exists(dest_dir):
                logging.warning(
                    "Merging/overriding all files in directory %s", dest_dir)
                merge_configuration_directories(template_dir, dest_dir)
            else:
                shutil.copytree(template_dir, dest_dir)
        resources_dir = os.path.join(app_path, 'deploy/resources')
        if os.path.exists(resources_dir):
            dest_dir = os.path.join(
                dest_helm_chart_path, 'resources', app_name)

            logging.info(
                "Collecting resources for application  %s to %s", app_name, dest_dir)

            merge_configuration_directories(resources_dir, dest_dir)

        subchart_dir = os.path.join(app_path, 'deploy/charts')
        if os.path.exists(subchart_dir):
            dest_dir = os.path.join(dest_helm_chart_path, 'charts', app_name)

            logging.info(
                "Collecting templates for application %s to %s", app_name, dest_dir)
            if os.path.exists(dest_dir):
                logging.warning(
                    "Merging/overriding all files in directory %s", dest_dir)
                merge_configuration_directories(subchart_dir, dest_dir)
            else:
                shutil.copytree(subchart_dir, dest_dir)


def copy_merge_base_deployment(dest_helm_chart_path, base_helm_chart):
    if not os.path.exists(base_helm_chart):
        return
    if os.path.exists(dest_helm_chart_path):
        logging.info("Merging/overriding all files in directory %s",
                     dest_helm_chart_path)
        merge_configuration_directories(base_helm_chart, dest_helm_chart_path)
    else:
        logging.info("Copying base deployment chart from %s to %s",
                     base_helm_chart, dest_helm_chart_path)
        shutil.copytree(base_helm_chart, dest_helm_chart_path)


def collect_helm_values(deployment_root, env=()):
    """
    Creates helm values from a cloudharness deployment scaffolding
    """

    values_template_path = os.path.join(
        deployment_root, DEPLOYMENT_CONFIGURATION_PATH, 'values-template.yaml')

    values = get_template(values_template_path)

    for e in env:
        specific_template_path = os.path.join(deployment_root, DEPLOYMENT_CONFIGURATION_PATH,
                                              f'values-template-{e}.yaml')
        if os.path.exists(specific_template_path):
            logging.info(
                "Specific environment values template found: " + specific_template_path)
            with open(specific_template_path) as f:
                values_env_specific = yaml.safe_load(f)
            values = dict_merge(values, values_env_specific)
    return values


def init_app_values(deployment_root, exclude, values=None):
    values = values if values is not None else {}
    app_base_path = os.path.join(deployment_root, APPS_PATH)
    overridden_template_path = os.path.join(
        deployment_root, DEPLOYMENT_CONFIGURATION_PATH, 'value-template.yaml')
    default_values_path = os.path.join(
        CH_ROOT, DEPLOYMENT_CONFIGURATION_PATH, 'value-template.yaml')

    for app_path in get_sub_paths(app_base_path):

        app_name = app_name_from_path(os.path.relpath(app_path, app_base_path))

        if app_name in exclude:
            continue
        app_key = app_name.replace('-', '_')
        if app_key not in values:
            default_values = get_template(default_values_path)
            values[app_key] = default_values
        overridden_defaults = get_template(overridden_template_path)
        values[app_key] = dict_merge(values[app_key], overridden_defaults)

    return values


def values_from_legacy(values):
    if KEY_HARNESS not in values:
        values[KEY_HARNESS] = {}
    harness = values[KEY_HARNESS]
    if KEY_SERVICE not in harness:
        harness[KEY_SERVICE] = {}
    if KEY_DEPLOYMENT not in harness:
        harness[KEY_DEPLOYMENT] = {}
    if KEY_DATABASE not in harness:
        harness[KEY_DATABASE] = {}

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
    if 'image' in harness[KEY_DEPLOYMENT]:
        values['image'] = harness[KEY_DEPLOYMENT]['image']

    values['name'] = harness['name']
    if harness[KEY_DEPLOYMENT].get('port', None):
        values['port'] = harness[KEY_DEPLOYMENT]['port']
    if 'resources' in harness[KEY_DEPLOYMENT]:
        values['resources'] = harness[KEY_DEPLOYMENT]['resources']


def generate_tag_from_content(content_path, ignore=()):
    from dirhash import dirhash
    return dirhash(content_path, 'sha1', ignore=ignore)


def extract_env_variables_from_values(values, envs=tuple(), prefix=''):
    if isinstance(values, dict):
        newenvs = list(envs)
        for key, value in values.items():
            v = extract_env_variables_from_values(
                value, envs, f"{prefix}_{key}".replace('-', '_').upper())
            if key in ('name', 'port', 'subdomain'):
                newenvs.extend(v)
        return newenvs
    else:
        return [env_variable(prefix, values)]


def create_env_variables(values):
    for app_name, value in values[KEY_APPS].items():
        if KEY_HARNESS in value:
            values['env'].extend(extract_env_variables_from_values(
                value[KEY_HARNESS], prefix='CH_' + app_name))
    values['env'].append(env_variable('CH_DOMAIN', values['domain']))
    values['env'].append(env_variable(
        'CH_IMAGE_REGISTRY', values['registry']['name']))
    values['env'].append(env_variable('CH_IMAGE_TAG', values['tag']))


def hosts_info(values):
    domain = values['domain']
    namespace = values['namespace']
    subdomains = [app[KEY_HARNESS]['subdomain'] for app in values[KEY_APPS].values() if
                  KEY_HARNESS in app and app[KEY_HARNESS]['subdomain']] + [alias for app in values[KEY_APPS].values() if
                                                                           KEY_HARNESS in app and app[KEY_HARNESS]['aliases'] for alias in app[KEY_HARNESS]['aliases']]
    try:
        ip = get_cluster_ip()
    except:
        logging.warning('Cannot get cluster ip')
        return
    logging.info(
        "\nTo test locally, update your hosts file" + f"\n{ip}\t{domain + ' ' + ' '.join(sd + '.' + domain for sd in subdomains)}")

    deployments = (app[KEY_HARNESS][KEY_DEPLOYMENT]['name']
                   for app in values[KEY_APPS].values() if KEY_HARNESS in app)

    logging.info(
        "\nTo run locally some apps, also those references may be needed")
    for appname in values[KEY_APPS]:
        app = values[KEY_APPS][appname]['harness']
        if 'deployment' not in app:
            continue
        print(
            "kubectl port-forward -n {namespace} deployment/{app} {port}:{port}".format(
                app=app['deployment']['name'], port=app['deployment']['port'], namespace=namespace))

    print(
        f"127.0.0.1\t{' '.join('%s.%s' % (s, values['namespace']) for s in deployments)}")


class ValuesValidationException(Exception):
    pass


def validate_helm_values(values):
    validate_dependencies(values)


def validate_dependencies(values):
    all_apps = {a for a in values["apps"]}
    for app in all_apps:
        app_values = values["apps"][app]
        if 'dependencies' in app_values[KEY_HARNESS]:
            soft_dependencies = {
                d.replace("-", "_") for d in app_values[KEY_HARNESS]['dependencies']['soft']}
            not_found = {d for d in soft_dependencies if d not in all_apps}
            if not_found:
                logging.warning(
                    f"Soft dependencies specified for application {app} not found: {','.join(not_found)}")
            hard_dependencies = {
                d.replace("-", "_") for d in app_values[KEY_HARNESS]['dependencies']['hard']}
            not_found = {d for d in hard_dependencies if d not in all_apps}
            if not_found:
                raise ValuesValidationException(
                    f"Bad application dependencies specified for application {app}: {','.join(not_found)}")

            build_dependencies = {
                d for d in app_values[KEY_HARNESS]['dependencies']['build']}

            not_found = {
                d for d in build_dependencies if d not in values[KEY_TASK_IMAGES]}
            not_found = {d for d in not_found if d not in all_apps}
            if not_found:
                raise ValuesValidationException(
                    f"Bad build dependencies specified for application {app}: {','.join(not_found)} not found as built image")

        if 'use_services' in app_values[KEY_HARNESS]:
            service_dependencies = {d['name'].replace(
                "-", "_") for d in app_values[KEY_HARNESS]['use_services']}

            not_found = {d for d in service_dependencies if d not in all_apps}
            if not_found:
                raise ValuesValidationException(
                    f"Bad service application dependencies specified for application {app}: {','.join(not_found)}")
