import time
import json
from types import SimpleNamespace as Namespace

from cloudharness import log
from cloudharness.events.client import EventClient
from cloudharness import applications
from cloudharness.models import CDCEvent, CDCEventMeta

from notifications.controllers.helpers import send


class NotificationHandler:
    def __init__(self, event_type, app_name, message_type, events):
        self.message_type = message_type
        self.events = events
        self.topic_id = f"{app_name}.{event_type}.{message_type}"

    def handle_event(self, message: CDCEvent):
        """
        Send a notification for the received event

        Args:
            message: the message
        """
        if self.message_type == message.message_type:
            operation = message.get("operation")
            for event in self.events:
                if event == operation:
                    meta: CDCEventMeta = message.meta
                    app_name = meta.app_name
                    description = meta.description
                    obj = json.loads(json.dumps(message.get("resource")), object_hook=lambda d: Namespace(**d))
                    log.info(f"{app_name} sent {operation} {self.message_type} {description} message")
                    send(
                        operation=operation,
                        context={
                            "app_name": app_name,
                            "message_type": self.message_type,
                            "user": meta.get("user", {}),
                            "description": description,
                            "obj": obj
                        }
                    )

class NotificationsController:
    _notification_handlers = []

    def __init__(self):
        # self._topics = []
        self._event_clients = []

    @staticmethod
    def handler(app, event_client, message):
        log.debug("Handler received message: %s",message)
        for nh in [nh for nh in NotificationsController._notification_handlers if nh.message_type == message.get("message_type")]:
            nh.handle_event(CDCEvent.from_dict(message))

    def _init_handlers(self):
        app = applications.get_current_configuration()
        for event_type in app.harness["events"]:
            for notification_app in app.harness["events"][event_type]:
                for notification_type in notification_app["types"]:
                    log.info(f"Init handler for event {notification_app['app']}.{notification_type['name']} type {event_type}")
                    nss = NotificationHandler(
                        event_type,
                        notification_app["app"], 
                        notification_type["name"], 
                        notification_type["events"])
                    if not nss.topic_id in (handler.topic_id for handler in NotificationsController._notification_handlers):
                        self._consume_topic(nss.topic_id)
                    NotificationsController._notification_handlers.append(nss)

    def _consume_topic(self, topic_id):
        log.info(f"Init topic: {topic_id}")
        event_client = EventClient(topic_id)
        event_client.async_consume(app=None, handler=self.handler, group_id="ch-notifications")
        self._event_clients.append(event_client)

    def start_handlers(self):
        """
        Start consuming incomming messages
        """
        self._init_handlers()
        # use a sleep loop to not frustrate the cpu
        nap_time = 30
        try:
            while True:
                time.sleep(nap_time)  # sleep xx seconds
                log.debug("Running...")
        except Exception as e:
            log.error('Notification Controller threw an error, stopping handlers.', exc_info=True)
        finally:
            self.stop_handlers()

    def stop_handlers(self):
        log.info("Stopping the notification handlers")
        for event_client in self._event_clients:
            log.info(f"Closing topic {event_client.topic_id}")
            event_client.close()
