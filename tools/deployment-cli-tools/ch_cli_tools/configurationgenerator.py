"""
Utilities to create a helm chart from a CloudHarness directory structure
"""
from typing import Union
import yaml
import os
import shutil
import logging
from hashlib import sha1
import tarfile
from docker import from_env as DockerClient
from pathlib import Path


from . import HERE, CH_ROOT
from cloudharness_utils.constants import TEST_IMAGES_PATH, HELM_CHART_PATH, APPS_PATH, HELM_PATH, \
    DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH
from .utils import get_cluster_ip, env_variable, get_sub_paths, guess_build_dependencies_from_dockerfile, image_name_from_dockerfile_path, \
    get_template, merge_configuration_directories, dict_merge, app_name_from_path, \
    find_dockerfiles_paths


KEY_HARNESS = 'harness'
KEY_SERVICE = 'service'
KEY_DATABASE = 'database'
KEY_DEPLOYMENT = 'deployment'
KEY_APPS = 'apps'
KEY_TASK_IMAGES = 'task-images'
# KEY_TASK_IMAGES_BUILD = f"{KEY_TASK_IMAGES}-build"
KEY_TEST_IMAGES = 'test-images'

DEFAULT_IGNORE = ('/tasks', '.dockerignore', '.hypothesis', "__pycache__", '.node_modules', 'dist', 'build', '.coverage')


class ConfigurationGenerator(object):
    def __init__(self, root_paths, tag: Union[str, int, None] = 'latest', registry='', local=True, domain=None, exclude=(), secured=True,
                 output_path='./deployment', include=None, registry_secret=None, tls=True, env=None,
                 namespace=None, templates_path=HELM_PATH):
        assert domain, 'A domain must be specified'
        self.root_paths = [Path(r) for r in root_paths]
        self.tag = tag
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
        self.registry_secret = registry_secret
        self.tls = tls
        self.env = env or {}
        self.namespace = namespace

        self.templates_path = templates_path
        self.dest_deployment_path = self.output_path / templates_path
        self.helm_chart_path = self.dest_deployment_path / 'Chart.yaml'
        self.__init_deployment()

        self.static_images = set()
        self.base_images = {}
        self.all_images = {}

    def __init_deployment(self):
        """
        Create the base helm chart
        """
        if self.dest_deployment_path.exists():
            shutil.rmtree(self.dest_deployment_path)
        # Initialize with default
        copy_merge_base_deployment(self.dest_deployment_path, Path(CH_ROOT) / DEPLOYMENT_CONFIGURATION_PATH / self.templates_path)

        # Override for every cloudharness scaffolding
        for root_path in self.root_paths:
            copy_merge_base_deployment(dest_helm_chart_path=self.dest_deployment_path,
                                       base_helm_chart=root_path / DEPLOYMENT_CONFIGURATION_PATH / self.templates_path)
            collect_apps_helm_templates(root_path, exclude=self.exclude, include=self.include,
                                        dest_helm_chart_path=self.dest_deployment_path, templates_path=self.templates_path)

    def _adjust_missing_values(self, helm_values):
        if 'name' not in helm_values:
            with open(self.helm_chart_path) as f:
                chart_idx_content = yaml.safe_load(f)
            helm_values['name'] = chart_idx_content['name'].lower()

    def _process_applications(self, helm_values, base_image_name):
        for root_path in self.root_paths:
            app_values = init_app_values(
                root_path, exclude=self.exclude, values=helm_values[KEY_APPS])
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS],
                                               app_values)

            app_base_path = root_path / APPS_PATH
            app_values = self.collect_app_values(
                app_base_path, base_image_name=base_image_name)
            helm_values[KEY_APPS] = dict_merge(helm_values[KEY_APPS],
                                               app_values)

    def collect_app_values(self, app_base_path, base_image_name=None):
        values = {}

        for app_path in app_base_path.glob("*/"):  # We get the sub-files that are directories
            app_name = app_name_from_path(f"{app_path.relative_to(app_base_path)}")

            if app_name in self.exclude:
                continue
            app_key = app_name.replace('-', '_')

            app_values = self.create_app_values_spec(app_name, app_path, base_image_name=base_image_name)

            # dockerfile_path = next(app_path.rglob('**/Dockerfile'), None)
            # # for dockerfile_path in app_path.rglob('**/Dockerfile'):
            # #     parent_name = dockerfile_path.parent.name.replace("-", "_")
            # #     if parent_name == app_key:
            # #         app_values['build'] = {
            # #             # 'dockerfile': f"{dockerfile_path.relative_to(app_path)}",
            # #             'dockerfile': "Dockerfile",
            # #             'context': os.path.relpath(dockerfile_path.parent, self.dest_deployment_path.parent),
            # #         }
            # #     elif "tasks/" in f"{dockerfile_path}":
            # #         parent_name = parent_name.upper()
            # #         values.setdefault("task-images-build", {})[parent_name] = {
            # #             'dockerfile': "Dockerfile",
            # #             'context': os.path.relpath(dockerfile_path.parent, self.dest_deployment_path.parent),
            # #         }
            # #         import ipdb; ipdb.set_trace()  # fmt: skip

            # if dockerfile_path:
            #     app_values['build'] = {
            #         # 'dockerfile': f"{dockerfile_path.relative_to(app_path)}",
            #         'dockerfile': "Dockerfile",
            #         'context': os.path.relpath(dockerfile_path.parent, self.dest_deployment_path.parent),
            #     }

            values[app_key] = dict_merge(
                values[app_key], app_values) if app_key in values else app_values

        return values

    def _init_static_images(self, base_image_name):
        for static_img_dockerfile in self.static_images:
            img_name = image_name_from_dockerfile_path(os.path.basename(
                static_img_dockerfile), base_name=base_image_name)
            self.base_images[os.path.basename(static_img_dockerfile)] = self.image_tag(
                img_name, build_context_path=static_img_dockerfile,
                dependencies=guess_build_dependencies_from_dockerfile(static_img_dockerfile)
            )

    def _assign_static_build_dependencies(self, helm_values):
        for static_img_dockerfile in self.static_images:
            key = os.path.basename(static_img_dockerfile)
            if key in helm_values[KEY_TASK_IMAGES]:
                dependencies = guess_build_dependencies_from_dockerfile(
                    f"{static_img_dockerfile}")
                for dep in dependencies:
                    if dep in self.base_images and dep not in helm_values[KEY_TASK_IMAGES]:
                        helm_values[KEY_TASK_IMAGES][dep] = self.base_images[dep]
                        # helm_values.setdefault(KEY_TASK_IMAGES_BUILD, {})[dep] = {
                        #     'context': os.path.relpath(static_img_dockerfile, self.dest_deployment_path.parent),
                        #     'dockerfile': 'Dockerfile',
                        # }

        for image_name in list(helm_values[KEY_TASK_IMAGES].keys()):
            if image_name in self.exclude:
                del helm_values[KEY_TASK_IMAGES][image_name]
                # del helm_values[KEY_TASK_IMAGES_BUILD][image_name]

    def _init_base_images(self, base_image_name):

        for root_path in self.root_paths:
            for base_img_dockerfile in self.__find_static_dockerfile_paths(root_path):
                img_name = image_name_from_dockerfile_path(
                    os.path.basename(base_img_dockerfile), base_name=base_image_name)
                self.base_images[os.path.basename(base_img_dockerfile)] = self.image_tag(
                    img_name, build_context_path=root_path,
                    dependencies=guess_build_dependencies_from_dockerfile(base_img_dockerfile)
                )

            self.static_images.update(find_dockerfiles_paths(
                os.path.join(root_path, STATIC_IMAGES_PATH)))
        return self.base_images

    def _init_test_images(self, base_image_name):
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
            tag = sha1((tag + "".join(self.all_images.get(n, '') for n in dependencies)).encode("utf-8")).hexdigest()
            logging.info(f"Generated tag: {tag}")
            app_name = image_name.split("/")[-1]  # the image name can have a prefix
            self.all_images[app_name] = tag
        return self.registry + image_name + (f':{tag}' if tag else '')


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


