"""
Utilities to create a helm chart from a CloudHarness directory structure
"""
from typing import List, Union
import yaml
import os
import shutil
import logging
from hashlib import sha1
import tarfile
from docker import from_env as DockerClient
from pathlib import Path
import abc

from . import HERE, CH_ROOT
from cloudharness_utils.constants import TEST_IMAGES_PATH, HELM_CHART_PATH, APPS_PATH, HELM_PATH, \
    DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH
from .utils import get_cluster_ip, env_variable, get_sub_paths, guess_build_dependencies_from_dockerfile, image_name_from_dockerfile_path, \
    get_template, merge_configuration_directories, dict_merge, app_name_from_path, \
    find_dockerfiles_paths, get_git_commit_hash


KEY_HARNESS = 'harness'
KEY_SERVICE = 'service'
KEY_DATABASE = 'database'
KEY_DEPLOYMENT = 'deployment'
KEY_APPS = 'apps'
KEY_TASK_IMAGES = 'task-images'
# KEY_TASK_IMAGES_BUILD = f"{KEY_TASK_IMAGES}-build"
KEY_TEST_IMAGES = 'test-images'

DEFAULT_IGNORE = ('/tasks', '.dockerignore', '.hypothesis', "__pycache__", '.node_modules', 'dist', 'build', '.coverage')


