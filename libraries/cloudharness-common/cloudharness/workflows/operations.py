import time
import pyaml

from collections.abc import Iterable

from cloudharness_cli.workflows.models.operation_status import OperationStatus

from cloudharness.events.client import EventClient
from cloudharness.utils import env, config
from cloudharness import log

from . import argo
from .tasks import Task, SendResultTask, CustomTask

POLLING_WAIT_SECONDS = 1
SERVICE_ACCOUNT = 'argo-workflows'


class BadOperationConfiguration(RuntimeError):
    pass


class PodExecutionContext:
    """
    Key-value pair representing the execution context with other pods.
    Automatically assigns meta data and pod affinity
    """

    def __init__(self, key, value, required=False):
        self.key = str(key)
        self.value = str(value)
        self.required = required


class ManagedOperation:
    """Abstract definition of an operation. Operation is an abstraction of an Argo workflow
    based on a collection of tasks that run according to the operation type and configuration.
    """

    def __init__(self,
        name,
        ttl_strategy: dict = {
            'secondsAfterCompletion': 60 * 60,
            'secondsAfterSuccess': 60 * 20,
            'secondsAfterFailure': 60 * 120
            },
        *args,
        on_exit_notify=None,
        **kwargs):
        self.name = name
        self.ttl_strategy = ttl_strategy
        self.on_exit_notify = on_exit_notify

    def execute(self, **parameters):
        raise NotImplementedError(f"{self.__class__.__name__} is abstract")


