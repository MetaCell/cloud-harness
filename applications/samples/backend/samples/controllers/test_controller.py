import connexion
import six

from samples import util


def error():  # noqa: E501
    """test sentry is working

     # noqa: E501


    :rtype: str
    """
    raise Exception("The error we supposed to find here")


def ping():  # noqa: E501
    """test the application is up

     # noqa: E501


    :rtype: str
    """
    import time
    return time.time()