class ConfigurationGenerator(object, metaclass=abc.ABCMeta):

    def __init__(self, root_paths: List[str], tag: Union[str, int, None] = 'latest', registry='', local=True, domain=None, exclude=(), secured=True,
                 output_path='./deployment', include: List[str] = None, registry_secret_name: str = None, tls: str = True, env: str = None,
                 namespace: str = None, templates_path: str = HELM_PATH, calculate_hash_tags: bool = False):
        assert domain, 'A domain must be specified'
        self.root_paths = [Path(r) for r in root_paths]
        self.tag = str(tag) if tag else None
        if registry and not registry.endswith('/'):
            self.registry = f'{registry}/'
        else:
            self.registry = registry
        self.local = local
        self.domain = domain
        self.exclude = exclude
        self.secured = secured
        self.output_path = Path(output_path)
        self.include = include
        self.registry_secret_name = registry_secret_name
        self.tls = tls
        self.env = env or {}
        self.namespace = namespace
        self.calculate_hash_tags = calculate_hash_tags

        # In this tree we will collect the  and their parent dependencies
        self.build_tree: dict[str, list[str]] = {}

        self.templates_path = templates_path
        self.dest_deployment_path = self.output_path / templates_path
        self.helm_chart_path = self.dest_deployment_path / 'Chart.yaml'
        self.__init_deployment()

        self.static_images = set()
        self.base_images = {}
        self.all_images = {}

    @abc.abstractmethod
    def create_app_values_spec(self, app_name, app_path, base_image_name=None, helm_values={}):
        ...

    @abc.abstractmethod
    def load_app_values(self, app_name, app_path, helm_values={}):
        """Lightweight loading of app values from deploy/values.yaml.

        Only reads YAML configuration — no Dockerfile discovery, no image tagging.
        Returns values with harness.dependencies and harness.secured populated,
        which is sufficient for include/dependency resolution.
        """
        ...

    @abc.abstractmethod
    def finalize_app_values(self, app_name, app_path, app_values, base_image_name=None, helm_values={}):
        """Expensive finalization of app values for included apps only.

        Performs Dockerfile discovery, image tagging (dirhash), and task image
        processing. Called only for apps that survive the include filter.
        """
        ...

    def __init_deployment(self):
        """
        Create the base helm chart — values files only for the initial phase.
        Templates, files, and resources are deferred to _finalize_base_deployment.
        """
        if self.dest_deployment_path.exists():
            shutil.rmtree(self.dest_deployment_path)
        # Initialize with default
        copy_merge_base_deployment(self.dest_deployment_path, Path(CH_ROOT) / DEPLOYMENT_CONFIGURATION_PATH / self.templates_path, self.env)

        # Override for every cloudharness scaffolding
        for root_path in self.root_paths:
            copy_merge_base_deployment(dest_helm_chart_path=self.dest_deployment_path,
                                       base_helm_chart=root_path / DEPLOYMENT_CONFIGURATION_PATH / self.templates_path, envs=self.env)

    def _adjust_missing_values(self, helm_values):
        if 'name' not in helm_values:
            with open(self.helm_chart_path) as f:
                chart_idx_content = yaml.safe_load(f)
            helm_values['name'] = chart_idx_content['name'].lower()

    def _process_applications(self, helm_values, base_image_name=None):
        for i in range(len(self.root_paths)):
            root_path = self.root_paths[i]
            base_name = base_image_name
            app_values = init_app_values(
                root_path, exclude=self.exclude, values=helm_values[KEY_APPS])
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS],
                                               app_values)

            app_base_path = root_path / APPS_PATH
            app_values = self.collect_app_values(
                app_base_path, base_image_name=base_name, helm_values=helm_values)
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS],
                                               app_values)

    def _load_all_app_values(self, helm_values):
        """Lightweight pass: load deploy/values.yaml for all apps.

        Only reads YAML configuration — no Dockerfile discovery, no image tagging.
        Populates harness.dependencies and harness.secured, which is sufficient
        for include/dependency resolution.
        """
        for root_path in self.root_paths:
            app_values = init_app_values(
                root_path, exclude=self.exclude, values=helm_values[KEY_APPS])
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS], app_values)

            app_base_path = root_path / APPS_PATH
            app_values = self._collect_app_values_lightweight(
                app_base_path, helm_values=helm_values)
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS], app_values)

    def _collect_app_values_lightweight(self, app_base_path, helm_values=None):
        """Collect only YAML-based values for all apps (no image processing)."""
        values = {}
        for app_path in app_base_path.glob("*/"):
            app_name = app_name_from_path(f"{app_path.relative_to(app_base_path)}")
            if app_name in self.exclude:
                continue
            app_values = self.load_app_values(app_name, app_path, helm_values=helm_values)
            values[app_name] = dict_merge(
                values[app_name], app_values) if app_name in values else app_values
        return values

    def _finalize_included_app_values(self, helm_values, base_image_name=None):
        """Expensive pass: run Dockerfile discovery and image tagging for included apps only."""
        included_apps = set(helm_values[KEY_APPS].keys())
        for root_path in self.root_paths:
            app_base_path = root_path / APPS_PATH
            for app_path in app_base_path.glob("*/"):
                app_name = app_name_from_path(f"{app_path.relative_to(app_base_path)}")
                if app_name not in included_apps:
                    continue
                finalized = self.finalize_app_values(
                    app_name, app_path, helm_values[KEY_APPS][app_name],
                    base_image_name=base_image_name, helm_values=helm_values)
                helm_values[KEY_APPS][app_name] = dict_merge(
                    helm_values[KEY_APPS][app_name], finalized)

    def collect_app_values(self, app_base_path, base_image_name=None, helm_values=None):
        values = {}

        for app_path in app_base_path.glob("*/"):  # We get the sub-files that are directories
            app_name = app_name_from_path(f"{app_path.relative_to(app_base_path)}")

            if app_name in self.exclude:
                continue
            app_key = app_name

            app_values = self.create_app_values_spec(app_name, app_path, base_image_name=base_image_name, helm_values=helm_values)

            values[app_key] = dict_merge(
                values[app_key], app_values) if app_key in values else app_values

        return values

    def _init_static_images(self, base_image_name):
        for i in range(len(self.root_paths)):
            root_path = self.root_paths[i]
            base_name = base_image_name
            for static_img_dockerfile in find_dockerfiles_paths(os.path.join(root_path, STATIC_IMAGES_PATH)):
                self.static_images.add(static_img_dockerfile)

                img_name = image_name_from_dockerfile_path(os.path.basename(
                    static_img_dockerfile), base_name=base_name)
                # Static images have context where the Dockerfile is located
                self.base_images[os.path.basename(static_img_dockerfile)] = self.image_tag(
                    img_name, build_context_path=static_img_dockerfile,
                    dependencies=guess_build_dependencies_from_dockerfile(static_img_dockerfile)
                )

    def _assign_static_build_dependencies(self, helm_values):
        static_consumers = {}
        for static_img_dockerfile in self.static_images:
            key = os.path.basename(static_img_dockerfile)
            if key in helm_values[KEY_TASK_IMAGES]:
                dependencies = guess_build_dependencies_from_dockerfile(
                    f"{static_img_dockerfile}")
                for dep in dependencies:
                    if dep in self.exclude and dep in helm_values[KEY_TASK_IMAGES] and key not in self.exclude:
                        static_consumers.setdefault(dep, set()).add(key)
                    if dep in self.base_images and dep not in helm_values[KEY_TASK_IMAGES]:
                        helm_values[KEY_TASK_IMAGES][dep] = self.base_images[dep]
                        # helm_values.setdefault(KEY_TASK_IMAGES_BUILD, {})[dep] = {
                        #     'context': os.path.relpath(static_img_dockerfile, self.dest_deployment_path.parent),
                        #     'dockerfile': 'Dockerfile',
                        # }

        self._prune_excluded_task_images(helm_values, extra_consumers=static_consumers)

    def _get_excluded_task_image_consumers(self, values):
        """Return reverse dependencies for excluded task images from app build deps."""
        task_images = values.get(KEY_TASK_IMAGES, {})
        apps = values.get(KEY_APPS, {})
        consumers = {}

        for app_name, app_values in apps.items():
            if app_name in self.exclude:
                continue
            build_dependencies = app_values.get(KEY_HARNESS, {}).get('dependencies', {}).get('build', [])
            if not build_dependencies:
                continue
            for dep in build_dependencies:
                if dep in self.exclude and dep in task_images:
                    consumers.setdefault(dep, set()).add(app_name)

        return consumers

    def _prune_excluded_task_images(self, values, extra_consumers=None):
        """Exclude task images only when no non-excluded image still depends on them."""
        task_images = values.get(KEY_TASK_IMAGES, {})
        if not task_images:
            return

        consumers = self._get_excluded_task_image_consumers(values)
        if extra_consumers:
            for image_name, image_consumers in extra_consumers.items():
                consumers.setdefault(image_name, set()).update(image_consumers)

        for image_name in list(task_images.keys()):
            if image_name not in self.exclude:
                continue
            used_by = sorted(consumers.get(image_name, set()))
            if used_by:
                logging.warning(
                    "Image %s was excluded but is still required by non-excluded builds: %s. Keeping it.",
                    image_name, ", ".join(used_by)
                )
                continue
            del task_images[image_name]

    def _init_base_images(self, base_image_name):
        """Initialize base images (infrastructure/base-images/) with root context."""
        for i in range(len(self.root_paths)):
            root_path = self.root_paths[i]
            base_name = base_image_name

            for base_img_dockerfile in find_dockerfiles_paths(os.path.join(root_path, BASE_IMAGES_PATH)):
                img_name = image_name_from_dockerfile_path(
                    os.path.basename(base_img_dockerfile), base_name=base_name)
                # Base images have context at root
                self.base_images[os.path.basename(base_img_dockerfile)] = self.image_tag(
                    img_name, build_context_path=root_path,
                    dependencies=guess_build_dependencies_from_dockerfile(base_img_dockerfile)
                )

        return self.base_images

    def _init_test_images(self, base_image_name):
        test_images = {}
        for i in range(len(self.root_paths)):
            root_path = self.root_paths[i]
            base_name = base_image_name

            for base_img_dockerfile in find_dockerfiles_paths(os.path.join(root_path, TEST_IMAGES_PATH)):
                img_name = image_name_from_dockerfile_path(
                    os.path.basename(base_img_dockerfile), base_name=base_name)
                test_images[os.path.basename(base_img_dockerfile)] = self.image_tag(
                    img_name, build_context_path=base_img_dockerfile)

        return test_images

    def _merge_base_helm_values(self, helm_values):
        # Override for every cloudharness scaffolding
        for root_path in self.root_paths:
            helm_values = dict_merge(
                helm_values,
                collect_helm_values(root_path, env=self.env)
            )

        return helm_values

    def _get_default_helm_values(self):
        ch_root_path = Path(CH_ROOT)
        values_yaml_path = ch_root_path / DEPLOYMENT_CONFIGURATION_PATH / HELM_PATH / 'values.yaml'
        helm_values = get_template(values_yaml_path)
        helm_values = dict_merge(helm_values,
                                 collect_helm_values(ch_root_path, env=self.env))

        return helm_values

    def create_tls_certificate(self, helm_values):
        if not self.tls:
            helm_values['tls'] = None
            return
        if not self.local:
            return
        helm_values['tls'] = self.domain.replace(".", "-") + "-tls"

        bootstrap_file = 'bootstrap.sh'
        certs_parent_folder_path = self.output_path / 'helm' / 'resources'
        certs_folder_path = certs_parent_folder_path / 'certs'

        # if os.path.exists(os.path.join(certs_folder_path)):
        if certs_folder_path.exists():
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
        os.chdir(Path(HERE) / 'scripts')
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
        if not certs_folder_path.exists():
            certs_folder_path.mkdir(parents=True)
        certs_tar = certs_parent_folder_path / 'certs.tar'
        with open(certs_tar, 'wb') as f:
            for chunk in bits:
                f.write(chunk)
        cf = tarfile.open(certs_tar)
        cf.extractall(path=certs_parent_folder_path)

        logs = container.logs()
        logging.info(f'openssl container logs: {logs}')

        # stop the container
        container.kill()

        logging.info("Created certificates for local deployment")

    def _clear_unused_db_configuration(self, harness_config):
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

        return self.registry + image_name + (f':{tag}' if tag else '')