class ContainerizedOperation(ManagedOperation):
    """
    Abstract Containarized operation based on an argo workflow
    """

    def __init__(self, basename: str, pod_context: PodExecutionContext = None, shared_directory=None, *args, **kwargs):
        """
        :param basename:
        :param pod_context: PodExecutionContext - represents affinity with other pods in the system
        :param shared_directory: bool|str|list
        """
        super(ContainerizedOperation, self).__init__(basename, *args, **kwargs)
        self.pod_context = pod_context
        self.persisted = None
        shared_path = None
        if shared_directory:
            if shared_directory is True:
                self.volumes = ['/mnt/shared']
                shared_path = '/mnt/shared'
            elif isinstance(shared_directory, str):
                self.volumes = [shared_directory]
                shared_path = shared_directory
            else:
                self.volumes = shared_directory
                assert len(set(shared_directory)) == len(shared_directory), "Shared directories are not unique"
                assert len(set(s.split(":")[0] for s in shared_directory)) == len(shared_directory), "Shared directories volumes are not unique"
                
            if shared_path:
                for task in self.task_list():
                    task.add_env('shared_directory', shared_path)
        else:
            self.volumes = tuple()

    def task_list(self):
        raise NotImplementedError()

    @property
    def entrypoint(self):
        raise NotImplemented

    @property
    def templates(self):
        raise NotImplemented

    def to_workflow(self, **arguments):
        return {
            'apiVersion': 'argoproj.io/v1alpha1',
            'kind': 'Workflow',
            'metadata': {'generateName': self.name},
            'spec': self.spec()
        }

    def spec(self):
        spec = {
            'entrypoint': self.entrypoint,
            'ttlStrategy': self.ttl_strategy,
            'templates': [self.modify_template(template) for template in self.templates],
            'serviceAccountName': SERVICE_ACCOUNT,
            'imagePullSecrets': [{'name': config.CloudharnessConfig.get_registry_secret()}],
            'volumes': [{
                # mount allvalues so we can use the cloudharness Python library
                'name': 'cloudharness-allvalues',
                'configMap': {
                    'name': 'cloudharness-allvalues'
                }
            }]
        }
        if self.on_exit_notify:
            spec = self.add_on_exit_notify_handler(spec)

        if self.pod_context:
            spec['affinity'] = self.affinity_spec()
        if self.volumes:
            spec['volumeClaimTemplates'] = [self.spec_volumeclaim(volume) for volume in self.volumes if
                                            ':' not in volume]  # without PVC prefix (e.g. /location)
            spec['volumes'] += [self.spec_volume(volume) for volume in self.volumes if
                                ':' in volume]  # with PVC prefix (e.g. pvc-001:/location)
        return spec

    def affinity_spec(self):

        term = {
            'labelSelector':
                {
                    'matchExpressions': [
                        {
                            'key': self.pod_context.key,
                            'operator': 'In',
                            'values': [self.pod_context.value]
                        },
                    ]
                },
            'topologyKey': 'kubernetes.io/hostname'
        }
        if not self.pod_context.required:
            return {
                'podAffinity':
                    {
                        'preferredDuringSchedulingIgnoredDuringExecution': [
                            {
                                'weight': 100,
                                'podAffinityTerm': term

                            }]
                    }
            }
        else:
            return {
                'podAffinity':
                    {
                        'requiredDuringSchedulingIgnoredDuringExecution': [term]
                    }
            }

    def add_on_exit_notify_handler(self, spec):
        queue = self.on_exit_notify['queue']
        payload = self.on_exit_notify['payload']
        exit_task = CustomTask(
            name="exit-handler",
            image_name='workflows-notify-queue',
            workflow_result='{{workflow.status}}',
            queue_name=queue,
            payload=payload
        )
        spec['onExit'] = 'exit-handler'
        spec['templates'].append(
            self.modify_template(exit_task.spec())
        )
        return spec

    def modify_template(self, template):
        """Hook to modify templates (e.g. add volumes)"""
        if self.pod_context:
            if 'metadata' not in template:
                template['metadata'] = {}
            if 'labels' not in template['metadata']:
                template['metadata']['labels'] = {}
            template['metadata']['labels'][self.pod_context.key] = self.pod_context.value
        if self.volumes:
            if 'container' in template:
                template['container']['volumeMounts'] += [self.volume_template(volume) for volume in self.volumes]
            elif 'script' in template:
                template['script']['volumeMounts'] += [self.volume_template(volume) for volume in self.volumes]
        
        return template

    def submit(self):
        """Created and submits the Argo workflow"""
        op = self.to_workflow()

        log.debug("Submitting workflow\n" + pyaml.dump(op))

        # TODO use rest api for that? Include this into cloudharness.workflows?
        self.persisted = argo.submit_workflow(op)
        return self.persisted

    def is_running(self):
        if self.persisted:
            self.refresh()
            return self.persisted.status in (OperationStatus.RUNNING, OperationStatus.PENDING)
        return False

    def refresh(self):
        self.persisted = argo.get_workflow(self.persisted.name)

    def is_error(self):
        if self.persisted:
            self.refresh()
            return self.persisted.status in (OperationStatus.ERROR, OperationStatus.FAILED)
        return False

    def name_from_path(self, path):
        return path.replace('/', '').replace('_', '').lower()

    def volume_template(self, volume):
        path = volume
        splitted = volume.split(':')[1]
        if len(splitted) > 1:
            path = splitted[1]
        return dict({
            'name': self.name_from_path(path), 
            'mountPath': path,
            'readonly': False if len(splitted) < 3 else splitted[2] == "ro"
            })
        
    def spec_volumeclaim(self, volume):
        # when the volume is NOT prefixed by a PVC (e.g. /location) then create a temporary PVC for the workflow
        if ':' not in volume:
            return {
                'metadata': {
                    'name': self.name_from_path(volume.split(':')[0]),
                },
                'spec': {
                    'accessModes': ["ReadWriteOnce"],
                    'resources': {
                        'requests':
                            {
                                'storage': f'{self.shared_volume_size}Mi'
                            }
                    }
                }
            }
        return {}

    def spec_volume(self, volume):
        # when the volume is prefixed by a PVC (e.g. pvc-001:/location) then add the PVC to the volumes of the workflow
        if ':' in volume:
            pvc, path = volume.split(':')
            return {
                'name': self.name_from_path(path),
                'persistentVolumeClaim': {
                    'claimName': pvc
                },
                
            }
        return {}

class SyncOperation(ManagedOperation):
    """A Sync operation returns the result directly with the execute method"""


class DirectOperation(SyncOperation):
    """A DirectOperation is running directly inside the service container. Whether an operation is direct or distributed
     is a design choice of the single service/application. The common scenario depicted here is operations that are
      querying a database rather than making calculations. Also, there is no need of a real api to define a direct
      operation, is just code running from the REST controller"""

    def __init__(self, name, callback):
        super().__init__(name)
        self.callback = callback

    def execute(self, *args, **kwargs):
        self.callback(*args, **kwargs)


class ResourceQueryOperation(DirectOperation):
    """Queries for a resource"""


class DataQueryOperation(DirectOperation):
    """Queries the Graph database"""
    pass


class SingleTaskOperation(ContainerizedOperation):
    def __init__(self, name, task: Task, *args, **kwargs):
        """
        Using a single task is a simplification we may want to
        :param task:
        """
        self.task = task
        super().__init__(name, *args, **kwargs)
        

    def task_list(self):
        return (self.task, )

    @property
    def entrypoint(self):
        return self.task.name

    @property
    def templates(self):
        return [self.task.spec()]


