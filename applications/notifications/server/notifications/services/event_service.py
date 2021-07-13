import json

from cloudharness import log
from cloudharness.events.client import EventClient
from cloudharness.utils.config import CloudharnessConfig as conf
from types import SimpleNamespace as Namespace

from notifications.services.notification_service import send


class NotificationHandler:
    def __init__(self, event_type, app_name, message_type, events):
        self.message_type = message_type
        self.events = events
        self.topic_id = f"{app_name}.{event_type}.{message_type}"

    def handle_event(self, message):
        """
        Handle the received event

        Args:
            message: the message
        """
        if self.message_type == message.get("message_type"):
            operation = message.get("operation")
            for event in self.events:
                if event == operation:
                    meta = message.get("meta", {})
                    app_name = meta.get("app_name", "")
                    obj_id = message.get("uid")
                    obj = json.loads(json.dumps(message.get("resource")), object_hook=lambda d: Namespace(**d))
                    log.info(f"{app_name} sent {operation} {self.message_type} with id: {obj_id} message")
                    send(
                        operation=operation,
                        context={
                            "app_name": app_name,
                            "message_type": self.message_type,
                            "user": meta.get("user", {}),
                            "description": meta.get("description", ""),
                            "uid": message.get("uid"),
                            "obj": obj
                        }
                    )

class MessageHandler:
    _handlers = []

    def __init__(self):
        self._topics = []
        self._event_clients = []
        self.init_topics()

    @staticmethod
    def handler(app, event_client, message):
        log.debug("Handler received message: %s",message)
        for nh in [nh for nh in MessageHandler._handlers if nh.message_type == message.get("message_type")]:
            nh.handle_event(message)

    def init_topics(self):
        app = conf.get_application_by_filter(name="notifications")[0]  # find the notification app configuration
        for event_type in app["harness"]["events"]:
            for notification_app in app["harness"]["events"][event_type]:
                for notification_type in notification_app["types"]:
                    nh = NotificationHandler(
                        event_type,
                        notification_app["app"], 
                        notification_type["name"], 
                        notification_type["events"])
                    MessageHandler._handlers.append(nh)
                    if nh.topic_id not in self._topics:
                        # if topic not yet in the list op topics create one (async_consume)
                        event_client = EventClient(nh.topic_id)
                        event_client.async_consume(app=None, handler=self.handler, group_id="ch-notifications")
                        self._event_clients.append(event_client)
                        self._topics.append(nh.topic_id)

    def stop(self):
        log.info("Closing the topics")
        for event_client in self._event_clients:
            log.info(f"Closing topic {event_client.topic_id}")
            event_client.close()


mh = None


def setup_event_service():
    global mh
    mh = MessageHandler()


def stop_event_services():
    global mh
    if mh:
        mh.stop()
