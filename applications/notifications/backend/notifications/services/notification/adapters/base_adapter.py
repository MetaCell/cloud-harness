import abc
import os

from jinja2 import Environment, PackageLoader, select_autoescape
from cloudharness.utils.config import CloudharnessConfig as config

jinja_env = Environment(
    loader=PackageLoader(config.get_current_app_name(), 'templates'),
    autoescape=select_autoescape(['html', 'xml'])
)


class NotificationBaseAdapter(metaclass=abc.ABCMeta):
    def __init__(self, notification, channel, backend):
        """
        Init a notification

        Args:
            notification: the notification object from the values.yaml
            channel: the channel object from the values.yaml

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
    def notify(self, context):
        """
        Trigger a notification for the notification and channel

        Args:
            context: the context passed to the template of the notification object
        """
        raise NotImplementedError

    def render_content(self, context):
        return self.template.render(**context)