def get_included_applications(values, include):
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
    return get_included_applications(values, dependent)


def get_included_builds(values, include):
    app_values = values['apps'].values()
    directly_included = [app for app in app_values if any(
        inc == app[KEY_HARNESS]['name'] for inc in include)]

    dependent = set(include)
    for app in directly_included:
        if app['harness']['dependencies'].get('build', None):
            dependent.update(set(app[KEY_HARNESS]['dependencies']['build']))
        if app['harness']['dependencies'].get('hard', None):
            dependent.update(set(app[KEY_HARNESS]['dependencies']['hard']))
        if app['harness']['dependencies'].get('soft', None):
            dependent.update(set(app[KEY_HARNESS]['dependencies']['soft']))
        if values['secured_gatekeepers'] and app[KEY_HARNESS]['secured']:
            dependent.add('accounts')
    if len(dependent) == len(include):
        return dependent
    return get_included_builds(values, dependent)


def merge_helm_chart(source_templates_path, dest_helm_chart_path=HELM_CHART_PATH):
    pass


def copy_merge_base_deployment(dest_helm_chart_path, base_helm_chart, envs=()):
    if not base_helm_chart.exists():
        return
    if dest_helm_chart_path.exists():
        logging.info("Merging/overriding all files in directory %s",
                     dest_helm_chart_path)
        merge_configuration_directories(f"{base_helm_chart}", f"{dest_helm_chart_path}", envs=envs)
    else:
        logging.info("Copying base deployment chart from %s to %s",
                     base_helm_chart, dest_helm_chart_path)
        shutil.copytree(base_helm_chart, dest_helm_chart_path)