def copy_merge_base_deployment(dest_helm_chart_path, base_helm_chart):
    if not base_helm_chart.exists():
        return
    if dest_helm_chart_path.exists():
        logging.info("Merging/overriding all files in directory %s",
                     dest_helm_chart_path)
        merge_configuration_directories(f"{base_helm_chart}", f"{dest_helm_chart_path}")
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


def collect_apps_helm_templates(search_root, dest_helm_chart_path, templates_path=HELM_PATH, exclude=(), include=None):
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
        if templates_path == HELM_PATH:
            template_dir = app_path / 'deploy' / 'templates'
        else:
            template_dir = app_path / 'deploy' / f'templates-{templates_path}'
        if template_dir.exists():
            dest_dir = dest_helm_chart_path / 'templates' / app_name

            logging.info(
                "Collecting templates for application %s to %s", app_name, dest_dir)
            if dest_dir.exists():
                logging.warning(
                    "Merging/overriding all files in directory %s", dest_dir)
                merge_configuration_directories(f"{template_dir}", f"{dest_dir}")
            else:
                shutil.copytree(template_dir, dest_dir)
        resources_dir = app_path / 'deploy' / 'resources'
        if resources_dir.exists():
            dest_dir = dest_helm_chart_path / 'resources' / app_name

            logging.info(
                "Collecting resources for application  %s to %s", app_name, dest_dir)

            merge_configuration_directories(f"{resources_dir}", f"{dest_dir}")

        if templates_path == HELM_PATH:
            subchart_dir = app_path / 'deploy/charts'
            if subchart_dir.exists():
                dest_dir = dest_helm_chart_path / 'charts' / app_name

                logging.info(
                    "Collecting templates for application %s to %s", app_name, dest_dir)
                if dest_dir.exists():
                    logging.warning(
                        "Merging/overriding all files in directory %s", dest_dir)
                    merge_configuration_directories(f"{subchart_dir}", f"{dest_dir}")
                else:
                    shutil.copytree(subchart_dir, dest_dir)


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
