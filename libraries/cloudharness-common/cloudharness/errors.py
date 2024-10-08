class EventTopicProduceException(Exception):
    def __init__(self, topic_id):
        self.topic_id = topic_id
        Exception.__init__(self, f'Events: unable to produce message to topic -> {topic_id}')


class EventTopicCreationException(Exception):
    def __init__(self, topic_id):
        self.topic_id = topic_id
        Exception.__init__(self, f'Events: unable to create topic -> {topic_id}')


class EventTopicConsumeException(Exception):
    def __init__(self, topic_id):
        self.topic_id = topic_id
        Exception.__init__(self, f'Events: unable to consume messages from topic -> {topic_id}')


class EventTopicDeleteException(Exception):
    def __init__(self, topic_id):
        self.topic_id = topic_id
        Exception.__init__(self, f'Events: unable to delete topic -> {topic_id}')


class EventGeneralException(Exception):
    pass


class MongoDBConfError(Exception):
    pass
