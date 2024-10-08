# Neo4j browser helm chart

Enable this application to deploy a Neo4j server with the neo4j browser enabled.

## How to use
The neo4j browser will be enabled at neo4j.[DOMAIN].

![Neo4j browser login](docs/browser-login.png)

The default credentials are set in the [application configuration file](deploy/values.yaml).

It is recommended to change the password during the first login, such as:

```
ALTER USER default SET PASSWORD '<new-password>'
```

## Implementation
This implementation uses the Neo4j reverse proxy server to enable usage via Ingress and http(s).

For more information, see https://neo4j.com/docs/operations-manual/current/kubernetes/accessing-neo4j-ingress/

