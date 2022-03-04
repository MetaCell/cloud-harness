import logging
import sys

from cloudharness_model.models.base_model_ import Model

log = logging

from cloudharness_model.encoder import CloudHarnessJSONEncoder
FORMAT = "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(stream=sys.stdout, format=FORMAT, level=logging.INFO)

def set_debug():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


# TODO log will write through a rest service

import json as js

json_dumps = js.dumps

def dumps(o, *args, **kwargs):
    if isinstance(o, Model):
       return json_dumps(o.to_dict(), *args, **kwargs)
    return json_dumps(o, *args, **kwargs)

json = js
json.dumps = dumps

class NotCorrectlyInitialized(Exception):
    pass

def init(appname: str):
    """
    Init cloudharness functionality for the current app

    Args:
        appname: the slug of the application

    Usage examples: 
        import cloudharness
        cloudharness.init('notifications')
    """
    if not appname:
        raise NotCorrectlyInitialized
    try:
        from cloudharness import sentry
        sentry.init(appname)
    except Exception as e:
        log.warning(f'Error enabling Sentry for {appname}', exc_info=True)

__all__ = ['log', 'init']

