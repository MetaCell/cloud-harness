"""Application instances.

An instance is a separate deployment of an application, declared as a directory under the
application's `deploy/instances`. It is served on its own subdomain and gets its own service,
deployment, database, volume and secrets, while running the image built for the application and
inheriting its whole configuration, resources and templates.

An instance is read together with the application declaring it and added to the deployment right
away as the application `[application]-[instance]`, derived from the application's values merged
so far. From then on it is an application like any other: it is merged root path by root path,
named, filtered and rendered the same way. Nothing in the values tells an instance apart from an
application: the directories under `deploy/instances` are the only record of what is an instance.
"""

import copy
import logging
from pathlib import Path

from cloudharness_utils.constants import APPS_PATH
from ..constants import KEY_DATABASE, KEY_DEPLOYMENT, KEY_HARNESS, KEY_SERVICE, KEY_TASK_IMAGES
from ..common_types import ValuesValidationException
from ..utils import app_name_from_path, dict_merge, yaml


# Directory of an application holding its instances, one sub-directory each
INSTANCES_PATH = 'instances'

# Everything that maps an application to a host: an instance serves its own subdomain, and
# inheriting these would make it claim the parent's hosts with a different backend.
INSTANCE_HOST_KEYS = ('subdomain', 'aliases', 'domain')

# Resource names are derived from the application key. Dropping the parent's lets an instance
# get its own service, deployment and database instead of colliding with the parent's.
INSTANCE_NAMED_RESOURCES = (KEY_SERVICE, KEY_DEPLOYMENT, KEY_DATABASE)


def instance_app_key(app_name, instance_name):
    """Application key an instance is deployed under: instances are applications in their own right.

    The key is what the whole deployment is built around: resources and templates are collected
    under it, and the service, deployment, database and gatekeeper are named after it.
    """
    return f"{app_name}-{instance_name}"


def instances_path(app_path):
    """Directory holding the instances of an application."""
    return Path(app_path) / 'deploy' / INSTANCES_PATH


def instance_values_files(instance_path, envs=()):
    """The values files declaring an instance for the given environments, in merge order:
    `values.yaml`, then `values-[env].yaml` for each environment."""
    return [path for path in [instance_path / 'values.yaml', *(instance_path / f'values-{env}.yaml' for env in envs)]
            if path.exists()]


def instance_directories(app_path, envs=()):
    """The instance directories of an application declared for the given environments, by name.

    An instance is declared by its values files: `values.yaml` deploys it in every environment,
    `values-[env].yaml` alone only in that environment. A directory declaring neither is skipped.
    """
    directories = {}
    for path in sorted(instances_path(app_path).glob("*/")):
        if not path.is_dir() or path.name.startswith('.'):
            continue
        if not instance_values_files(path, envs):
            logging.info("Instance %s declares no values for the current environments, skipping", path)
            continue
        directories[app_name_from_path(f"{path.name}")] = path
    return directories


def instance_names(app_name, root_paths, envs=()):
    """Names of the instances an application declares in any root path."""
    return {name for root_path in root_paths
            for name in instance_directories(Path(root_path) / APPS_PATH / app_name, envs)}


def application_names(root_paths):
    """Names of the applications found in any root path."""
    return {app_name_from_path(f"{path.name}") for root_path in root_paths
            for path in (Path(root_path) / APPS_PATH).glob("*/") if path.is_dir()}


def instance_sets(instance_values, *path):
    """Whether an instance defines a value of its own at the given path of its configuration.

    Presence, not truthiness: an instance explicitly declaring an empty value (e.g.
    `connect_string: ""` as a deliberate opt-out) still counts as declaring it.
    """
    node = instance_values
    for key in path[:-1]:
        if not isinstance(node, dict):
            return False
        node = node.get(key)
    return isinstance(node, dict) and path[-1] in node


def build_instance_values(app_values, parent_name, instance_name, instance_values):
    """Application values of a single instance: the parent's configuration, stripped of what
    identifies the parent, with the instance's own values merged on top.

    The merge follows `dict_merge`: mappings are merged key by key, lists (`env`,
    `uri_role_mapping`, `aliases`, ...) are replaced wholesale by the instance's.
    """
    instance_app = copy.deepcopy(app_values)
    harness = instance_app.setdefault(KEY_HARNESS, {})

    for key in INSTANCE_HOST_KEYS:
        harness.pop(key, None)
    harness.pop('name', None)
    for key in INSTANCE_NAMED_RESOURCES:
        resource = harness.get(key)
        if isinstance(resource, dict):
            resource.pop('name', None)

    instance_app = dict_merge(instance_app, instance_values)
    harness = instance_app[KEY_HARNESS]

    # An instance is reached on its own subdomain: without one of its own it answers on its
    # directory's name, so that an empty values file is enough to deploy it. An instance
    # declaring `subdomain: null` opts out and gets no ingress.
    if 'subdomain' not in (instance_values.get(KEY_HARNESS) or {}):
        harness['subdomain'] = instance_name

    # An automatic volume is a claim created for the application: left inherited, the instance
    # would mount the parent's storage. Named after the instance, it gets a claim of its own. A
    # volume that is not automatic is a pre-existing claim, shared like between any applications.
    volume = (harness.get(KEY_DEPLOYMENT) or {}).get('volume') or {}
    if volume.get('name') and volume.get('auto', True) \
            and not instance_sets(instance_values, KEY_HARNESS, KEY_DEPLOYMENT, 'volume', 'name'):
        volume['name'] = f"{instance_name}-{volume['name']}"

    # A connection string points at one database: inherited, it would connect the instance to the
    # parent's. Emptied, it keeps the parent's intent of an externally managed database while
    # requiring a value of its own, the way an application declaring `connect_string: ""` does.
    database = harness.get(KEY_DATABASE) or {}
    if database.get('connect_string') and not instance_sets(instance_values, KEY_HARNESS, KEY_DATABASE, 'connect_string'):
        database['connect_string'] = ''

    # An instance declaring the parent's database name shares its database server. Its initial
    # database is then named after the instance application, so that it never gets the parent's
    # data. Hyphens become underscores: database identifiers with hyphens need quoting in SQL.
    parent_database = (app_values.get(KEY_HARNESS) or {}).get(KEY_DATABASE) or {}
    if database.get('name') and database['name'] == (parent_database.get('name') or f"{parent_name}-db"):
        for database_type, type_config in database.items():
            if isinstance(type_config, dict) and type_config.get('initialdb') \
                    and not instance_sets(instance_values, KEY_HARNESS, KEY_DATABASE, database_type, 'initialdb'):
                type_config['initialdb'] = instance_app_key(parent_name, instance_name).replace('-', '_')

    # The instance runs the parent's image, inherited with the rest of the configuration: it is
    # never built on its own, and the task images produced by the parent's build belong to the
    # parent alone.
    instance_app['build'] = False
    instance_app[KEY_TASK_IMAGES] = {}

    return instance_app