def collect_helm_values(deployment_root, env=()):
    """
    Creates helm values from a cloudharness deployment scaffolding
    """
    values_template_path = deployment_root / DEPLOYMENT_CONFIGURATION_PATH / 'values-template.yaml'

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
        app_key = app_name
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
    content_path = str(content_path)
    ignore = set(ignore)

    # Cloned git repos always live under {content_path}/dependencies/ (possibly
    # nested one extra level, e.g. dependencies/{path}/{repo}).
    # Use their commit hash instead of hashing their content with dirhash.
    git_hashes = []
    dependencies_path = os.path.join(content_path, 'dependencies')
    if os.path.isdir(dependencies_path):
        ignore.add('dependencies')
        for dirpath, dirnames, _ in os.walk(dependencies_path):
            for dirname in list(dirnames):
                subdir = os.path.join(dirpath, dirname)
                if os.path.isdir(os.path.join(subdir, '.git')):
                    dirnames.remove(dirname)  # don't descend into the repo
                    commit_hash = get_git_commit_hash(subdir)
                    if commit_hash:
                        logging.info(f"Using git commit hash {commit_hash} for cloned repo at {subdir}")
                        git_hashes.append(commit_hash)
                    else:
                        logging.warning(f"Could not get git commit hash for repo at {subdir}")

    content_hash = dirhash(content_path, 'sha1', ignore=ignore, allow_cyclic_links=True)

    if git_hashes:
        return sha1((content_hash + ''.join(git_hashes)).encode('utf-8')).hexdigest()
    return content_hash


