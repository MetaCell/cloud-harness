import os

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
