#!/bin/bash
set -e
set -x
cp /etc/kafka-configmap/log4j.properties /etc/kafka/

KAFKA_BROKER_ID=${HOSTNAME##*-}
SEDS=("s/#init#broker.id=#init#/broker.id=$KAFKA_BROKER_ID/")
LABELS="kafka-broker-id=$KAFKA_BROKER_ID"
ANNOTATIONS=""

hash kubectl 2>/dev/null || {
  SEDS+=("s/#init#broker.rack=#init#/#init#broker.rack=# kubectl not found in path/")
} && {
  ZONE=$(kubectl get node "$NODE_NAME" -o=go-template='{{index .metadata.labels "failure-domain.beta.kubernetes.io/zone"}}')
  if [ "x$ZONE" == "x" ]; then
    SEDS+=("s/#init#broker.rack=#init#/#init#broker.rack=# zone label not found for node $NODE_NAME/")
  else
    SEDS+=("s/#init#broker.rack=#init#/broker.rack=$ZONE/")
    LABELS="$LABELS kafka-broker-rack=$ZONE"
  fi

  OUTSIDE_HOST=$(kubectl get node "$NODE_NAME" -o jsonpath='{.status.addresses[?(@.type=="InternalIP")].address}')
  OUTSIDE_PORT=$((32400 + ${KAFKA_BROKER_ID}))
  SEDS+=("s|#init#advertised.listeners=PLAINTEXT://#init#|advertised.listeners=PLAINTEXT://:9092,OUTSIDE://${OUTSIDE_HOST}:${OUTSIDE_PORT}|")
  ANNOTATIONS="$ANNOTATIONS kafka-listener-outside-host=$OUTSIDE_HOST kafka-listener-outside-port=$OUTSIDE_PORT"

  if [ ! -z "$LABELS" ]; then
    kubectl -n $POD_NAMESPACE label pod $POD_NAME $LABELS || echo "Failed to label $POD_NAMESPACE.$POD_NAME - RBAC issue?"
  fi
  if [ ! -z "$ANNOTATIONS" ]; then
    kubectl -n $POD_NAMESPACE annotate pod $POD_NAME $ANNOTATIONS || echo "Failed to annotate $POD_NAMESPACE.$POD_NAME - RBAC issue?"
  fi
}
printf '%s\n' "${SEDS[@]}" | sed -f - /etc/kafka-configmap/server.properties > /etc/kafka/server.properties.tmp
[ $? -eq 0 ] && mv /etc/kafka/server.properties.tmp /etc/kafka/server.properties

# wait for events to be up & running
# install curl first
apt update && apt install -y curl
for i in {1..100}
do
  sleep 5
  if curl events; then
    curl events:80/clusters --data 'name=cluster-'${POD_NAMESPACE}'&zkHosts=zookeeper:2181&kafkaVersion=2.2.0&jmxEnabled=true&jmxUser=&jmxPass=&logkafkaEnabled=true&pollConsumers=true&activeOffsetCacheEnabled=true&tuning.brokerViewUpdatePeriodSeconds=30&tuning.clusterManagerThreadPoolSize=2&tuning.clusterManagerThreadPoolQueueSize=100&tuning.kafkaCommandThreadPoolSize=2&tuning.kafkaCommandThreadPoolQueueSize=100&tuning.logkafkaCommandThreadPoolSize=2&tuning.logkafkaCommandThreadPoolQueueSize=100&tuning.logkafkaUpdatePeriodSeconds=30&tuning.partitionOffsetCacheTimeoutSecs=5&tuning.brokerViewThreadPoolSize=2&tuning.brokerViewThreadPoolQueueSize=1000&tuning.offsetCacheThreadPoolSize=2&tuning.offsetCacheThreadPoolQueueSize=1000&tuning.kafkaAdminClientThreadPoolSize=2&tuning.kafkaAdminClientThreadPoolQueueSize=1000&tuning.kafkaManagedOffsetMetadataCheckMillis=30000&tuning.kafkaManagedOffsetGroupCacheSize=1000000&tuning.kafkaManagedOffsetGroupExpireDays=7&securityProtocol=PLAINTEXT&saslMechanism=DEFAULT&jaasConfig=' -X POST
    exit 0
  fi
done
