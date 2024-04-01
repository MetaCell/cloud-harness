"""
Utilities to create a helm chart from a CloudHarness directory structure
"""
from typing import Union
import yaml
from ruamel.yaml import YAML
import os
import logging
import subprocess
import copy


from cloudharness_utils.constants import VALUES_MANUAL_PATH, COMPOSE
from .utils import get_cluster_ip, image_name_from_dockerfile_path, get_template, \
    merge_to_yaml_file, dict_merge, app_name_from_path, find_dockerfiles_paths, find_file_paths

from .models import HarnessMainConfig

from .configurationgenerator import ConfigurationGenerator, validate_helm_values, KEY_HARNESS, KEY_SERVICE, KEY_DATABASE, KEY_APPS, KEY_TASK_IMAGES, KEY_TEST_IMAGES, KEY_DEPLOYMENT, values_from_legacy, values_set_legacy, get_included_with_dependencies, create_env_variables, collect_apps_helm_templates


def create_docker_compose_configuration(root_paths, tag: Union[str, int, None]='latest', registry='', local=True, domain=None, exclude=(), secured=True,
                      output_path='./deployment', include=None, registry_secret=None, tls=True, env=None,
                      namespace=None) -> HarnessMainConfig:
    if (type(env)) == str:
        env = [env]
    return CloudHarnessDockerCompose(root_paths, tag=tag, registry=registry, local=local, domain=domain, exclude=exclude, secured=secured,
                            output_path=output_path, include=include, registry_secret=registry_secret, tls=tls, env=env,
                            namespace=namespace, templates_path=COMPOSE).process_values()


