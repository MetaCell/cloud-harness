import json
import time

from cloudharness import log
from cloudharness.events.client import EventClient
from cloudharness.utils.config import CloudharnessConfig as conf
from flask import current_app
from kafka.errors import TopicAlreadyExistsError
from types import SimpleNamespace as Namespace

from .notification_service import notify


class NotificationHandler:
    def __init__(self, app_name, message_type, events):
        self.message_type = message_type
        self.events = events
        self.topic_id = f"{app_name}.cdc.{message_type}"

    def handle_event(self, app, topic_id, message):
        """
        Handle the event

        Args:
            app: the current flask app object
            topic_id: the name of the topic the message was received in
            message: the message
        """
        if self.topic_id == topic_id:
            operation = message.get("operation")
            for event in self.events:
                if event == operation:
                    app_name = message.get("app_name")
                    obj_id = message.get("uid")
                    obj = json.loads(json.dumps(message.get("resource")), object_hook=lambda d: Namespace(**d))
                    log.info(f"{app_name} sent {operation} {self.message_type} with id: {obj_id} message")
                    notify(
                        operation=operation,
                        context={
                            "app_name": app_name,
                            "message_type": self.message_type,
                            "user": message.get("user"),
                            "description": message.get("description"),
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
        log.info(f"Handler received message: {message}")
        for nh in [nh for nh in MessageHandler._handlers if nh.topic_id == event_client.topic_id]:
            nh.handle_event(app, event_client.topic_id, message)

    def init_topics(self):
        for app in conf.get_application_by_filter(harness__notifications=True):  # find all apps with notification configuration
            for notification in app.harness.notifications:
                message_type = notification["type"]
                nh = NotificationHandler(app["harness.name"], 
                    message_type, 
                    notification["events"])
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
                    event_client.async_consume(app=current_app, handler=self.handler, group_id="ch-notifications")
                    self._event_clients.append(event_client)
                    self._topics.append(nh.topic_id)

    def stop(self):
        log.info("Closing the topics")
        for event_client in self._event_clients:
            log.info(f"Closing topic {event_client.topic_id}")
            event_client.close()


mh = None


def test_kafka_running():
    try:
        EventClient("ch-notifications-testing")._get_consumer()
    except:
        return False
    return True


def setup_event_service():
    kafka_running = False
    nap_time = 15
    while not kafka_running:
        kafka_running = test_kafka_running()
        if not kafka_running:
            log.error(f"Kafka not running? Going for a {nap_time} seconds power nap and will try again later")
            time.sleep(nap_time)  # sleep xx seconds and try again
    global mh
    mh = MessageHandler()


def stop_event_services():
    global mh
    if mh:
        mh.stop()
