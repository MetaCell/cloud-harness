# Admin Event Listener for Keycloak

## Building
```
mvn clean install
cp ./jar-module/target/metacell-admin-event-listener-module-1.0.0.jar ../plugins/
```

## Install

* Build the accounts image (run harness-deploy and helm install/upgrade commands)
* Log into the Keycloak admin
* open the Manage / Events page
* go to the Config tab and add the metacell-admin-event-listener to the Event listeners
