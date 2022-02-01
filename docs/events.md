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