def extract_env_variables_from_values(values, envs=tuple(), prefix=''):
    if isinstance(values, dict):
        newenvs = list(envs)
        for key, value in values.items():
            v = extract_env_variables_from_values(
                str(value), envs, f"{prefix}_{key}".replace('-', '_').upper())
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
    subdomains = [app[KEY_HARNESS]['subdomain'] for app in values[KEY_APPS].values() if KEY_HARNESS in app and app[KEY_HARNESS]['subdomain']] +\
        [alias for app in values[KEY_APPS].values() if KEY_HARNESS in app and app[KEY_HARNESS]['aliases'] for alias in app[KEY_HARNESS]['aliases']]

    deployments = (app[KEY_HARNESS][KEY_DEPLOYMENT]['name']
                   for app in values[KEY_APPS].values() if KEY_HARNESS in app)

    logging.info(
        "\nTo run locally some apps, also those references may be needed")
    for appname in values[KEY_APPS]:
        app = values[KEY_APPS][appname][KEY_HARNESS]
        if KEY_SERVICE not in app:
            continue
        print(
            "kubectl port-forward -n {namespace} service/{app} {port}:{port}".format(
                app=app[KEY_SERVICE]['name'], port=app[KEY_SERVICE]['port'], namespace=namespace))

    print(
        f"127.0.0.1\t{' '.join('%s.%s' % (values[KEY_APPS][s][KEY_HARNESS][KEY_SERVICE]['name'], values['namespace']) for s in deployments)}")

    try:
        local = values.get('local', False)
        ip = get_cluster_ip(local=local)
    except:
        logging.warning('Cannot get cluster ip')
        ip = "127.0.0.1"
    logging.info(
        "\nTo test locally, update your hosts file" + f"\n{ip}\t{domain + ' ' + ' '.join(sd + '.' + domain for sd in subdomains)}")


class ValuesValidationException(Exception):
    pass


def validate_helm_values(values):
    validate_dependencies(values)


def validate_dependencies(values):
    all_apps = {a for a in values["apps"]}
    for app in all_apps:
        app_values = values["apps"][app]
        app_task_images = set(app_values.get(KEY_TASK_IMAGES, {}))
        if 'dependencies' in app_values[KEY_HARNESS]:
            soft_dependencies = {
                d for d in app_values[KEY_HARNESS]['dependencies']['soft']}
            not_found = {d for d in soft_dependencies if d not in all_apps}
            if not_found:
                logging.warning(
                    f"Soft dependencies specified for application {app} not found: {','.join(not_found)}")
            hard_dependencies = {
                d for d in app_values[KEY_HARNESS]['dependencies']['hard']}
            not_found = {d for d in hard_dependencies if d not in all_apps}
            if not_found:
                raise ValuesValidationException(
                    f"Bad application dependencies specified for application {app}: {','.join(not_found)}")

            build_dependencies = {
                d for d in app_values[KEY_HARNESS]['dependencies']['build']}

            available_builds = set(values.get(KEY_TASK_IMAGES, {})) | all_apps | app_task_images
            not_found = {
                d for d in build_dependencies if d not in available_builds}
            if not_found:
                raise ValuesValidationException(
                    f"Bad build dependencies specified for application {app}: {','.join(not_found)} not found as built image")

        if 'use_services' in app_values[KEY_HARNESS]:
            service_dependencies = {d['name'] for d in app_values[KEY_HARNESS]['use_services']}

            not_found = {d for d in service_dependencies if d not in all_apps}
            if not_found:
                logging.warning(
                    f"Service proxy (use_services) dependencies for application {app} are not deployed: "
                    f"{','.join(not_found)}. Proxies to these services will not be created."
                )