class ExecuteAndWaitOperation(ContainerizedOperation, SyncOperation):

    def execute(self, timeout=None):
        self.persisted = self.submit()
        start_time = time.time()
        while not self.persisted.is_finished():
            time.sleep(POLLING_WAIT_SECONDS)
            log.debug(f"Polling argo workflow {self.persisted.name}")
            self.persisted = argo.get_workflow(self.persisted.name)
            log.debug(f"Polling succeeded for {self.persisted.name}. Current phase: {self.persisted.status}")
            if timeout and time.time() - start_time > timeout:
                log.error("Timeout exceeded while polling for results")
                return self.persisted
        return self.persisted


class DistributedSyncOperation(ExecuteAndWaitOperation, SingleTaskOperation):
    """Sync operation that runs on a separate container"""


class DataFrameOperation(DistributedSyncOperation):
    """Uses Spark dataframe abstraction to implement parallel big data query and processing"""
    pass


class AsyncOperation(ContainerizedOperation):
    """The operation is made asynchronously in an Argo workflow.
    The workflow can be monitored during the execution"""

    def execute(self):
        op = self.submit()
        return op

    def get_operation_update_url(self):
        return f"{env.get_cloudharness_workflows_service_url()}/operations/{self.persisted.name}"


class CompositeOperation(AsyncOperation):
    """Operation with multiple tasks"""

    def __init__(self, basename, tasks, shared_directory="", shared_volume_size=10,
                 pod_context: PodExecutionContext = None,
                 *args, **kwargs):
        """

        :param basename:
        :param tasks:
        :param shared_directory: can set to True or a path. If set, tasks will use that directory to store results. It
        will also be available from the container as environment variable `shared_directory`
        :param shared_volume_size: size of the shared volume in MB (if shared_directory is not set, it is ignored)
        :param pod_context: PodExecutionContext - represents affinity with other pods in the system
        """
        self.tasks = tasks
        AsyncOperation.__init__(self, basename, pod_context, shared_directory=shared_directory, *args, **kwargs)
        


        self.shared_volume_size = shared_volume_size
        if len(self.task_list()) != len(set(self.task_list())):
            raise BadOperationConfiguration('Tasks in the same operation must have different names')
        self.entrypoint_template = {'name': self.entrypoint, 'steps': self.steps_spec()}

    def steps_spec(self):
        raise NotImplemented

    def task_list(self):
        return self.tasks

    @property
    def templates(self):
        return [self.entrypoint_template] + [task.spec() for task in self.task_list()]

    def spec(self):
        spec = super().spec()

        return spec

    def modify_template(self, template):
        # TODO verify the following condition. Can we mount volumes also with source based templates
        super().modify_template(template)
      
        return template






class PipelineOperation(CompositeOperation):

    def steps_spec(self):
        return [[task.instance()] for task in self.tasks]

    @property
    def entrypoint(self):
        return self.name + '-pipeline'


class DistributedSyncOperationWithResults(PipelineOperation, ExecuteAndWaitOperation, SyncOperation):
    """Synchronously returns the result from the workflow. Uses a shared volume and a queue"""

    def __init__(self, name, task: Task, *args, **kwargs):
        PipelineOperation.__init__(self, name, [task, SendResultTask()], shared_directory="/mnt/shared", *args,
                                   **kwargs)
        self.client = None

    def submit(self):
        op = super().submit()
        topic_name = op.name
        self.client = EventClient(topic_name)
        self.client.create_topic()
        return op

    def execute(self, timeout=None):
        op = ExecuteAndWaitOperation.execute(self, timeout)

        result = self.client.consume_all()
        if result is None:
            raise RuntimeError(
                "Operation `" + op.name + "` did not put results in the queue. Check your workflow configuration")
        self.client.delete_topic()
        return result


class ParallelOperation(CompositeOperation):

    def steps_spec(self):
        return [[task.instance() for task in self.tasks]]

    @property
    def entrypoint(self):
        return self.name + '-parallel'


class SimpleDagOperation(CompositeOperation):
    """Simple DAG definition limited to a pipeline of parallel operations"""

    def __init__(self, basename, *task_groups, shared_directory=None, pod_context: PodExecutionContext = None, **kwargs):
        task_groups = tuple(
            task_group if isinstance(task_group, Iterable) else (task_group,) for task_group in task_groups)
        super().__init__(basename, pod_context=pod_context, tasks=task_groups, shared_directory=shared_directory, **kwargs)

    def steps_spec(self):
        return [[task.instance() for task in task_group] for task_group in self.tasks]

    @property
    def entrypoint(self):
        return self.name + '-simpledag'

    def task_list(self):
        return [task for task_group in self.tasks for task in task_group]


__all__ = [c for c in dir() if c.endswith('Operation')]
