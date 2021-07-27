import abc
import os

from jinja2 import Environment, PackageLoader, select_autoescape

jinja_env = Environment(
    loader=PackageLoader('notifications', 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


class NotificationBaseAdapter(metaclass=abc.ABCMeta):
    def __init__(self, notification, channel, backend):
        """
        Init a notification to send notifications for the channel using the backend
        The template, template folder and other attributes are configured in the values.yaml in the `notification:` section
        example:
            notification:
                channels:
                    admins:
                        adapter: email
                        backends:
                            - email
                        templateFolder: html
                        from: info@example.com
                        to:
                            - info@example.com
                    log:
                        adapter: email
                        backends: 
                            - console
                        templateFolder: text
                        from: info@example.com
                        to:
                            - info@example.com
                operations:
                    create:
                        subject: New {{ message_type }} - {{ domain }}
                        template: model-instance-create
                        channels:
                            - admins
                    update:
                        subject: Update {{ message_type }} - {{ domain }}
                        template: model-instance-update
                        channels:
                            - admins
                    delete:
                        subject: Delete {{ message_type }} - {{ domain }}
                        template: model-instance-delete
                        channels:
                            - admins

        Args:
            notification: the notification object from the values.yaml
            channel: the channel of the notification
            backend: the backend to use for sending the notification

        Returns:
            new Notification object
        """
        self.notification = notification
        self.channel = channel
        self.backend = backend
        self.template = jinja_env.get_template(
            os.path.join(
                self.channel["templateFolder"],
                self.notification["template"]
        ))

    @abc.abstractmethod
    def send(self, context):
        """
        Trigger a notification for the notification and channel

        Args:
            context: the context passed to the template of the notification object
        """
        ...

    def render_content(self, context):
        return self.template.render(**context)
