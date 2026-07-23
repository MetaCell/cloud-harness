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


def write_file(body=None):  # noqa: E501
    """writes a file on the application volume

     # noqa: E501

    :param body: Optional content of the file to write.
    :type body: dict | bytes

    :rtype: dict
    """
    import os
    import socket
    import time

    from flask import has_request_context, request

    if body is None and has_request_context() and request.is_json:
        body = request.get_json()

    try:
        from cloudharness.applications import get_current_configuration
        mountpath = get_current_configuration().harness.deployment.volume.mountpath
    except Exception:
        # not running inside a cloudharness deployment (e.g. unit tests)
        mountpath = "/tmp/myvolume"

    hostname = socket.gethostname()
    filename = f"{time.strftime('%Y%m%d-%H%M%S')}-{hostname}.txt"
    path = os.path.join(mountpath, filename)
    content = (body or {}).get("content") or f"written by {hostname}"

    os.makedirs(mountpath, exist_ok=True)
    with open(path, "w") as f:
        f.write(content)

    return {"filename": filename, "path": path, "hostname": hostname}


def serialization():
    return User(last_name="Last", first_name="First")
