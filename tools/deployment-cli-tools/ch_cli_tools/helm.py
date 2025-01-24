"""
Utilities to create a helm chart from a CloudHarness directory structure
"""
from typing import Union
import yaml
import os
import logging
from hashlib import sha1
import subprocess

from cloudharness_utils.constants import VALUES_MANUAL_PATH, HELM_CHART_PATH
from .utils import get_cluster_ip, get_git_commit_hash, image_name_from_dockerfile_path, \
    get_template, merge_to_yaml_file, dict_merge, app_name_from_path, \
    find_dockerfiles_paths

from .models import HarnessMainConfig

from .configurationgenerator import ConfigurationGenerator, validate_helm_values, \
    KEY_HARNESS, KEY_SERVICE, KEY_DATABASE, KEY_APPS, KEY_TASK_IMAGES, KEY_TEST_IMAGES, KEY_DEPLOYMENT, DEFAULT_IGNORE, \
    values_from_legacy, values_set_legacy, get_included_with_dependencies, create_env_variables, collect_apps_helm_templates, generate_tag_from_content, guess_build_dependencies_from_dockerfile


def deploy(namespace, output_path='./deployment'):
    helm_path = os.path.join(output_path, HELM_CHART_PATH)
    logging.info('Deploying helm chart %s', helm_path)
    subprocess.run("helm dependency update".split(), cwd=helm_path)

    subprocess.run(
        f"helm upgrade {namespace} {helm_path} -n {namespace} --install --reset-values".split())


def create_helm_chart(root_paths, tag: Union[str, int, None] = 'latest', registry='', local=True, domain=None, exclude=(), secured=True,
                      output_path='./deployment', include=None, registry_secret=None, tls=True, env=None,
                      namespace=None) -> HarnessMainConfig:
    if (type(env)) == str:
        env = [env]
    return CloudHarnessHelm(root_paths, tag=tag, registry=registry, local=local, domain=domain, exclude=exclude, secured=secured,
                            output_path=output_path, include=include, registry_secret=registry_secret, tls=tls, env=env,
                            namespace=namespace).process_values()


class CloudHarnessHelm(ConfigurationGenerator):

    def process_values(self) -> HarnessMainConfig:
        """
        Creates values file for the helm chart
        """
        helm_values = self._get_default_helm_values()

        self._adjust_missing_values(helm_values)

        helm_values = self._merge_base_helm_values(helm_values)

        helm_values[KEY_APPS] = {}

        base_image_name = helm_values['name']

        helm_values[KEY_TASK_IMAGES] = {}

        self._init_base_images(base_image_name)
        self._init_static_images(base_image_name)
        helm_values[KEY_TEST_IMAGES] = self._init_test_images(base_image_name)

        self._process_applications(helm_values, base_image_name)

        self.create_tls_certificate(helm_values)

        values, include = self.__finish_helm_values(values=helm_values)

        # Adjust dependencies from static (common) images
        self._assign_static_build_dependencies(helm_values)

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
        values['build_hash'] = get_git_commit_hash(self.root_paths[-1])  # Fix: Call the defined function to get the git commit hash
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

            self._clear_unused_db_configuration(harness)
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

    def create_app_values_spec(self, app_name, app_path, base_image_name=None, helm_values={}):
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

        deployment_values = values[KEY_HARNESS].get(KEY_DEPLOYMENT, {})
        deployment_image = deployment_values.get('image', None) or values.get('image', None)
        values['build'] = not bool(deployment_image)  # Used by skaffold and ci/cd to determine if the image should be built
        if len(image_paths) > 0 and not deployment_image:
            image_name = image_name_from_dockerfile_path(os.path.relpath(
                image_paths[0], os.path.dirname(app_path)), base_image_name)
            deployment_values['image'] = self.image_tag(
                image_name, build_context_path=app_path, dependencies=build_dependencies)
        elif KEY_HARNESS in values and not deployment_image and values[
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