def inherit_parent_image(instance_app, parent_app):
    """Give an instance the image of its parent application, unless it pins one of its own.

    An instance inherits the image with the rest of the parent's values, but with `--include` the
    image is only computed when the included applications are finalized, after the instance has
    been derived from them.
    """
    parent_harness_image = ((parent_app.get(KEY_HARNESS) or {}).get(KEY_DEPLOYMENT) or {}).get('image')
    image = instance_app.get('image') or parent_app.get('image') or parent_harness_image
    if not image:
        return
    instance_app['image'] = image
    deployment = instance_app.setdefault(KEY_HARNESS, {}).setdefault(KEY_DEPLOYMENT, {})
    if not deployment.get('image'):
        deployment['image'] = image


def check_instance_collisions(root_paths, exclude=(), envs=()):
    """Check that no instance and application are deployed under the same key, as merging their
    values into one would silently deploy neither."""
    applications = application_names(root_paths) - set(exclude)
    for app_name in applications:
        for instance_name in instance_names(app_name, root_paths, envs):
            app_key = instance_app_key(app_name, instance_name)
            if app_key in applications:
                raise ValuesValidationException(
                    f"Instance `{instance_name}` of application `{app_name}` is deployed as application "
                    f"`{app_key}`, which already exists. Rename the instance or the application.")


def resolve_instance_includes(include, app_name, instance_keys):
    """Resolve `--include` over the instances of one application.

    An instance is deployed together with the application it belongs to: including an
    application includes its instances, and including an instance alone pulls in the parent it
    inherits its configuration and image from. Single instances are left out with `--exclude`.
    """
    resolved = set(include)
    if app_name in resolved or resolved & set(instance_keys):
        resolved.add(app_name)
        resolved.update(instance_keys)
    return resolved


def task_image_collision(app_key, task_images):
    """The task image an instance application key would take ownership of, if any.

    Task images are resolved to the application that builds them by longest name prefix
    (`resolve_task_image_owner`), so an instance is in the way of the image named after it and
    of every image whose name it prefixes: `samples-print` would own `samples-print-file`.
    """
    for task_image in sorted(task_images):
        if task_image == app_key or task_image.startswith(f"{app_key}-"):
            return task_image
    return None


def load_instance_values(instance_path, envs=()):
    """The override values declared in one instance directory: `values.yaml`, overridden by
    `values-[env].yaml`."""
    values = {}
    for values_path in instance_values_files(instance_path, envs):
        with values_path.open() as f:
            values = dict_merge(values, yaml.load(f) or {})
    return values


def collect_instances(app_name, root_paths, envs=()):
    """Collect the override values of the instances an application declares in any root path.

    An instance is a directory under the application's `deploy/instances`, holding a
    `values.yaml` (or a `values-[env].yaml`, to deploy it in that environment only) with the
    values overriding the application's, plus the `resources` and `templates` overriding the
    application's own. The same instance declared in several root paths is merged, a later root
    overriding an earlier one.

    Returns a mapping of instance name -> override values, empty when the application declares
    no instance.
    """
    instances = {}
    # Task images are named `[application]-[task directory]`, the same way an instance
    # application is: an instance whose key prefixes one would take ownership of it.
    task_images = set()

    for root_path in root_paths:
        app_path = Path(root_path) / APPS_PATH / app_name
        task_images.update(app_name_from_path(f"{app_name}/{task_path.name}")
                           for task_path in (app_path / 'tasks').glob("*/") if task_path.is_dir())

        for instance_name, instance_path in instance_directories(app_path, envs).items():
            instances[instance_name] = dict_merge(
                instances.get(instance_name, {}), load_instance_values(instance_path, envs))

    for instance_name in instances:
        collision = task_image_collision(instance_app_key(app_name, instance_name), task_images)
        if collision:
            raise ValuesValidationException(
                f"Instance `{instance_name}` of application `{app_name}` is deployed as application "
                f"`{instance_app_key(app_name, instance_name)}`, which takes over the task image "
                f"`{collision}`. Rename the instance.")

    return instances
