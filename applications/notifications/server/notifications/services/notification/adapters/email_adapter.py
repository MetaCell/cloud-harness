from cloudharness.utils.config import CloudharnessConfig as conf
from notifications.services.notification.adapters.base_adapter import NotificationBaseAdapter


class NotificationEmailAdapter(NotificationBaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_from = self.channel["from"]
        self.email_to = self.channel["to"]

    def send(self, context):
        subject = self.notification["subject"] \
            .replace("{{domain}}", conf.get_configuration()["domain"]) \
            .replace("{{message_type}}", context.get("message_type"))
        context.update({
            "subject": subject
        })
        message = self.render_content(context)
        self.backend(
            email_from=self.email_from,
            email_to=self.email_to,
            subject=subject,
            message=message).send()
