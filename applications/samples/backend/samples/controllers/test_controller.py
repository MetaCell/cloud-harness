from cloudharness.models import User

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

    import os

    import time
    return time.time()


def serialization():
    return User(last_name="Last", first_name="First")
