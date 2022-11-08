# Events

The events application is created upon a Kafka StatefulSet.

## Access the Kafka manager

The [Kafka Manager](https://github.com/yahoo/CMAK) is preconfigured and accessible at the address https://events.MYDOMAIN.

## Configure the Kafka parameters

Override the [broker server configuration file](../applications/events/deploy/resources/broker/server.properties) to change most of the relevant configurations.

## Locally test Kafka queue calls
The following allows to call/test to Kafka locally.
It is useful to test and debug an application which listens/writes to the queue

Kafka broker to local 9092
```
kubectl port-forward --namespace mnp $(kubectl get po -n mnp | grep kafka-0 | \awk '{print $1;}') 9092:9092
```

Also add to your hosts file
```
127.0.0.1      kafka-0.broker.mnp.svc.cluster.local bootstrap.mnp.svc.cluster.local
```

## Backend library

### Data Create, Delete and Change Events

Data change events are a special kind of event used to notify the system that some
data is created/changed/deleted.

The best way to send a CDC Event is by a decorator in a service function:

```python
from cloudharness.events.decorators import send_event

@send_event(message_type="my_object", operation="create")
def create_myobject(self, body):
    created_object = ... # database logic
    return created_object
```


The above event can be consumed as:

```python
from cloudharness.events.client import EventClient
from cloudharness.models import CDCEvent

def handler(app, event_client, message: CDCEvent):
    ...

event_client = EventClient("my_object")
event_client.async_consume(handler=handler, group_id="ch-notifications")
```

For a concrete code example of the CDC events, see the [notification application](/applications/notifications/server/notifications/controllers/notifications_controller.py)

### Consume and handle a generic event

```python
from cloudharness.events.client import EventClient

def my_callback(event_client, message):
    ...

client = EventClient("my-topic")
client.async_consume(group_id="my-group", handler=my_callback)
```


### Produce a generic event

```python
from cloudharness.workflows.utils import notify_queue

my_message = {"a": "b"}
notify_queue("my-topic", my_message)
```