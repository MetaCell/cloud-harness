from cloudharness import log
from notifications.backends.base_backend import NotificationBaseBackend


class NotificationConsoleBackend(NotificationBaseBackend):
    """
    Console notification backend

    This backend outputs all adapter (keyword) arguments.
    E.g. the rendered message, subject etc
    The backend can be usefull for debugging the notification adapters.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def send(self):
        log.info("Send notification")
        log.info(f"args:{self.args}")
        log.info("kwargs:\n"+"\n".join("{0}: {1!r}".format(k,v) for k,v in self.kwargs.items()))
