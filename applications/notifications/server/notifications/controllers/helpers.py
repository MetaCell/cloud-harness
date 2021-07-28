from cloudharness import log as logger
from cloudharness import applications as apps
from cloudharness.utils.config import CloudharnessConfig as conf
from notifications.adapters import NotificationEmailAdapter
from notifications.backends import NotificationEmailBackend, NotificationConsoleBackend


def send(operation, context):
    notification_app = apps.get_configuration('notifications')
    notification = notification_app["notification"]["operations"][operation]

    for c in notification["channels"]:
        channel = notification_app["notification"]["channels"][c]
        for b in channel["backends"]:
            if   b == "email":
                channel_backend = NotificationEmailBackend
            elif b == "console":
                channel_backend = NotificationConsoleBackend

            try:
                if channel["adapter"].lower() == "email":
                    NotificationEmailAdapter(
                        notification=notification,
                        channel=channel,
                        backend=channel_backend).send(context=context)
                else:
                    raise NotImplementedError
            except Exception as e:
                logger.error('Sending notification error.', exc_info=True)