class CloudHarnessDockerCompose(ConfigurationGenerator):

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

        # self.create_tls_certificate(helm_values)

        values, include = self.__finish_helm_values(values=helm_values)

        # Adjust dependencies from static (common) images
        self._assign_static_build_dependencies(helm_values)

        for root_path in self.root_paths:
            collect_apps_helm_templates(root_path, exclude=self.exclude, include=self.include,
                                        dest_helm_chart_path=self.dest_deployment_path, templates_path=self.templates_path)

        # Save values file for manual helm chart
        merged_values = merge_to_yaml_file(helm_values, self.dest_deployment_path / VALUES_MANUAL_PATH)
        if self.namespace:
            merge_to_yaml_file({'metadata': {'namespace': self.namespace},
                                'name': helm_values['name']}, self.helm_chart_path)
        validate_helm_values(merged_values)

        # All values save
        all_values = self.__get_default_helm_values_with_secrets(merged_values)

        merge_to_yaml_file(all_values, self.dest_deployment_path / 'allvalues.yaml')

        self.generate_docker_compose_yaml()

        return HarnessMainConfig.from_dict(merged_values)

    def generate_docker_compose_yaml(self):
        compose_templates = self.dest_deployment_path
        dest_compose_yaml = self.dest_deployment_path.parent / "docker-compose.yaml"

        logging.info(f'Generate docker compose configuration in: {dest_compose_yaml}, using templates from {compose_templates}')
        command = f"helm template {compose_templates} > {dest_compose_yaml}"

        subprocess.call(command, shell=True)

        self.__post_process_multiple_document_docker_compose(dest_compose_yaml)

    def __post_process_multiple_document_docker_compose(self, yaml_document):
        if not yaml_document.exists():
            logging.warning("Something went wrong during the docker-compose.yaml generation, cannot post-process it")
            return

        yaml_handler = YAML()
        documents = yaml_handler.load_all(yaml_document)

        main_document = None
        for document in documents:
            if not document:
                continue
            if "cloudharness-metadata" in document:
                document_path = self.dest_deployment_path / document["cloudharness-metadata"]["path"]
                logging.info("Post-process docker-compose.yaml, creating %s", document_path)
                document_path.parent.mkdir(parents=True, exist_ok=True)
                data = document["data"]
                document_path.write_text(data)
            else:
                # We need to save the main document later
                # "load_all" returns a generator over the file,
                # so if we modify it while looping on "documents"
                # the output will be affected (probably truncated for some outputs)
                main_document = document  # we need to save the main document later
        yaml_handler.dump(main_document, yaml_document)

    def __get_default_helm_values_with_secrets(self, helm_values):
        helm_values = copy.deepcopy(helm_values)
        # {{- $values_copy := deepCopy .Values }}
        # {{- range $key, $val := .Values.apps }}
        #   {{- $new_secrets := dict "apps" (dict $key (dict "harness" (dict "secrets"))) }}
        #   {{- $tmp := mergeOverwrite $values_copy $new_secrets }}
        # {{- end }}
        # {{ $values_copy | toYaml | indent 4 }}
        for key, val in helm_values['apps'].items():
            helm_values['apps'][key]['harness']['secrets'] = {}
        return helm_values

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

    def create_app_values_spec(self, app_name, app_path, base_image_name=None):
        logging.info('Generating values script for ' + app_name)

        deploy_path = app_path / 'deploy'
        specific_template_path = deploy_path / 'values.yaml'
        if specific_template_path.exists():
            logging.info(f"Specific values template found: {specific_template_path}")
            values = get_template(specific_template_path)
        else:
            values = {}

        for e in self.env:
            specific_template_path = deploy_path / f'values-{e}.yaml'
            if specific_template_path.exists():
                logging.info(
                    f"Specific environment values template found: {specific_template_path}")
                with open(specific_template_path) as f:
                    values_env_specific = yaml.safe_load(f)
                values = dict_merge(values, values_env_specific)

        if KEY_HARNESS in values and 'name' in values[KEY_HARNESS] and values[KEY_HARNESS]['name']:
            logging.warning('Name is automatically set in applications: name %s will be ignored',
                            values[KEY_HARNESS]['name'])

        image_paths = [path for path in find_dockerfiles_paths(
            app_path) if 'tasks/' not in path and 'subapps' not in path]

        # Inject entry points commands
        for image_path in image_paths:
            self.inject_entry_points_commands(values, image_path, app_path)

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
                task_path, app_path.parent))
            img_name = image_name_from_dockerfile_path(task_name, base_image_name)

            # values[KEY_TASK_IMAGES][task_name] = self.image_tag(
            #     img_name, build_context_path=task_path, dependencies=values[KEY_TASK_IMAGES].keys())
            # values.setdefault(KEY_TASK_IMAGES_BUILD, {})[task_name] = {
            #     'context': os.path.relpath(task_path, self.dest_deployment_path.parent),
            #     'dockerfile': 'Dockerfile',
            # }

            # values[KEY_TASK_IMAGES][task_name] = {
            #     'name': self.image_tag(img_name, build_context_path=task_path, dependencies=values[KEY_TASK_IMAGES].keys()),
            #     # 'context': os.path.relpath(task_path, self.dest_deployment_path.parent),
            #     # 'dockerfile': 'Dockerfile',
            # }

            values[KEY_TASK_IMAGES][task_name] = self.image_tag(img_name, build_context_path=task_path, dependencies=values[KEY_TASK_IMAGES].keys())

        return values


    def inject_entry_points_commands(self, helm_values, image_path, app_path):
        context_path = os.path.relpath(image_path, '.')

        mains_candidates = find_file_paths(context_path, '__main__.py')

        task_main_file = identify_unicorn_based_main(mains_candidates, app_path)

        if task_main_file:
            helm_values[KEY_HARNESS]['deployment']['command'] = 'python'
            helm_values[KEY_HARNESS]['deployment']['args'] = f'/usr/src/app/{os.path.basename(task_main_file)}/__main__.py'


def identify_unicorn_based_main(candidates, app_path):
        import re
        gunicorn_pattern = re.compile(r"gunicorn")
        # sort candidates, shortest path first
        for candidate in sorted(candidates,key=lambda x: len(x.split("/"))):
            dockerfile_path = f"{candidate}/.."
            while not os.path.exists(f"{dockerfile_path}/Dockerfile") and os.path.abspath(dockerfile_path) != os.path.abspath(app_path):
                dockerfile_path += "/.."
            dockerfile = f"{dockerfile_path}/Dockerfile"
            if not os.path.exists(dockerfile):
                continue
            with open(dockerfile, 'r') as file:
                if re.search(gunicorn_pattern, file.read()):
                    return candidate
            requirements = f"{candidate}/../requirements.txt"
            if not os.path.exists(requirements):
                continue
            with open(requirements, 'r') as file:
                if re.search(gunicorn_pattern, file.read()):
                    return candidate
        return None