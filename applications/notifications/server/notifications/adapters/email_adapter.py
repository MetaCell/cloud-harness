from cloudharness.utils.config import CloudharnessConfig as conf
from jinja2 import Template
from notifications.adapters.base_adapter import NotificationBaseAdapter


class NotificationEmailAdapter(NotificationBaseAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.email_from = self.channel["from"]
        self.email_to = self.channel["to"]

    def send(self, context):
        subject = Template(self.notification["subject"]).render(
            domain=conf.get_configuration()["domain"],
            message_type=context.get("message_type")
        )
        context.update({
            "subject": subject
        })
        message = self.render_content(context)
        self.backend(
            email_from=self.email_from,
            email_to=self.email_to,
            subject=subject,
            message=message).send()
