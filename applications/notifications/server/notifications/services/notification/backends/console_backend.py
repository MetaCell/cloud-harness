from cloudharness import log as logger
from notifications.services.notification.backends.base_backend import NotificationBaseBackend


class NotificationConsoleBackend(NotificationBaseBackend):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def send(self):
        logger.info("Send notification")
        logger.info(f"args:{self.args}")
        logger.info("kwargs:\n"+"\n".join("{0}: {1!r}".format(k,v) for k,v in self.kwargs.items()))
