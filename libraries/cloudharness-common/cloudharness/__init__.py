import logging
import sys

log = logging

# logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def set_debug():
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


# TODO log will write through a rest service


class NotCorrectlyInitialized(Exception):
    pass

def init(appname: str):
    """
    Init cloudharness functionality for the current app

    Args:
        appname: the slug of the application

    Usage examples: 
        import cloudharness
        cloudharness.init('workspaces')
    """
    if not appname:
        raise NotCorrectlyInitialized
    import cloudharness.sentry
    sentry.init(appname)

__all__ = ['log', 'init']