def collect_apps_helm_templates(search_root, dest_helm_chart_path, templates_path=HELM_PATH, exclude=(), include=None, envs=()):
    """
    Searches recursively for helm templates inside the applications and collects the templates in the destination

    :param search_root:
    :param dest_helm_chart_path: collected helm templates destination folder
    :param exclude:
    :return:
    """
    app_base_path = search_root / APPS_PATH

    for app_path in app_base_path.glob("*/"):  # We get the sub-files that are directories
        app_name = app_name_from_path(os.path.relpath(f"{app_path}", app_base_path))
        if app_name in exclude or (include and not any(inc in app_name for inc in include)):
            continue

        # Determine which template directory to use
        regular_template_dir = app_path / 'deploy' / 'templates'
        if templates_path == HELM_PATH:
            template_dir = regular_template_dir
        else:
            template_dir = app_path / 'deploy' / f'templates-{templates_path}'

        if template_dir.exists():
            dest_dir = dest_helm_chart_path / 'templates' / app_name

            logging.info(
                "Collecting templates for application %s to %s", app_name, dest_dir)
            if dest_dir.exists():
                logging.warning(
                    "Merging/overriding all files in directory %s", dest_dir)
                merge_configuration_directories(f"{template_dir}", f"{dest_dir}", envs)
            else:
                shutil.copytree(template_dir, dest_dir)
            if envs:
                merge_configuration_directories(f"{dest_dir}", f"{dest_dir}", envs)

        # For non-helm mode (e.g., compose), also copy helper templates (_*.tpl) from regular
        # templates directory. These are needed because resources (e.g., realm.json) may reference
        # template helpers defined there.
        if templates_path != HELM_PATH and regular_template_dir.exists():
            helper_files = list(regular_template_dir.glob("_*.tpl"))
            if helper_files:
                dest_dir = dest_helm_chart_path / 'templates' / app_name
                dest_dir.mkdir(parents=True, exist_ok=True)
                logging.info(
                    "Collecting helper templates for application %s to %s", app_name, dest_dir)
                for helper_file in helper_files:
                    dest_file = dest_dir / helper_file.name
                    if not dest_file.exists():  # Don't overwrite if templates-{path} provided one
                        shutil.copy(helper_file, dest_file)

        resources_dir = app_path / 'deploy' / 'resources'
        if resources_dir.exists():
            dest_dir = dest_helm_chart_path / 'resources' / app_name

            logging.info(
                "Collecting resources for application  %s to %s", app_name, dest_dir)

            merge_configuration_directories(f"{resources_dir}", f"{dest_dir}", envs)
            if envs:
                merge_configuration_directories(f"{dest_dir}", f"{dest_dir}", envs)

        if templates_path == HELM_PATH:
            subchart_dir = app_path / 'deploy/charts'
            if subchart_dir.exists():
                dest_dir = dest_helm_chart_path / 'charts' / app_name

                logging.info(
                    "Collecting templates for application %s to %s", app_name, dest_dir)
                if dest_dir.exists():
                    logging.warning(
                        "Merging/overriding all files in directory %s", dest_dir)
                    merge_configuration_directories(f"{subchart_dir}", f"{dest_dir}", envs)
                else:
                    shutil.copytree(subchart_dir, dest_dir)
                if envs:
                    merge_configuration_directories(f"{dest_dir}", f"{dest_dir}", envs)


# def collect_apps_helm_templates(search_root, dest_helm_chart_path, templates_path=None, exclude=(), include=None):
#     """
#     Searches recursively for helm templates inside the applications and collects the templates in the destination

#     :param search_root:
#     :param dest_helm_chart_path: collected helm templates destination folder
#     :param exclude:
#     :return:
#     """
#     app_base_path = os.path.join(search_root, APPS_PATH)

#     import ipdb; ipdb.set_trace()  # fmt: skip

#     for app_path in get_sub_paths(app_base_path):
#         app_name = app_name_from_path(os.path.relpath(app_path, app_base_path))
#         if app_name in exclude or (include and not any(inc in app_name for inc in include)):
#             continue
#         template_dir = os.path.join(app_path, 'deploy', 'templates')
#         if os.path.exists(template_dir):
#             dest_dir = os.path.join(
#                 dest_helm_chart_path, 'templates', app_name)

#             logging.info(
#                 "Collecting templates for application %s to %s", app_name, dest_dir)
#             if os.path.exists(dest_dir):
#                 logging.warning(
#                     "Merging/overriding all files in directory %s", dest_dir)
#                 merge_configuration_directories(template_dir, dest_dir)
#             else:
#                 shutil.copytree(template_dir, dest_dir)
#         resources_dir = os.path.join(app_path, 'deploy/resources')
#         if os.path.exists(resources_dir):
#             dest_dir = os.path.join(
#                 dest_helm_chart_path, 'resources', app_name)

#             logging.info(
#                 "Collecting resources for application  %s to %s", app_name, dest_dir)

#             merge_configuration_directories(resources_dir, dest_dir)

#         subchart_dir = os.path.join(app_path, 'deploy/charts')
#         if os.path.exists(subchart_dir):
#             dest_dir = os.path.join(dest_helm_chart_path, 'charts', app_name)

#             logging.info(
#                 "Collecting templates for application %s to %s", app_name, dest_dir)
#             if os.path.exists(dest_dir):
#                 logging.warning(
#                     "Merging/overriding all files in directory %s", dest_dir)
#                 merge_configuration_directories(subchart_dir, dest_dir)
#             else:
#                 shutil.copytree(subchart_dir, dest_dir)
