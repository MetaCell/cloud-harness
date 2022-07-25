# Admin Event Listener for Keycloak

## Building
```
mvn clean install
cp ./ear-module/target/metacell-admin-event-listener-bundle-0.1.0.ear ../plugins/
```

## Install

* Build the accounts image (run harness-deploy and helm install/upgrade commands)
* Log into the Keycloak admin
* open the Manage / Events page
* go to the Config tab and add the metacell-admin-event-listener to the Event listeners
