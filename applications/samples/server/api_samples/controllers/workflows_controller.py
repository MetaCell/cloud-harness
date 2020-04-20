import connexion
import six

from api_samples.models.inline_response202 import InlineResponse202  # noqa: E501
from api_samples import util


def submit_async():  # noqa: E501
    """Send an asynchronous operation

     # noqa: E501


    :rtype: InlineResponse202
    """
    return 'do some magic!'


def submit_sync():  # noqa: E501
    """Send a synchronous operation

     # noqa: E501


    :rtype: str
    """
    return 'do some magic!'


def submit_sync_with_results(a=None, b=None):  # noqa: E501
    """Send a synchronous operation and get results using the event queue. Just a sum, but in the cloud

     # noqa: E501

    :param a: first number to sum
    :type a: 
    :param b: second number to sum
    :type b: 

    :rtype: str
    """
    return 'do some magic!'
