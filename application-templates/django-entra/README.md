# __APP_NAME__

Template for a CloudHarness application with a Django-Ninja backend and a React frontend, which
authenticates its users with **Microsoft Entra ID** (single tenant) through OpenID Connect.

It does not depend on Keycloak (`accounts`), Kafka (`events`), the gatekeeper or the CloudHarness base
images: the application handles the login itself, and users are created and updated in Django when they log in.

- [How authentication works](#how-authentication-works)
- [Configure authentication](#configure-authentication)
  - [1. Register the application in Entra](#1-register-the-application-in-entra)
  - [2. Configure the deployment](#2-configure-the-deployment)
  - [3. Assign users](#3-assign-users)
  - [Roles and access](#roles-and-access)
  - [Protecting views and API endpoints](#protecting-views-and-api-endpoints)
  - [Calling the API with a bearer token](#calling-the-api-with-a-bearer-token)
  - [Settings reference](#settings-reference)
- [Using the template for a new application](#using-the-template-for-a-new-application)
- [Local development](#local-development)
- [Tests](#tests)

## How authentication works

Every request goes through two Django middlewares. Browsers use a Django session:
`LoginRequiredMiddleware` redirects a user who is not logged in to `/oidc/login/` (Entra sign-in, authorization
code with PKCE), and `/oidc/callback/` validates the ID token, syncs the user and starts the session.
API clients send an Entra access token instead: `BearerTokenMiddleware` validates it (signature, expiry,
issuer, audience, tenant) and syncs the user from its claims, cached for 60 seconds. In both cases, a user
without an app role gets a 403.

- **Login.** A browser that opens any protected page is redirected to `/oidc/login/`, then to Microsoft.
  After sign-in, `/oidc/callback/` validates the ID token, creates or updates the Django user and starts a
  Django session. The user is then sent back to the page they first asked for.
- **Users** are matched by their Entra object id (`oid`, stored in `cloudharness_django.Member`).
  Username, email, first and last name are copied from the token on every login. Changes in Entra are
  applied at the next login: there is no background synchronisation (no Microsoft Graph).
  Entra users have no usable password, so they can only log in through Entra.
- **Roles** are Entra *app roles* (the `roles` claim of the token). They are mirrored as Django groups
  and decide the user's access (see [Roles and access](#roles-and-access)).
- **API clients** can send an Entra access token instead of a session cookie.
- **Logout.** A `POST` to `/oidc/logout/` (with the CSRF token) ends the Django session and the Entra session (a `GET`, from a link or a bookmark, shows a logout button).

The CloudHarness gatekeeper is not used (`harness.secured: false`): gogatekeeper only supports Keycloak as
identity provider and does not read the Entra `roles` claim. All the paths are protected by Django instead.

The code lives in the vendored libraries:

| Library | Content |
|---|---|
| [libraries/cloudharness-common](libraries/cloudharness-common) | `cloudharness.auth.entra`: configuration, token validation |
| [libraries/cloudharness-django](libraries/cloudharness-django) | Django settings, `/oidc/` views, authentication backend, middlewares, user sync, admin |
| [libraries/models](libraries/models) | CloudHarness configuration model |

## Configure authentication

### 1. Register the application in Entra

In the [Microsoft Entra admin center](https://entra.microsoft.com):

1. **App registrations → New registration**
   - *Supported account types*: **Accounts in this organizational directory only** (single tenant).
   - *Redirect URI*: platform **Web**, `https://<subdomain>.<domain>/oidc/callback/`.
     Entra accepts plain `http://` redirect URIs only for `localhost`.
2. **Authentication**: add the other redirect URIs you need:
   - `http://localhost:8000/oidc/callback/` for local development;
   - the application root `https://<subdomain>.<domain>/`, so that Entra returns to the application after logout.
3. **Certificates & secrets → New client secret.** Copy the **value**: it is shown only once.
4. **App roles → Create app role**, once per role, with *Allowed member types* **Users/Groups**.
   The **Value** must match the role names in the settings
   ([backend/django_baseapp/settings.py](backend/django_baseapp/settings.py)):

   | Display name | Value |
   |---|---|
   | Administrator | `__APP_NAME__-administrator` |
   | User | `__APP_NAME__-user` |

5. To call the API with bearer tokens: **Expose an API → Application ID URI**
   (the default `api://<client id>` is an accepted audience) and **Add a scope** (e.g. `access`).
   The application only accepts delegated access tokens for this scope (see
   [Calling the API with a bearer token](#calling-the-api-with-a-bearer-token)).
   Clients then request `api://<client id>/access` to get a token for this application.
6. Optional: **Token configuration → Add optional claim** `email`, `given_name`, `family_name`
   (token type *ID*, and *Access* if the API is used with bearer tokens).
   Without them, the names are taken from the display name (`name`) and the email from the username.

From the **Overview** page, note the **Directory (tenant) ID** and the **Application (client) ID**.

### 2. Configure the deployment

The non-secret values go in the `entra` section of [deploy/values.yaml](deploy/values.yaml):

```yaml
harness:
  secured: false                # no gatekeeper: the application authenticates its users
  secrets:
    entra-client-secret: ""     # set at deploy time, never committed
    django-secret-key: ""       # generated by CloudHarness at the first deployment

entra:
  tenant_id: "<directory (tenant) id>"
  client_id: "<application (client) id>"
  api_audience: ""              # extra accepted access token audience, defaults to api://<client_id>
  authority_host: https://login.microsoftonline.com   # change only for national clouds
```

The client secret is an application secret, mounted in the container and read at runtime.
Do not write it in `values.yaml`. Provide it at deploy time instead:

```bash
harness-deployment ... # as usual
helm upgrade --install ... --set apps.__APP_NAME__.harness.secrets.entra-client-secret=<secret>
```

You can also have the CI/CD pipeline set it, or use a secret manager. Declare the secrets as `""`, not
null: Helm drops null values, and the secret would not be created or would lose the value set at deploy time.

The Django `SECRET_KEY` comes from the `django-secret-key` application secret, which CloudHarness generates
once with a random value and keeps across deployments (or `DJANGO_SECRET_KEY`). Without one, the application
refuses to start unless `DEBUG` is on, in which case it uses a development key.

In a deployment, `ALLOWED_HOSTS` is set to the application host names (`<subdomain>.<domain>`, the aliases and
the in-cluster service names) and the pod IP of the Kubernetes probes (the `POD_IP` variable in `harness.env`).
Requests with any other `Host` or `X-Forwarded-Host` get a 400. Add other host names to `ALLOWED_HOSTS` in
`settings.py`. When the deployment is served on https, the session and CSRF cookies are `Secure`; the
https redirect and HSTS are left to the ingress.

Each value can be overridden by an environment variable, which takes precedence over `values.yaml`
and the secret. This is how the application is configured outside a deployment:

| Environment variable | values.yaml / secret |
|---|---|
| `ENTRA_TENANT_ID` | `entra.tenant_id` |
| `ENTRA_CLIENT_ID` | `entra.client_id` |
| `ENTRA_CLIENT_SECRET` | secret `entra-client-secret` |
| `ENTRA_API_AUDIENCE` | `entra.api_audience` |
| `ENTRA_AUTHORITY_HOST` | `entra.authority_host` |

Behind the CloudHarness ingress the application trusts the `X-Forwarded-Host` and `X-Forwarded-Proto`
headers, so that the redirect URI it sends to Entra is the public `https://` address. That address
must match the one registered in step 1.

### 3. Assign users

In **Enterprise applications → __APP_NAME__ → Users and groups → Add user/group**, select the users
(or groups, which requires Entra ID P1/P2) and the role.

Optionally, set **Properties → Assignment required? = Yes** in the same enterprise application, so that
users without a role assignment cannot sign in at all. Otherwise they can sign in, but the application
answers 403.

Role changes take effect at the user's next login. Removing a role does not end the sessions that are
already open, which last up to `SESSION_COOKIE_AGE` (1 hour by default).

To lock a user out of the application only, a superuser can uncheck *Active* on the user in the Django admin
(the only user field editable there unless `USER_CHANGE_ENABLED`). The Entra login does not reactivate the user.
Disabling the account in Entra, or removing its role assignment, locks it out everywhere.

### Roles and access

| App role | Main UI and API | Django admin (`/admin/`) |
|---|---|---|
| `__APP_NAME__-user` | ✓ | ✗ |
| `__APP_NAME__-administrator` | ✓ | ✓ as superuser |
| no role | 403 | ✗ |

At every login:

- Users with the administrator role become Django `is_superuser` and `is_staff`; everybody else loses both.
  Editing these flags in the admin has no lasting effect, because Entra sets them again at the next login.
- The configured roles the user has are mirrored as Django groups with the same name. Groups that are
  not app roles are left untouched, so the application can manage its own groups.
- Roles that are not in `AUTH_ALL_ROLES` are ignored.

The roles are configured in [backend/django_baseapp/settings.py](backend/django_baseapp/settings.py):

```python
AUTH_CLIENT_NAME = PROJECT_NAME.lower().replace("_", "-")   # "__APP_NAME__"

AUTH_ADMIN_ROLE = f"{AUTH_CLIENT_NAME}-administrator"  # application and Django admin (superuser)
AUTH_USER_ROLE = f"{AUTH_CLIENT_NAME}-user"            # application only
AUTH_ALL_ROLES = [AUTH_ADMIN_ROLE, AUTH_USER_ROLE]
```

To add an application role (e.g. `__APP_NAME__-editor`), create it in the app registration, add it to
`AUTH_ALL_ROLES` and check it in your code (see below). Only `AUTH_ADMIN_ROLE` grants Django admin access.

The Django admin login (`/admin/login/`) goes through Entra too: an administrator is sent back to the
admin, a logged-in user without the administrator role gets a 403. Local Django accounts
(`python manage.py createsuperuser`) can log in with a password only when `PASSWORD_LOGIN_ENABLED` is on,
by default only with `DEBUG` (local development): they bypass Entra MFA and conditional access.
Enable it in a deployment only for a break-glass account, and turn it off afterwards.

### Protecting views and API endpoints

`LoginRequiredMiddleware` protects every path. A request is allowed when it comes from a logged-in user
who has at least one role in `AUTH_ALL_ROLES` (or is a superuser). Otherwise:

- an anonymous browser navigation (`GET`, `Accept: text/html`) is redirected to the Entra login;
- any other anonymous request gets `401 {"message": "Unauthorized"}`;
- a logged-in user without a role gets `403`.

The paths in `AUTH_EXEMPT_URLS` are reachable without login. The default list is:

```python
AUTH_EXEMPT_URLS = [
    r"^/api/live$",
    r"^/api/ready$",
    r"^/oidc/",
    r"^/admin/login/",
    r"^/static/(?!www/)",   # admin assets; the frontend build (/static/www/) stays protected
]
```

Only canonical paths can be exempt: a path such as `/static//www/` or `/static/./www/`, which Django would
serve as `/static/www/`, requires a login.

To make more paths public, override the list in `settings.py`, keeping the default entries. To protect
each view yourself instead, set `AUTH_REQUIRED = False`.

In the API ([backend/__APP_MODULE__/api/__init__.py](backend/__APP_MODULE__/api/__init__.py)), `user_auth`
accepts either an Entra bearer token or the login session. With the session, Django-Ninja checks the
CSRF token on unsafe methods. Use `user_auth` so that the endpoint is documented as authenticated in
the OpenAPI schema:

```python
from cloudharness_django.services import get_auth_service

@api.get('/me', response={200: UserSchema}, auth=user_auth, tags=['auth'])
def me(request):
    ...

@api.get('/reports', auth=user_auth)
def reports(request):
    # role based check on the app roles of the user (request.user.is_superuser for the administrators)
    if "__APP_NAME__-editor" not in get_auth_service().get_user_roles(request.user):
        raise Http403()
    ...
```

`GET /api/me` returns the current user, with `roles` and `is_admin`. The frontend uses it in
[frontend/src/components/CurrentUser.tsx](frontend/src/components/CurrentUser.tsx) to show the user and
the logout link, and to redirect to `/oidc/login/` on 401.

### Calling the API with a bearer token

A client can call the API with an Entra **delegated access token** issued for this application, i.e. a
token obtained for a user with the scope `api://<client id>/access`. The token must:

- be issued by the configured tenant;
- have the audience `api://<client id>`, `entra.api_audience` or the client id;
- have the `scp` claim: ID tokens (which have the client id as audience too) and application tokens
  (client credentials) are rejected;
- carry the `roles` claim of the user.

```bash
curl -H "Authorization: Bearer $TOKEN" https://<subdomain>.<domain>/api/me
```

Bearer users are synced like browser users. The result is cached per user for
`BEARER_TOKEN_USER_CACHE_TTL` seconds, as long as the token has the same roles and names (a token with other
roles syncs the user again). An invalid or expired token makes the request anonymous (401).

### Settings reference

Django settings, set in [backend/django_baseapp/settings.py](backend/django_baseapp/settings.py):

| Setting | Default | Description |
|---|---|---|
| `AUTH_ADMIN_ROLE` | `<app>-administrator` | App role that makes a user a Django superuser. Required. |
| `AUTH_ALL_ROLES` | admin + user role | App roles that give access to the application, mirrored as Django groups. |
| `AUTH_REQUIRED` | `True` | Require a logged-in user with an app role on every path. |
| `AUTH_EXEMPT_URLS` | probes, `/oidc/`, `/admin/login/`, `/static/` except `/static/www/` | Regular expressions of the public paths. |
| `BEARER_TOKEN_USER_CACHE_TTL` | `60` | Seconds a bearer token user is cached. |
| `SESSION_COOKIE_AGE` | `3600` | Lifetime of the login session, in seconds. |
| `USER_CHANGE_ENABLED` | `False` | Allow editing users and groups in the Django admin (always allowed with `DEBUG`). |
| `PASSWORD_LOGIN_ENABLED` | `DEBUG` | Password login of local Django users at `/admin/login/`, bypassing Entra. |
| `LOGIN_REDIRECT_URL` | `/` | Where to go after login without a `next` page, and after logout. |

URLs:

| URL | |
|---|---|
| `/oidc/login/?next=<path>` | Starts the login and returns to `<path>`. Only local paths are accepted. |
| `/oidc/callback/` | Redirect URI of the app registration. |
| `/oidc/logout/` | `POST` with the CSRF token: logs out of the application and of Entra. The frontend sets the `csrftoken` cookie. A `GET` (a link or a bookmark) shows a logout button. |
| `/admin/` | Django admin, for administrators. |

## Using the template for a new application

Create the application from the CloudHarness `__APP_NAME__` template (from the root of a CloudHarness project):

```bash
harness-application my-app -t __APP_NAME__
```

It creates `applications/my-app` with the backend module `my_app`, the app roles `my-app-administrator` and
`my-app-user`, and generates the TypeScript API client of the frontend (requires Java, as the other
CloudHarness templates). The template is self-contained: do not add the `base`, `webapp` or `django-*`
templates. Then:

1. Register a new Entra application with those role names (see [step 1](#1-register-the-application-in-entra)).
2. Fill the `entra` section in `deploy/values.yaml` and provide the `entra-client-secret` at deploy time.
3. Run `harness-deployment` so that the generated deployment files (helm, skaffold, Tilt) include the application.

## Local development

### Install the Python dependencies

```bash
cd applications/__APP_NAME__
source dev-setup.sh       # -p to install pytest as well
```

### Configure Entra

Copy [.env.example](.env.example) to `.env` (git-ignored) and fill in the tenant id, client id and client
secret. The app registration must have the redirect URI `http://localhost:8000/oidc/callback/`.

### Prepare the backend

```bash
cd backend
python3 manage.py migrate
python3 manage.py collectstatic --noinput
python3 manage.py createsuperuser   # optional: a local admin account (DEBUG only), see Roles and access
# link the frontend build into the static folder, only needed once
cd static/www && ln -s ../../../frontend/dist dist
```

Without a CloudHarness deployment the backend uses a local SQLite database. To use the deployment
database instead:

1. Run `harness-deployment ... -n [NAMESPACE] -i __APP_NAME__`, then `port-forward.sh [NAMESPACE]`.
2. Map `127.0.0.1 __APP_NAME__-db` in the hosts file.
3. Set `CH_VALUES_PATH` to the generated `deployment/helm/values.yaml`.

### Run the backend

```bash
cd backend
set -a; source ../.env; set +a
CH_CURRENT_APP_NAME=__APP_NAME__ DJANGO_SETTINGS_MODULE=django_baseapp.settings \
  uvicorn --host 0.0.0.0 --port 8000 django_baseapp.asgi:application
```

Open http://localhost:8000: you are redirected to the Entra login.

The VS Code launch configuration reads the same `.env` file.

### Run the frontend

The frontend is in [frontend](frontend) (see [frontend/README.md](frontend/README.md)). The Vite dev server
proxies `/api/` and `/oidc/` to the backend, so the login works from the dev server as well.

- `yarn dev`: local development without a backend.
- `yarn start`: local development with the backend on localhost:5000.
- `yarn start:dev`: local development with the backend on the remote dev deployment.
- `yarn start:local`: local development with the backend on the local dev deployment.

To regenerate the API client stubs: `harness-generate clients __APP_NAME__ -t`.

## Tests

```bash
cd backend && python manage.py test cloudharness_django __APP_MODULE__
cd libraries/cloudharness-common && pytest tests
```

### API tests with test tokens

API tests cannot sign in to Entra interactively. Instead, the test deployment also accepts *test tokens*:
tokens with the same claims as Entra tokens (issuer, audience, tenant, roles) but signed with a local test key
(header `kid: cloudharness-test`). Only deployments built with the test values
(`harness-deployment ... -e test`, see [deploy/values-test.yaml](deploy/values-test.yaml)) accept them:

```yaml
harness:
  secrets:
    entra-test-public-key:   # PEM public key, set at deploy time
entra:
  test_tokens: true          # test deployments only, never in production
```

1. Generate a key pair: `python test/api/entra_token.py keygen`.
2. Set the public key as the `entra-test-public-key` secret of the test deployment
   (`--set apps.__APP_NAME__.harness.secrets.entra-test-public-key=...`).
3. Run [test/api](test/api) with the private key in `ENTRA_TEST_PRIVATE_KEY`.
   The tenant and client ids are read from `deploy/values.yaml` (or `ENTRA_TENANT_ID` / `ENTRA_CLIENT_ID`).

The test tokens are still checked for expiry, issuer, audience and tenant. When `test_tokens` is enabled,
the application logs a warning when it loads the Entra configuration. The CloudHarness schemathesis autotest is disabled in the test
values, because it can only authenticate through Keycloak. [test/api/test_st.py](test/api/test_st.py) runs
the schemathesis checks with test tokens instead.

### End to end tests with test tokens

[test/e2e/landing.spec.ts](test/e2e/landing.spec.ts) runs in the CloudHarness Puppeteer runner against a
test deployment, like the API tests. The browser sends a test token in the `Authorization` header of every
request to the application (never to other origins), so it is logged in without the Entra sign-in page.
It checks that:

- a user with the `__APP_NAME__-user` role sees the landing page and their user (from `/api/me`), with no
  console errors and no failed requests;
- a user without an app role gets a 403;
- an anonymous user is redirected to `/oidc/login/`.

The test values enable the e2e tests and disable the common CloudHarness smoke test, which cannot log in
(`harness.test.e2e.smoketest: false`): the spec does the same checks while logged in.

The tests need `ENTRA_TEST_PRIVATE_KEY`, `ENTRA_TENANT_ID` and `ENTRA_CLIENT_ID` in their environment.
Locally, `harness-test` passes the shell environment, and the ids can also be read from `deploy/values.yaml`.
In the CI pipeline only `test/e2e` is mounted in the test container: set the three variables in the pipeline.

To run them by hand with the CI image, against a test deployment:

```bash
docker build -t ch-test-e2e cloud-harness/test/test-e2e
docker run --rm -v $PWD/applications/__APP_NAME__/test/e2e:/home/test/__tests__/__APP_NAME__:ro \
  -e APP_URL=https://__APP_NAME__.<domain> -e SKIP_SMOKETEST=true \
  -e ENTRA_TENANT_ID=... -e ENTRA_CLIENT_ID=... -e ENTRA_TEST_PRIVATE_KEY="$(cat private.pem)" \
  ch-test-e2e yarn test
```

On minikube, add `--network minikube --add-host __APP_NAME__.<domain>:$(minikube ip)`.
