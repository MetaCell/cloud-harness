# Develop in the backend with CloudHarness

## Base images and libraries
TODO 

## Create a default Backend with Flask and Openapi
TODO

## Use the CloudHarness Python library

### Get applications references and configurations
TODO

### Check authentication and Authorization

#### Secure a RESTful API

Note: this document is not a tutorial on how to secure an application on Cloud Harness. The aim is giving the CH developer an insight on how it's implemented. To see an example of a secured api, see samples application:

* [Secured backend api](/applications/samples/backend/samples/controllers/auth_controller.py) (actually a normal api, the openapi configuraition does everything)
* [Openapi configuration: add bearerAuth](/applications/samples/api/samples.yaml#L20)  
* [Openapi configuration: configure bearer handler](/applications/samples/api/samples.yaml#L141)  


Following some insights to have a web application dashboard secured with username and password and then interact with a RESTful API using JWT 

Using OpenAPI to generate the code, we introduce the following security

```yaml
security:
  - bearerAuth: []
components:
  securitySchemes: 
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

Then we look for `security_controller.py` file:

```python
def info_from_bearerAuth(token):
    SCHEMA = 'https://'
    AUTH_DOMAIN = os.environ.get('AUTH_DOMAIN')
    AUTH_REALM = os.environ.get('AUTH_REALM')
    BASE_PATH = f"//{os.path.join(AUTH_DOMAIN, 'auth/realms', AUTH_REALM)}"
    AUTH_PUBLIC_KEY_URL = urljoin(SCHEMA, BASE_PATH)

    # We extract KC public key to validate the JWT we receive 
    KEY = json.loads(requests.get(AUTH_PUBLIC_KEY_URL, verify=False).text)['public_key'] 
    
    # Create the key
    KEY = f"-----BEGIN PUBLIC KEY-----\n{KEY}\n-----END PUBLIC KEY-----"
    
    try:
        # Here we decode the JWT
        decoded = jwt.decode(token, KEY, audience='account', algorithms='RS256')
    except:
        current_app.logger.debug(f"Error validating user: {sys.exc_info()}")
        return None
    
    # Here we proceed to do all the validation we need to check if we grant access to the RESTful API 
    valid = 'offline_access' in decoded['realm_access']['roles']
    current_app.logger.debug(valid)
    return {'uid': 'user_id' }
```

#### Using the AuthClient

The Cloudharness AuthClient is a handy wrapper for the Keycloak REST API.
This wrapper class can be used to retrieve the current user of the http(s) request
or to retrieve the Keycloak groups with all users etc.

All functions of the AuthClient class are wrapped by the `with_refreshtoken` decorator
to auto refresh the token in case the token is expired. There is no need to manually
refresh the token.

`AuthClient` uses the `admin_api` account to log in into the Keycloak admin REST api
the password is stored in the `accounts` secret and is retrieve using the Cloudharness
`get_secret` function (imported from `cloudharness.utils.secrets`)

<br/>

For more information about the usage of the `AuthClient` see the Python doc strings

<br/>

**Important note:**

it is mandatory that the application deployment has a hard dependency to the 
`accounts` application. This dependency will mount the accounts secret to the pods.

<br/>

Examples:
```python
from cloudharness.auth.keycloak import AuthClient

ac = AuthClient()

def example1():
  current_user = ac.get_current_user()

def exampl2():
  all_groups = ac.get_groups(with_members=True)
```


### Run workflows

See [the workflows api](./workflows-api.md) dedicated document.

## Debug inside the cluster

See [here](../../build-deploy/local-deploy/debug.md).