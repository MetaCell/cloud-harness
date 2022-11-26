from . import argo

from cloudharness.utils.env import get_cloudharness_variables, get_image_full_tag
from .utils import WORKFLOW_NAME_VARIABLE_NAME, is_accounts_present, volume_mount_template

SERVICE_ACCOUNT = 'argo-workflows'


class Task(argo.ArgoObject):
    """
    Abstract interface for a task.
    """

    def __init__(self, name, resources={}, volume_mounts=[],  **env_args):
        self.name = name.replace(' ', '-').lower()
        self.resources = resources
        self.__envs = get_cloudharness_variables()
        self.volume_mounts = volume_mounts
        for k in env_args:
            self.__envs[k] = str(env_args[k])

    @property
    def image_name(self):
        raise NotImplemented

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def instance(self):
        # We are not considering arguments, we are always having a single template for each step
        return {
            'name': self.name,
            'template': self.name
        }

    @property
    def envs(self):
        envs = [dict(name=key, value=value)
                for key, value in self.__envs.items()]
        # Add the name of the workflow to task env
        envs.append({'name': WORKFLOW_NAME_VARIABLE_NAME, 'valueFrom': {
            'fieldRef': {'fieldPath': 'metadata.name'}}})
        return envs

    def add_env(self, name, value):
        self.__envs[name] = value

    def cloudharness_configmap_spec(self):
        base_spec = [
            {
                'name': 'cloudharness-allvalues',
                'mountPath': '/opt/cloudharness/resources/allvalues.yaml',
                'subPath': 'allvalues.yaml'
            }
        ]
        if is_accounts_present():
            base_spec.append({
                'name': 'cloudharness-kc-accounts',
                'mountPath': '/opt/cloudharness/resources/auth',
            })
        return base_spec

    def volumes_mounts_spec(self):
        return self.cloudharness_configmap_spec() + [volume_mount_template(volume) for volume in self.volume_mounts]


class ContainerizedTask(Task):

    def __init__(self, name, resources={}, image_pull_policy='IfNotPresent', command=None, **env_args):
        super().__init__(name, resources, **env_args)
        self.image_pull_policy = image_pull_policy
        self.command = command
        

    def spec(self):
        spec = {
            'container': {
                'image': self.image_name,
                'env': self.envs,
                'resources': self.resources,
                'imagePullPolicy': self.image_pull_policy,
                'volumeMounts': self.volumes_mounts_spec(),
            },
            'inputs': {},
            'metadata': {},
            'name': self.name,
            'outputs': {}

        }
        if self.command is not None:
            spec['container']['command'] = self.command
        return spec


class InlinedTask(Task):
    """
    Allows to run Python tasks
    """

    def __init__(self, name, source, **kwargs):
        super().__init__(name, **kwargs)
        self.source = source

    def spec(self):
        return {
            'name': self.name,
            'script':
                {
                    'image': self.image_name,
                    'env': self.envs,
                    'source': self.source,
                    'volumeMounts': self.volumes_mounts_spec(),
                    'command': [self.command]
                }
        }

    @property
    def command(self):
        raise NotImplemented


class PythonTask(InlinedTask):
    def __init__(self, name, func):
        import inspect
        super().__init__(name, (inspect.getsource(
            func) + f"\n{func.__name__}()").strip())

    @property
    def image_name(self):
        return get_image_full_tag('cloudharness-base')

    @property
    def command(self):
        return 'python'


class BashTask(InlinedTask):

    @property
    def image_name(self):
        return get_image_full_tag('cloudharness-base')

    @property
    def command(self):
        return 'bash'


class CustomTask(ContainerizedTask):
    def __init__(self, name, image_name, resources={}, image_pull_policy='IfNotPresent', command=None, **env_args):
        super().__init__(name, resources=resources,
                         image_pull_policy=image_pull_policy, command=command, **env_args)
        self.__image_name = get_image_full_tag(image_name)

    @property
    def image_name(self):
        return self.__image_name


class CommandBasedTask(ContainerizedTask):
    """
    Shortcut task to run a command in a cloudharness-base image
    """

    def __init__(self, name, command, resources={}, image_pull_policy='IfNotPresent', **env_args):
        super().__init__(name, resources=resources,
                         image_pull_policy=image_pull_policy, command=command, **env_args)

    @property
    def image_name(self):
        return get_image_full_tag('cloudharness-base')


class SendResultTask(CustomTask):
    """Special task used to send a workflow result to a queue.
    The workflow result consists of all the files inside the shared directory"""

    def __init__(self):
        super().__init__('send-result-event', 'workflows-send-result-event')
