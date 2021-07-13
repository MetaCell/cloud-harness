import os
import sys
import threading
import time
import traceback
import logging

from time import sleep
from json import dumps, loads
from keycloak.exceptions import KeycloakGetError
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError, KafkaTimeoutError

from cloudharness import log
from cloudharness.auth.keycloak import AuthClient
from cloudharness.errors import *
from cloudharness.utils import env
from cloudharness.utils.config import CloudharnessConfig as config

logging.getLogger('kafka').setLevel(logging.ERROR)


AUTH_CLIENT = None
CURRENT_APP_NAME = config.get_current_app_name()

def get_authclient():
    global AUTH_CLIENT
    if not AUTH_CLIENT:
        AUTH_CLIENT = AuthClient()
    return AUTH_CLIENT


class EventClient:
    def __init__(self, topic_id):
        self.topic_id = topic_id
        self.client_id = env.get_cloudharness_events_client_id()
        self.service = env.get_cloudharness_events_service()

    def _get_consumer(self, group_id='default') -> KafkaConsumer:
        return KafkaConsumer(self.topic_id,
                             bootstrap_servers=self.service,
                             auto_offset_reset='earliest',
                             enable_auto_commit=True,
                             group_id=group_id,
                             value_deserializer=lambda x: loads(x.decode('utf-8')))


    def create_topic(self):
        """ Connects to cloudharness Events and creates a new topic
        Return:
            True if topic was created correctly, False otherwise.
        """
        ## Connect to kafka
        admin_client = KafkaAdminClient(bootstrap_servers=self.service,
                                        client_id=self.client_id)
        # ## Create topic

        new_topic = NewTopic(name=self.topic_id, num_partitions=1, replication_factor=1)
        try:
            result = admin_client.create_topics(new_topics=[new_topic], validate_only=False)
            log.info(f"Created new topic {self.topic_id}")
            return result
        except TopicAlreadyExistsError as e:
            # topic already exists "no worries", proceed
            return True
        except Exception as e:
            log.error(f"Error creating the new Topics --> {e}", exc_info=True)
            raise EventGeneralException from e

    def produce(self, message: dict):
        ''' Write a message to the current topic
            Params:
                message: dict with message to be published.
            Return:
                True if the message was published correctly, False otherwise.
        '''
        producer = KafkaProducer(bootstrap_servers=self.service,
                                 value_serializer=lambda x: dumps(x).encode('utf-8'))
        try:
            return producer.send(self.topic_id, value=message)
        except KafkaTimeoutError as e:
            try:
                # it could be that the topic wasn't created yet
                # let's try to create it and resend the message
                self.create_topic()
                return producer.send(self.topic_id, value=message)
            except KafkaTimeoutError as e:
                log.error("Not able to fetch topic metadata", exc_info=True)
                raise EventTopicProduceException from e
        except Exception as e:
            log.error(f"Error produce to topic {self.topic_id} --> {e}", exc_info=True)
            raise EventGeneralException from e
        finally:
            producer.close()

    def gen_topic_id(topic_type, message_type):
        return f"{CURRENT_APP_NAME}.{topic_type}.{message_type}"

    @staticmethod
    def send_event(message_type, operation, obj, uid="id", func_name=None, func_args=None, func_kwargs=None, topic_id=None):
        """
        Send a CDC (change data capture) event into a topic
        The topic name is generated from the current app and message type
        e.g. workflows.cdc.jobs

        Params:
            message_type: the type of the message (relates to the object type) e.g. jobs
            operation: the operation on the object e.g. create / update / delete
            obj: the object itself
            uid: the unique identifier attribute of the object
            func_name: the caller function name defaults to None
            func_args: the caller function "args" defaults to None
            func_kwargs: the caller function "kwargs" defaults to None
            topic_id: the topic_id to use, generated when None, defaults to None
        """
        if not topic_id:
            topic_id = EventClient.gen_topic_id(
                topic_type="cdc",
                message_type=message_type)

        ec = EventClient(topic_id=topic_id)
        try:
            if not isinstance(obj, dict):
                if hasattr(obj, "to_dict"):
                    resource = obj.to_dict()
                else:
                    resource = vars(obj)
            resource_id = resource.get(uid)
            try:
                # try to get the current user
                user = get_authclient().get_current_user()
            except KeycloakGetError:
                user = {}

            # serialize only the func args that can be serialized
            fargs = []
            for a in func_args:
                try:
                    fargs.append(loads(dumps(a)))
                except Exception as e:
                    # argument can't be serialized
                    pass

            # serialize only the func kwargs that can be serialized
            fkwargs = []
            for kwa, kwa_val in func_kwargs.items():
                try:
                    fkwargs.append({
                        kwa: loads(dumps(kwa_val))
                    })
                except Exception as e:
                    # keyword argument can't be serialized
                    pass

            # send the message
            ec.produce(
                {
                    "meta": {
                        "app_name": CURRENT_APP_NAME,
                        "user": user,
                        "func": str(func_name),
                        "args": fargs,
                        "kwargs": fkwargs,
                        "description": f"{message_type} - {resource_id}",
                    },
                    "message_type": message_type,
                    "operation": operation,
                    "uid": resource_id,
                    "resource": resource
                }
            )
            log.info(f"sent cdc event {message_type} - {operation} - {resource_id}")
        except Exception as e:
            log.error('send_event error.', exc_info=True)

    def consume_all(self, group_id='default') -> list:
        ''' Return a list of messages published in the topic '''

        consumer = self._get_consumer(group_id)
        try:
            for topic in consumer.poll(10000).values():
                return [record.value for record in topic]
        except Exception as e:
            log.error(f"Error trying to consume all from topic {self.topic_id} --> {e}", exc_info=True)
            raise EventTopicConsumeException from e
        finally:
            consumer.close()

    def delete_topic(self) -> bool:

        log.debug("Deleting topic " + self.topic_id)
        ## Connect to kafka
        admin_client = KafkaAdminClient(bootstrap_servers=self.service,
                                        client_id=self.client_id)
        ## Delete topic
        try:
            admin_client.delete_topics([self.topic_id])
            return True
        except UnknownTopicOrPartitionError as e:
            log.error(f"Topic {self.topic_id} does not exists.")
            raise EventTopicDeleteException from e

        except Exception as e:
            log.error(f"Error deleting the Topic {self.topic_id} --> {e}", exc_info=True)
            raise EventGeneralException from e

    def close(self):
        if hasattr(self, '_consumer_thread'):
            # for now no cleanup tasks to do
            pass

    def _consume_task(self, app=None, group_id=None, handler=None):
        log.info(f'Kafka consumer thread started, listening for messages in queue: {self.topic_id}')
        while True:
            try:
                self.consumer = self._get_consumer(group_id)
                for message in self.consumer:
                    try:
                        handler(event_client=self, app=app, message=message.value)
                    except Exception as e:
                        log.error(f"Error during execution of the consumer Topic {self.topic_id} --> {e}", exc_info=True)
                self.consumer.close()
            except Exception as e:
                    log.error(f"Error during execution of the consumer Topic {self.topic_id} --> {e}", exc_info=True)
                    time.sleep(15)

    def async_consume(self, app=None, handler=None, group_id='default'):
        log.debug('creating thread')
        if app:
            log.debug('get current object from app')
            app = app._get_current_object()
        self._consumer_thread = threading.Thread(
            target=self._consume_task, 
            kwargs={'app': app,
                    'group_id': group_id,
                    'handler': handler})
        self._consumer_thread.daemon = True
        self._consumer_thread.start()
        log.debug('thread started')

if __name__ == "__main__":
    # creat the required os env variables
    os.environ['CLOUDHARNESS_EVENTS_CLIENT_ID'] = env.get_cloudharness_events_client_id()
    os.environ['CLOUDHARNESS_EVENTS_SERVICE'] = env.get_cloudharness_events_service()

    # instantiate the client
    client = EventClient('test-sync-op-results-qcwbc')

    # create a topic from env variables
    # print(client.create_topic())
    # publish to the prev created topic
    # print(client.produce({"message": "In God we trust, all others bring data..."}))
    # read from the topic
    print(client.consume_all('my-group'))
    # delete the topic
    # print(client.delete_topic())
