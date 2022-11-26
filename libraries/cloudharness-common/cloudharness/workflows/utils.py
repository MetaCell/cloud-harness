import os

from cloudharness import applications
from cloudharness.events.client import EventClient
from cloudharness.utils.env import get_variable

WORKFLOW_NAME_VARIABLE_NAME = "CH_WORKFLOW_NAME"

SHARED_DIRECTORY_VARIABLE_NAME = "shared_directory"


def get_workflow_name():
    """Get the workflow name from inside a workflow"""
    name = get_variable(WORKFLOW_NAME_VARIABLE_NAME)
    remove = name.split("-")[-1]
    return name[0:-len(remove) - 1]


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
