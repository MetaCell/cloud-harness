import os
import sys
import threading
import time
import traceback

from time import sleep
from json import dumps, loads
from kafka import KafkaProducer, KafkaConsumer
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError, UnknownTopicOrPartitionError, KafkaTimeoutError

from cloudharness import log
from cloudharness.errors import *
from cloudharness.utils import env


class EventClient:
    def __init__(self, topic_id):
        self.client_id = env.get_cloudharness_events_client_id()
        self.topic_id = topic_id
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
        log.info(f"Creating topic {self.topic_id}")
        admin_client = KafkaAdminClient(bootstrap_servers=self.service,
                                        client_id=self.client_id)
        # ## Create topic

        topic_list = []
        for topic in [NewTopic(name=self.topic_id, num_partitions=1, replication_factor=1)]:
            try:
                # validate if the Topic already exists
                admin_client.create_topics(new_topics=[topic], validate_only=True)
                # if not then add it to the topic_list
                topic_list.append(topic)
            except TopicAlreadyExistsError as e:
                pass
            except Exception as e:
                log.error(f"Ups... We had an error validating the creation of topic {topic.name} --> {e}", exc_info=True)
                raise EventGeneralException from e

        # now create the missing topics
        try:
            return admin_client.create_topics(new_topics=topic_list, validate_only=False)
        except TopicAlreadyExistsError as e:
            # topic already exists "no worries", proceed
            pass
        except Exception as e:
            log.error(f"Ups... We had an error creating the new Topics --> {e}", exc_info=True)
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
            log.error("Ups... Not able to fetch topic metadata", exc_info=True)
            raise EventTopicProduceException from e
        except Exception as e:
            log.error(f"Ups... We had an error produce to topic {self.topic_id} --> {e}", exc_info=True)
            raise EventGeneralException from e
        finally:
            producer.close()

    def consume_all(self, group_id='default') -> list:
        ''' Return a list of messages published in the topic '''

        consumer = self._get_consumer(group_id)
        try:
            for topic in consumer.poll(10000).values():
                return [record.value for record in topic]
        except Exception as e:
            log.error(f"Ups... We had an error trying to consume all from topic {self.topic_id} --> {e}", exc_info=True)
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
            log.error(f"Ups... We had an error deleting the Topic {self.topic_id} --> {e}", exc_info=True)
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
                        log.error(f"Ups... there was an error during execution of the consumer Topic {self.topic_id} --> {e}", exc_info=True)
                        log.error(traceback.print_exc())
                self.consumer.close()
            except Exception as e:
                    log.error(f"Ups... there was an error during execution of the consumer Topic {self.topic_id} --> {e}", exc_info=True)
                    log.error(traceback.print_exc())
                    time.sleep(10)
        # log.info(f'Kafka consumer thread {self.topic_id} stopped')

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
