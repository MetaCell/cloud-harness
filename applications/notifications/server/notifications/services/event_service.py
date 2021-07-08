import json
import time

from cloudharness import log
from cloudharness.events.client import EventClient
from cloudharness.utils.config import CloudharnessConfig as conf
from kafka.errors import TopicAlreadyExistsError
from types import SimpleNamespace as Namespace

from notifications.services.notification_service import notify


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
                    notify(
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
        for app in conf.get_application_by_filter(name="notifications"):  # find the notification app configuration
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
                            try:
                                # try to create the topic, if it exists it will throw an exception
                                log.info(f"Setting up topic {nh.topic_id}")
                                event_client.create_topic()
                            except TopicAlreadyExistsError as e:
                                pass
                            except Exception as e:
                                log.error(f"Error creating topic {nh.topic_id}", exc_info=e)
                            event_client.async_consume(app=None, handler=self.handler, group_id="ch-notifications")
                            self._event_clients.append(event_client)
                            self._topics.append(nh.topic_id)

    def stop(self):
        log.info("Closing the topics")
        for event_client in self._event_clients:
            log.info(f"Closing topic {event_client.topic_id}")
            event_client.close()


mh = None


def test_kafka_running():
    EventClient("ch-notifications-testing")._get_consumer()


def setup_event_service():
    try:
        test_kafka_running()
    except:
        nap_time = 15
        time.sleep(nap_time)  # sleep a few seconds before st
        raise Exception("Kafka not running, exiting...")
    global mh
    mh = MessageHandler()


def stop_event_services():
    global mh
    if mh:
        mh.stop()
