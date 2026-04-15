# Events

The events application runs a Kafka `StatefulSet` in KRaft mode.

## Access Kafka UI

The [Kafka UI](https://github.com/provectus/kafka-ui) application is preconfigured and accessible at the address `https://events.MYDOMAIN`.

## Configure the Kafka parameters

Override the `kafka` values in [applications/events/deploy/values.yaml](../applications/events/deploy/values.yaml) to change the relevant broker parameters.

The `kafka.config` map is converted into Kafka `server.properties` settings automatically. For example:

```yaml
kafka:
  config:
    num.partitions: "6"
    auto.create.topics.enable: "false"
```

The default override set is intentionally small and only keeps the single-node KRaft deployment behavior stable.

## Reset local KRaft state

Kafka metadata and log state are stored on the `kafka` PVC. If a local Minikube deployment gets stuck because of stale KRaft state, delete the broker pod and its PVC before redeploying:

```bash
kubectl delete pod -n test kafka-0
kubectl delete pvc -n test data-kafka-0
```

Then run `harness-deployment` again to recreate the broker with a fresh volume.

## Locally test Kafka queue calls
The following allows to call/test to Kafka locally.
It is useful to test and debug an application which listens/writes to the queue

Kafka broker to local `9092`
```
kubectl port-forward --namespace mnp svc/bootstrap 9092:9092
```

Also add to your hosts file
```
127.0.0.1      bootstrap.mnp.svc.cluster.local kafka-0.broker.mnp.svc.cluster.local
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
