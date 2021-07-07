from cloudharness import log as logger
from cloudharness.utils.config import CloudharnessConfig as conf
from .notification.adapters import NotificationEmailAdapter
from .notification.backends import NotificationEmailBackend, NotificationConsoleBackend

DOMAIN = conf.get_configuration()["domain"]
NOTIFICATION_APP_CONFIG = conf.get_application_by_filter(name='notifications')[0]
CHANNELS = NOTIFICATION_APP_CONFIG["notification"]["channels"]
BACKENDS = NOTIFICATION_APP_CONFIG["notification"]["backends"]


def notify(operation, context):
    notification = NOTIFICATION_APP_CONFIG["notification"]["operations"][operation]

    for c in notification["channels"]:
        channel = CHANNELS[c]
        for b in channel["backends"]:
            if   b == "email":
                channel_backend = NotificationEmailBackend
            elif b == "console":
                channel_backend = NotificationConsoleBackend

            try:
                if channel["type"].lower() == "email":
                    NotificationEmailAdapter(
                        notification=notification,
                        channel=channel,
                        backend=channel_backend).notify(context=context)
                else:
                    raise NotImplementedError
            except Exception as e:
                logger.error('Sending notification error.', exc_info=True)
