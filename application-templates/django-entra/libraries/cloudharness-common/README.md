# CloudHarness backend library (Microsoft Entra edition)

A trimmed copy of the CloudHarness core library, vendored in the application. It keeps the
configuration helpers (`cloudharness.applications`, `cloudharness.utils.config`, `cloudharness.utils.secrets`,
`cloudharness.utils.env`), logging and Sentry, and replaces the Keycloak auth client with
Microsoft Entra ID support. The Keycloak, Kafka events, Argo workflows and Kubernetes modules are removed.

## Installation

```
pip install -e ../models
pip install -e .
```

## Entra auth

`cloudharness.auth.entra` reads the `entra` section of the application values.yaml (or the `ENTRA_*`
environment variables) and validates the Entra access tokens:

```python
from cloudharness.auth import decode_token, get_current_user_claims, get_current_user_id, EntraIdentity

claims = decode_token(token)              # raises InvalidToken
identity = EntraIdentity.from_claims(claims)
```

The token is checked against the tenant signing keys (cached), the expiration, the issuer
(v1 and v2 endpoints of the tenant), the audience (`client_id` or `api_audience`) and the tenant id.

## Middleware

The Django (`cloudharness.middleware.django.CloudharnessMiddleware`) and ASGI
(`cloudharness.middleware.asgi.AuthMiddleware`) middlewares store the bearer token of the
`Authorization` header of the request in a context variable, used by `get_current_user_claims`.

```python
MIDDLEWARE = [
    ...
    'cloudharness.middleware.django.CloudharnessMiddleware',
    ...
]
```

## Tests

```
pip install -r test-requirements.txt
pytest tests
```
