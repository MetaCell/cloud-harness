import json
from cloudharness_model.encoder import CloudHarnessJSONEncoder
import logging
import sys

log = logging

FORMAT = "%(asctime)s [%(levelname)s] %(module)s.%(funcName)s: %(message)s"
logging.basicConfig(stream=sys.stdout, format=FORMAT, level=logging.INFO)


def set_debug():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


# TODO log will write through a rest service


json_dumps = json.dumps


def dumps(o, *args, **kwargs):
    try:
        if "cls" not in kwargs:
            return json_dumps(o, cls=CloudHarnessJSONEncoder, *args, **kwargs)
        return json_dumps(o, *args, **kwargs)
    except TypeError as e:
        # If serialization fails, try converting objects with to_dict method
        if "not JSON serializable" in str(e):
            if hasattr(o, "to_dict") and callable(getattr(o, "to_dict")):
                o = o.to_dict()
                return json_dumps(o, *args, **kwargs)
            # Handle lists/tuples of objects with to_dict
            if isinstance(o, (list, tuple)):
                converted = [item.to_dict() if hasattr(item, "to_dict") and callable(getattr(item, "to_dict")) else item for item in o]
                return json_dumps(converted, *args, **kwargs)
        # If we still can't serialize, try without cls parameter
        if "cls" in kwargs:
            kwargs_no_cls = {k: v for k, v in kwargs.items() if k != "cls"}
            return json_dumps(o, *args, **kwargs_no_cls)
        raise


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
