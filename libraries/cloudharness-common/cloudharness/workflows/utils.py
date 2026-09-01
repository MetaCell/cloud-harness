import os

from cloudharness import applications
from cloudharness.events.client import EventClient
from cloudharness.utils.config import CloudharnessConfig
from cloudharness.utils.env import get_variable

WORKFLOW_NAME_VARIABLE_NAME = "CH_WORKFLOW_NAME"

SHARED_DIRECTORY_VARIABLE_NAME = "shared_directory"


class PodExecutionContext:
    """
    Key-value pair representing the execution context with other pods.
    Automatically assigns meta data and pod affinity
    """

    def __init__(self, key, value, required=False):
        self.key = str(key)
        self.value = str(value)
        self.required = required


def get_workflow_name():
    """Get the workflow name from inside a workflow"""
    name = get_variable(WORKFLOW_NAME_VARIABLE_NAME)
    remove = name.split("-")[-1]
    return name[0:-len(remove) - 1]


def deployment_volumes():
    """Yields the volume specs of all the application (and sub-application) deployments"""
    def walk(configurations: dict):
        for name, configuration in configurations.items():
            if name == 'harness' or not isinstance(configuration, dict):
                continue
            harness = configuration.get('harness')
            if isinstance(harness, dict):
                volume = (harness.get('deployment') or {}).get('volume')
                if volume:
                    yield volume
            yield from walk(configuration)

    yield from walk(CloudharnessConfig.get_configuration().get('apps') or {})


def volume_is_write_many(claim_name):
    """Tells whether the claim belongs to an application volume declared ReadWriteMany
    (`harness.deployment.volume.writeMany`, or the legacy `usenfs` flag)"""
    for volume in deployment_volumes():
        if volume.get('name') == claim_name:
            return bool(volume.get('usenfs') or volume.get('writeMany'))
    return False


def volume_requires_affinity(v):
    """Tells whether a volume mount (`claim:path[:mode]`) requires pod affinity.

    Pods sharing a ReadWriteOnce volume must all run on the volume's node. ReadWriteMany
    volumes attach to several nodes at once, hence require no affinity: they are recognized
    either from the application declaring the volume, or from the explicit `rwx` mount mode.
    A mount without a claim prefix is provisioned for the workflow itself and is not matched
    by the `usesvolume` affinity.
    """
    if ':' not in v or 'rwx' in v[-4:]:
        return False
    return not volume_is_write_many(v.split(':')[0])


def get_shared_directory():
    return os.getenv(SHARED_DIRECTORY_VARIABLE_NAME)


def notify_queue(queue, message):
    client = EventClient(queue)
    client.produce(message)


def is_accounts_present():
    try:
        applications.ApplicationConfiguration = applications.get_configuration(
            'accounts')
        return True
    except Exception:
        return False


def name_from_path(path):
    return path.replace('/', '').replace('_', '').lower()


def volume_mount_template(volume):
    path = volume
    splitted = volume.split(':')
    if len(splitted) > 1:
        path = splitted[1]
    return dict({
        'name': name_from_path(path),
        'mountPath': path,
        'readonly': False if len(splitted) < 3 else splitted[2] == "ro"
    })


def affinity_spec(contexts: PodExecutionContext):
    PREFERRED = 'preferredDuringSchedulingIgnoredDuringExecution'
    REQUIRED = 'requiredDuringSchedulingIgnoredDuringExecution'

    pod_affinity = {
        PREFERRED: [],
        REQUIRED: []
    }

    for context in contexts:
        term = {
            'labelSelector':
                {
                    'matchExpressions': [
                        {
                            'key': context.key,
                            'operator': 'In',
                            'values': [context.value]
                        },
                    ]
                },
            'topologyKey': 'kubernetes.io/hostname'
        }
        if not context.required:
            pod_affinity[PREFERRED].append(
                {
                    'weight': 100,
                    'podAffinityTerm': term

                })
        else:
            pod_affinity[REQUIRED].append(term)

    return {
        'podAffinity': pod_affinity
    }
