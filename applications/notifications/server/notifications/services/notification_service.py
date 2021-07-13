from cloudharness import log as logger
from cloudharness.utils.config import CloudharnessConfig as conf
from notifications.services.notification.adapters import NotificationEmailAdapter
from notifications.services.notification.backends import NotificationEmailBackend, NotificationConsoleBackend


def send(operation, context):
    notification_app = conf.get_application_by_filter(name='notifications')[0]
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
