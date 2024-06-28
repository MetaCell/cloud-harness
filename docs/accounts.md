## Manage user accounts
A user account must be provided to access to the MNP secured applications.

1. Login to the administration console on https://accounts.MYDOMAIN with user `admin`:`metacell`. 

> Change the password immediately if you are on a production environment!
2. Add a user (menu Users on the left)
1. Set a password to the user (tab credentials). Set temporary as *off*
1. On Role Mappings, assign all roles to the user

## Configure a Gatekeeper

To put a gatekeeper in front of your application, set `harness/secured` to `true`
in the application's values.yaml.

To assign paths and roles, set `uri_role_mapping` as you would do in the [gatekeeper configuration file resources](https://github.com/gogatekeeper/gatekeeper/blob/master/docs/content/configuration/_index.md).

Example:

```yaml
harness:
  ...
  secured: true
  uri_role_mapping:
  - uri: /*
    roles:
    - administrator
```

See the [Gogatekeeper official documentation](https://github.com/gogatekeeper/gatekeeper/blob/master/docs/content/userguide/_index.md) for more.


## Backend development
### Secure and enpoint with the Gatekeeper

The simplest solution to give authorized access to some api endpoint is to configure the gatekeeper (see above).

```yaml
harness:
  ...
  secured: true
  uri_role_mapping:
  - uri: /admin/*
    methods:
    - POST
    - PUT
    - DELETE
    roles:
    - administrator
  - uri: /open-page
    white-listed: true
```

Note: the `secured` attribute by default denies entry to every page.
Can add white listed page but depending on the application a "default open"
logic can be more appropriate.

To specify a default open logic set secured to "open" and add all the secured paths to the mapping
```yaml
harness:
  ...
  secured: open
```

#### Proxy specific configurations
Proxy configurations can be personalized in the application in the case that we want to have more restrictive values than the global ones (see [here](./ingress-domains-proxies.md#proxy-configurations) for more )

```yaml
harness:
  proxy:
    timeout:
      # -- Timeout for proxy connections in seconds.
      send:
      # -- Timeout for proxy responses in seconds.
      read:
      keepalive:
    payload:
      # -- Maximum size of payload in MB
      max: 
```
### Secure an enpoint with OpenAPI

In every api endpoint that you want to secure, add the bearerAuth security as in the example:

```yaml
paths:
  /valid:
    get:
      summary: Check if the token is valid. Get a token by logging into the base url
      security:
        - bearerAuth: []
```

In the components section, add the following
```yaml
components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      x-bearerInfoFunc: cloudharness.auth.decode_token
```

See the examples:

* [Secured with openapi](/applications/samples/backend/samples/controllers/auth_controller.py) (actually a normal api, the openapi configuration does everything)
* [Openapi configuration: add bearerAuth](/applications/samples/api/samples.yaml#L20)  
* [Openapi configuration: configure bearer handler](/applications/samples/api/samples.yaml#L141)  


### Use the AuthClient

The Cloudharness AuthClient is a handy wrapper for the Keycloak REST API.
This wrapper class can be used to retrieve the current user of the http(s) request
or to retrieve the Keycloak groups with all users etc.

All functions of the AuthClient class are wrapped by the `with_refreshtoken` decorator
to auto refresh the token in case the token is expired. There is no need to manually
refresh the token.

`AuthClient` uses the `admin_api` account to log in into the Keycloak admin REST api
the password is stored in the `accounts` secret and is retrieve using the Cloudharness
`get_secret` function (imported from `cloudharness.utils.secrets`)

For more information about the usage of the `AuthClient` see the Python doc strings

---
**Important note:**

it is mandatory that the application deployment has a hard dependency to the 
`accounts` application. This dependency will mount the accounts secret to the pods.
---


Examples:
```python
from cloudharness.auth.keycloak import AuthClient
from cloudharness.models import User

ac = AuthClient()

current_user: User = ac.get_current_user()
email = current_user.email

all_groups = ac.get_groups(with_members=True)
```
## Configure default test users and client roles

Test users and client roles can be added on each application's `values.yaml` file.

Example:

```yaml
harness:
  name: myapp
  accounts:
    roles:
    - role1
    - role2
    - role3
    users:
    - username: sample@testuser.com
      clientRoles:
      - role1
      realmRoles:
      - offline_access
    - username: samples-test-user2
      email: sample2@testuser.com
      password: test1
      clientRoles:
      - role1
      realmRoles:
      - offline_access
```

The above configuration will create 3 client roles under the "myapp" client and 2 users.

---
**NOTE**
Users and client roles are defined as a one-off initialization: they
can be configured only on a new deployment and cannot be updated.
---
