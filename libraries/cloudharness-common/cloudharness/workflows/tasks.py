from . import argo
import time

SERVICE_ACCOUNT = 'argo-workflows'

from cloudharness import log
from cloudharness.utils.env import get_cloudharness_variables, get_image_full_tag

from .utils import WORKFLOW_NAME_VARIABLE_NAME

class Task(argo.ArgoObject):
    """
    Abstract interface for a task.
    """

    def __init__(self, name):
        self.name = name.replace(' ', '-').lower()

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


class ContainerizedTask(Task):

    def __init__(self, name, resources={}, image_pull_policy='IfNotPresent', **env_args):
        super().__init__(name)

        self.__envs = get_cloudharness_variables()
        self.resources = resources
        self.image_pull_policy = image_pull_policy

        for k in env_args:
            self.__envs[k] = str(env_args[k])

    @property
    def envs(self):
        envs = [dict(name=key, value=value) for key, value in self.__envs.items()]
        # Add the name of the workflow to task env
        envs.append({'name': WORKFLOW_NAME_VARIABLE_NAME, 'valueFrom': {'fieldRef': {'fieldPath': 'metadata.name'}}})
        return envs

    def add_env(self, name, value):
        self.__envs[name] = value

    def spec(self):
        spec = {
            'container': {
                'image': self.image_name,
                'env': self.envs,
                'resources': self.resources,
                'imagePullPolicy': self.image_pull_policy,
                'volumeMounts': [{
                        'name': 'cloudharness-allvalues',
                        'mountPath': '/opt/cloudharness/resources/allvalues.yaml',
                        'subPath': 'allvalues.yaml'
                    }],
            },
            'inputs': {},
            'metadata': {},
            'name': self.name,
            'outputs': {}

        }
        return spec


class InlinedTask(Task):
    """
    Allows to run Python tasks
    """

    def __init__(self, name, source):
        super().__init__(name)
        self.source = source

    def spec(self):
        return {
            'name': self.name,
            'script':
                {
                    'image': self.image_name,
                    'source': self.source,
                    'command': [self.command]
                }
        }

    @property
    def command(self):
        raise NotImplemented


class PythonTask(InlinedTask):
    def __init__(self, name, func):
        import inspect
        super().__init__(name, (inspect.getsource(func) + f"\n{func.__name__}()").strip())

    @property
    def image_name(self):
        return 'python:3'

    @property
    def command(self):
        return 'python'


class CustomTask(ContainerizedTask):
    def __init__(self, name, image_name, resources={}, image_pull_policy='IfNotPresent', **env_args):
        super().__init__(name, resources, image_pull_policy, **env_args)
        self.__image_name = get_image_full_tag(image_name)

    @property
    def image_name(self):
        return self.__image_name


class SendResultTask(CustomTask):
    """Special task used to send the a workflow result to a queue.
    The workflow result consists of all the files inside the shared directory"""

    def __init__(self):
        super().__init__('send-result-event', 'workflows-send-result-event')
