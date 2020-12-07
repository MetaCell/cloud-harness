import connexion
import six

from api_samples.models.inline_response202 import InlineResponse202  # noqa: E501
from api_samples import util
from api_samples.models import InlineResponse202
from api_samples.models.inline_response202_task import InlineResponse202Task
from flask.json import jsonify

from cloudharness import log

try:
    from cloudharness.workflows import operations, tasks
except Exception as e:
    log.error("Cannot start workflows module. Probably this is related some problem with the kubectl configuration", e)


def submit_async():  # noqa: E501
    """Send an asyncronous operation

     # noqa: E501


    :rtype: InlineResponse202
    """
    shared_directory = '/mnt/shared'
    task_write = tasks.CustomTask('download-file', 'workflows-extract-download', url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')
    task_print = tasks.CustomTask('print-file', 'workflows-print-file', file_path=shared_directory + '/README.md')
    op = operations.PipelineOperation('test-custom-connected-op-', (task_write, task_print), shared_directory=shared_directory)

    submitted = op.execute()
    if not op.is_error():
        return InlineResponse202(task= InlineResponse202Task(href=op.get_operation_update_url(), name=submitted.name)), 202
    else:
        return 'Error submitting operation', 500


def submit_sync():  # noqa: E501
    """Send a syncronous operation

     # noqa: E501


    :rtype: str
    """
    task = tasks.CustomTask('download-file', 'workflows-extract-download', url='https://www.metacell.us')

    op = operations.DistributedSyncOperation('test-sync-op-', task)
    workflow = op.execute()
    return workflow.raw


def submit_sync_with_results(a=1, b=2):  # noqa: E501
    """Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud

     # noqa: E501

    :param a: first number to sum
    :type a: float
    :param b: second number to sum
    :type b: float

    :rtype: str
    """
    task = tasks.CustomTask('test-sum', 'samples-sum', a=a, b=b)
    try:
        op = operations.DistributedSyncOperationWithResults('test-sync-op-results-', task)
        result = op.execute()
        return result
    except Exception as e:
        return jsonify(str(e)), 200



def error():  # noqa: E501
    """test sentry is working

     # noqa: E501


    :rtype: str
    """
    return "a"[2]
