import json as js
from cloudharness_model.encoder import CloudHarnessJSONEncoder
import logging
import sys

log = logging

FORMAT = "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(stream=sys.stdout, format=FORMAT, level=logging.INFO)


def set_debug():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


# TODO log will write through a rest service


json_dumps = js.dumps


def dumps(o, *args, **kwargs):
    try:
        if "cls" not in kwargs:
            return json_dumps(o, cls=CloudHarnessJSONEncoder, *args, **kwargs)
        return json_dumps(o, *args, **kwargs)
    except:
        logging.error(repr(o))
        raise


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
        from cloudharness import sentry, applications
        if applications.get_current_configuration().is_sentry_enabled():
            sentry.init(appname)
    except Exception as e:
        log.warning(f'Error enabling Sentry for {appname}', exc_info=True)


__all__ = ['log', 'init']
