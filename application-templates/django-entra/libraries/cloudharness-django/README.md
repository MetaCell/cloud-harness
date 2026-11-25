# cloudharness-django (Microsoft Entra edition)

A Django library that integrates a [CloudHarness](https://github.com/MetaCell/cloud-harness) application
with **Microsoft Entra ID** (single tenant). It replaces the Keycloak (`accounts`), Kafka (`events`) and
gatekeeper based integration: the application authenticates its users itself and provisions them in
Django just in time.

The CloudHarness gatekeeper (gogatekeeper) is not used: it only supports Keycloak as identity provider
(its discovery url must contain `/realms/<realm>`) and it does not read the Entra `roles` claim.

## How it works

```
Browser                                       API client
   │ GET /some/page                              │ Authorization: Bearer <Entra access token>
   ▼                                             ▼
LoginRequiredMiddleware ◄──────────── BearerTokenMiddleware
   │ not logged in → 302 /oidc/login/            │ validates signature (tenant JWKS), exp, iss, aud, tid
   │ no app role   → 403                         │ → EntraBackend → UserService.sync_user (cached 60 s)
   ▼                                             ▼
/oidc/login/ ──► Entra authorize (code + PKCE) ──► /oidc/callback/
                                                   │ msal redeems the code, validates the ID token
                                                   │ EntraBackend → UserService.sync_user(claims)
                                                   ▼
                                                 Django session
```

* **Users** are created or updated from the token claims at every login (`oid` → `Member.oid`,
  `preferred_username` → username, `email`, `given_name`/`family_name` or `name`). There is no
  background synchronisation: changes in Entra are applied at the next login (or after
  `BEARER_TOKEN_USER_CACHE_TTL` for bearer tokens). Users without a usable password are created, so
  Entra users can only log in through Entra.
* **Roles** are Entra *app roles* (the `roles` claim). They are mirrored as Django groups and set the
  flags: the admin role makes a superuser with Django admin access, the other roles give access to the
  application only.
* **Access**: every path requires a logged in user with any of the app roles (`AUTH_ALL_ROLES`), except
  `AUTH_EXEMPT_URLS`. This replaces the gatekeeper `uri_role_mapping`.

## Entra app registration

1. *App registrations → New registration*, single tenant. Add the **Web** redirect URIs
   `https://<subdomain>.<domain>/oidc/callback/` (and `http://localhost:8000/oidc/callback/` for local development).
2. *Certificates & secrets*: create a client secret.
3. *App roles*: create the roles named as in the settings (e.g. `__APP_NAME__-administrator`,
   `__APP_NAME__-user`), allowed member type *Users/Groups*.
4. *Enterprise applications → the app → Users and groups*: assign the roles to users or groups.
   Optionally set *Assignment required* so that unassigned users cannot sign in at all.
5. To call the API with bearer tokens (delegated access tokens only, with the `scp` claim): *Expose an API*, set the Application ID URI
   (`api://<client id>`, the default accepted audience) and add a scope.
6. Optional: *Token configuration → Add optional claim* `email`, `given_name`, `family_name` to the ID and access tokens.

## Configuration

In the application `deploy/values.yaml`:

```yaml
harness:
  secured: false              # no gatekeeper
  secrets:
    entra-client-secret: ""   # set by the CI/CD pipeline, helm --set or a secret manager ("" not null)
    django-secret-key: ""     # Django SECRET_KEY, generated once by CloudHarness
entra:
  tenant_id: <directory (tenant) id>
  client_id: <application (client) id>
  api_audience: ""            # accepted access token audience, defaults to api://<client id>
  authority_host: https://login.microsoftonline.com
```

Every value can be overridden with the environment variables `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID`,
`ENTRA_CLIENT_SECRET`, `ENTRA_API_AUDIENCE` and `ENTRA_AUTHORITY_HOST` (local development).

In the application `settings.py`:

```python
PROJECT_NAME = "MY_APP"   # must be set before the import

from cloudharness_django.settings import *  # noqa

AUTH_ADMIN_ROLE = "my-app-administrator"
AUTH_USER_ROLE = "my-app-user"
AUTH_ALL_ROLES = [AUTH_ADMIN_ROLE, AUTH_USER_ROLE]
```

The settings import sets `SECRET_KEY` (the `django-secret-key` secret or `DJANGO_SECRET_KEY`; required unless
`DEBUG`), `ALLOWED_HOSTS` (the application host names, service names and `POD_IP`), secure cookies on https,
and adds `cloudharness_django` and `django_prometheus` to `INSTALLED_APPS`, the bearer
token and login required middlewares, the `EntraBackend` authentication backend, the database settings
from the CloudHarness values (SQLite when running outside a deployment) and the `/oidc/` urls.

### Optional settings

| Setting | Default | Description |
|---|---|---|
| `AUTH_REQUIRED` | `True` | Require a logged in user with an app role on every path. Set to `False` to protect the views individually. |
| `AUTH_EXEMPT_URLS` | probes, `/oidc/`, `/admin/login/`, `/static/` except `/static/www/` | Regular expressions of the paths reachable without login. |
| `BEARER_TOKEN_USER_CACHE_TTL` | `60` | Seconds a bearer token user is cached. |
| `USER_CHANGE_ENABLED` | `False` | Allow editing users in the Django admin. |
| `PASSWORD_LOGIN_ENABLED` | `DEBUG` | Password login of local users (`ModelBackend` and the Django admin login form), see Local superusers. |

## Urls

| Url | |
|---|---|
| `/oidc/login/?next=<path>` | Starts the login |
| `/oidc/callback/` | Redirect URI of the app registration |
| `/oidc/logout/` | `POST` with the CSRF token: logs out of the application and of Entra; a `GET` shows a logout button |

## Services

```python
from cloudharness_django.services import get_auth_service, get_user_service, AuthorizationLevel

get_auth_service().get_auth_level(["my-app-user"])     # AuthorizationLevel.USER
get_auth_service().get_user_roles(request.user)        # app roles of a Django user
get_auth_service().has_access(request.user)
```

Token validation helpers are in the `cloudharness` library:

```python
from cloudharness.auth import decode_token, get_current_user_claims, get_current_user_id
```

## Test tokens

Test deployments can accept tokens signed with a local test key besides the Entra ones, so that
API tests can authenticate without a real Entra user: set `entra.test_tokens: true` (only in
`deploy/values-test.yaml`) and the PEM public key in the `entra-test-public-key` secret (or
`ENTRA_TEST_TOKENS=true` and `ENTRA_TEST_PUBLIC_KEY`). The tokens must have the header
`kid: cloudharness-test` and the same issuer, audience and tenant as the Entra tokens.
**Never enable it in production.**

## Local superusers

The password login of local users (e.g. created with `python manage.py createsuperuser`) bypasses
Entra, with its MFA and conditional access policies. It is enabled only with `PASSWORD_LOGIN_ENABLED`,
which defaults to `DEBUG` (local development): `ModelBackend` is then added to the authentication
backends and `/admin/login/` shows the Django password form. If Entra is not configured (no tenant and
client id), `/oidc/login/` then redirects to `/admin/login/`, and the logout returns to `LOGIN_REDIRECT_URL`.

Otherwise (the default in production) `/admin/login/` sends to the Entra login, local users cannot
log in and their existing sessions are not accepted, and a logged-in user without the administrator
role gets a 403 on the Django admin.
