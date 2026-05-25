# cloudharness-django

A Django library that integrates [CloudHarness](https://github.com/MetaCell/cloud-harness) infrastructure into Django applications. It handles Keycloak OIDC authentication, automatically synchronises Keycloak users/groups/organisations into Django's database, and listens to Kafka events to keep that data up to date in real time.

## Table of contents

- [How it works](#how-it-works)
- [Installation](#installation)
- [Configuration](#configuration)
- [Startup](#startup)
- [Models](#models)
- [Authentication](#authentication)
- [Services](#services)
- [Authorization levels](#authorization-levels)
- [Event-driven synchronisation](#event-driven-synchronisation)
- [Management commands](#management-commands)
- [Admin UI](#admin-ui)
- [Local development](#local-development)

---

## How it works

```
HTTP request
     │
     ▼
BearerTokenMiddleware
     │  extracts JWT from Authorization header or kc-access cookie
     │  decodes token → gets Keycloak user ID (sub)
     │  checks Django cache (TTL 60 s)
     │        hit  ──────────────────────────────────► request.user
     │        miss ──► _get_user()
     │                      │
     │                      ├─ User.objects.get(member__kc_id=…)
     │                      │       found  ─► sync_kc_user() (updates fields)
     │                      │       not found ─► sync_kc_user() (creates User + Member)
     │                      │
     │                      └─► SAFETY CHECK: User must always have a Member
     │                               ok  ─► cache user ─► request.user
     │                               fail ─► keep anonymous
     ▼
Django view / Django Ninja


Keycloak admin events (via Kafka)
     │
     ▼
KeycloakMessageService.event_handler()
     │
     ├─ USER          ─► invalidate_user_cache() + sync_kc_user()
     ├─ GROUP         ─► sync_kc_group()
     ├─ CLIENT_ROLE_MAPPING ─► sync_kc_user()
     ├─ GROUP_MEMBERSHIP    ─► sync_kc_user() (groups re-synced inside)
     └─ ORGANIZATION_MEMBERSHIP ─► sync_kc_user() (orgs re-synced inside)
```

Every authenticated request syncs the Keycloak user into the Django `User` table. A `Member` record (holding the Keycloak UUID `kc_id`) is always created alongside it. The middleware caches the resolved `User` object for 60 seconds to avoid a database round-trip on every request. Kafka events invalidate that cache and trigger a full re-sync when Keycloak data changes.

---

## Installation

```bash
pip install cloudharness-django
```

Add the library's settings module to the **top** of your `settings.py`:

```python
PROJECT_NAME = "my-app"   # must be set before the import

from cloudharness_django.settings import *  # noqa: F401, F403
```

This import:

- Appends `cloudharness_django`, `admin_extra_buttons`, and `django_prometheus` to `INSTALLED_APPS`.
- Inserts `BearerTokenMiddleware` (and Prometheus middleware) into `MIDDLEWARE`.
- Configures the `DATABASES` setting from the CloudHarness deployment values (PostgreSQL in Kubernetes, SQLite on a developer machine when no `allvalues.yaml` is found).
- Sets `CSRF_TRUSTED_ORIGINS` from the CloudHarness domain.
- Redirects `ROOT_URLCONF` through `cloudharness_django.urls` (which mounts Prometheus metrics and then delegates to your original URL config).

Run migrations once after installation:

```bash
python manage.py migrate
```

---

## Configuration

Add the following to your `settings.py` after importing the CloudHarness settings:

```python
# Keycloak client name (usually the application name in lower case)
KC_CLIENT_NAME = PROJECT_NAME.lower()

# Role names that exist (or will be created) in the Keycloak client
KC_ADMIN_ROLE      = f"{KC_CLIENT_NAME}-administrator"
KC_MANAGER_ROLE    = f"{KC_CLIENT_NAME}-manager"
KC_USER_ROLE       = f"{KC_CLIENT_NAME}-user"

KC_ALL_ROLES       = [KC_ADMIN_ROLE, KC_MANAGER_ROLE, KC_USER_ROLE]
KC_PRIVILEGED_ROLES = [KC_MANAGER_ROLE]

# Role automatically assigned to every new Keycloak user via the default realm role.
# Set to None to disable.
KC_DEFAULT_USER_ROLE = KC_USER_ROLE
```

### Optional settings

| Setting | Default | Description |
|---|---|---|
| `BEARER_TOKEN_USER_CACHE_TTL` | `60` | Seconds a resolved `User` object is cached in Django's cache backend. |
| `USER_CHANGE_ENABLED` | `False` | Allow editing users directly in the Django admin (bypasses Keycloak). |

---

## Startup

Call `init_services()` during application startup (e.g. in `apps.py` `ready()`):

```python
# apps.py
from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = "my_app"

    def ready(self):
        from cloudharness_django.services import init_services
        from cloudharness_django.services.events import init_listener_in_background

        # Initialise auth + user services (creates the Keycloak client and roles if absent)
        init_services()

        # Start the Kafka consumer in a background thread
        init_listener_in_background()
```

If Keycloak may not be reachable immediately (e.g. during container startup), use the background variant for services as well:

```python
from cloudharness_django.services import init_services_in_background
init_services_in_background()
```

Both background helpers retry with a 5-second interval until they succeed.

---

## Models

| Model | Purpose |
|---|---|
| `Member` | Links a Django `User` to its Keycloak UUID (`kc_id`). Always present; a `User` without a `Member` is treated as anonymous. |
| `Team` | Links a Django `Group` to a Keycloak group (`kc_id`). Tracks the group owner. |
| `Organization` | Mirrors a Keycloak organisation. Can be pre-created in Django (without `kc_id`) and will be matched by name when Keycloak syncs. |
| `OrganizationMember` | Many-to-many membership table between `User` and `Organization`. |

Extending `Organization` with application-specific fields:

```python
from cloudharness_django.models import Organization

class MyOrganization(models.Model):
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="my_org")
    logo = models.ImageField(upload_to="org_logos/", blank=True)
```

---

## Authentication

### Middleware: `BearerTokenMiddleware`

Activated automatically via the settings import. On every request it:

1. Reads the bearer token from the `Authorization` header or `kc-access` cookie.
2. Decodes and validates the JWT (via `cloudharness.auth.keycloak.AuthClient`).
3. Looks up the Django `User` by `member__kc_id`, creating it if absent.
4. Syncs user attributes and group memberships from Keycloak.
5. Caches the result and sets `request.user`.

If the token is invalid, the user is logged out and the `kc-access` cookie is deleted.

### Cache invalidation

When a user is deleted or deactivated in Keycloak the Kafka event handler calls `invalidate_user_cache()` to remove the stale cache entry before syncing. You can also call it directly:

```python
from cloudharness_django.middleware import invalidate_user_cache
invalidate_user_cache(kc_user_id)
```

---

## Services

Services are initialised per execution context (thread or coroutine) using `contextvars.ContextVar`. They are created lazily on first access.

```python
from cloudharness_django.services import get_auth_service, get_user_service

auth_service = get_auth_service()   # AuthService
user_service = get_user_service()   # UserService
```

### `AuthService`

| Method | Description |
|---|---|
| `get_auth_client()` | Returns the underlying `cloudharness.auth.AuthClient`. |
| `create_client()` | Creates the Keycloak client and its roles if they do not exist. |
| `get_auth_level(kc_user, kc_roles)` | Returns the `AuthorizationLevel` for the given user. |

### `UserService`

| Method | Description |
|---|---|
| `sync_kc_user(kc_user, delete=False)` | Create or update the Django `User` + `Member` for a Keycloak user. Atomic. |
| `sync_kc_user_groups(kc_user)` | Replace the user's Django groups with their current Keycloak groups. |
| `sync_kc_user_organizations(kc_user)` | Sync `OrganizationMember` rows for the user. |
| `sync_kc_group(kc_group)` | Create or update the Django `Group` + `Team` for a Keycloak group. |
| `sync_kc_groups()` | Sync all Keycloak groups. |
| `sync_kc_users_groups()` | Full sync: all users, their groups, and their memberships. |
| `create_team(group_name)` | Create a group in both Keycloak and Django. |
| `add_user_to_team(user, team_name)` | Add a user to a group in Keycloak (Django side follows via Kafka). |
| `rm_user_from_team(user, team_name)` | Remove a user from a group in Keycloak. |

Accessing the current user from within a view:

```python
from cloudharness_django.services import get_auth_service

auth_service = get_auth_service()
auth_client  = auth_service.get_auth_client()
kc_user      = auth_client.get_current_user()
auth_level   = auth_service.get_auth_level(kc_user)
```

---

## Authorization levels

`AuthorizationLevel` is an enum returned by `AuthService.get_auth_level()`:

| Level | Condition |
|---|---|
| `NO_AUTHORIZATION` | User has no client roles. |
| `NON_PRIVILEGED` | User has at least one role in `KC_ALL_ROLES`. |
| `PRIVILEGED` | User has at least one role in `KC_PRIVILEGED_ROLES`. |
| `ADMIN` | User has the `KC_ADMIN_ROLE`. Also sets `is_superuser` and `is_staff` on the Django `User`. |

```python
from cloudharness_django.services.auth import AuthorizationLevel

if auth_level == AuthorizationLevel.ADMIN:
    ...
```

---

## Event-driven synchronisation

`KeycloakMessageService` consumes the `keycloak.fct.admin` Kafka topic. On each Keycloak admin event it dispatches to the appropriate sync method:

| Keycloak event | Action |
|---|---|
| `USER` (any operation) | `invalidate_user_cache()` + `sync_kc_user()` |
| `USER` with `DELETE` | `sync_kc_user(delete=True)` — deactivates the Django user |
| `GROUP` | `sync_kc_group()` |
| `CLIENT_ROLE_MAPPING` | `sync_kc_user()` — re-evaluates superuser status |
| `GROUP_MEMBERSHIP` | `sync_kc_user()` — groups re-synced inside |
| `ORGANIZATION_MEMBERSHIP` | `sync_kc_user()` — organisations re-synced inside |

Use `init_listener_in_background()` (see [Startup](#startup)) to start the consumer. If Kafka is unavailable (e.g. on a developer machine without `allvalues.yaml`), the function exits silently.

---

## Management commands

Manually trigger a full sync of all Keycloak users and groups:

```bash
python manage.py cloudharness sync
```

Useful after bulk changes in Keycloak or to bootstrap a fresh database.

---

## Admin UI

The Django admin provides:

- **User list** with a "Sync from Keycloak" button per user.
- **Group list** with team management.
- **Organization list** with member overview.

Direct user editing in the admin is disabled by default (`USER_CHANGE_ENABLED = False`). To allow it (e.g. in a development environment):

```python
# settings.py
USER_CHANGE_ENABLED = True
```

---

## Local development

Without a running Kubernetes cluster, `cloudharness_django.settings` falls back to SQLite and logs a warning. You still need a reachable Keycloak instance. To test Kafka event handling locally, copy your deployment's `allvalues.yaml` to the path referenced by `ALLVALUES_PATH` and ensure Kafka is accessible.

Environment variables used by the library:

| Variable | Description |
|---|---|
| `ACCOUNTS_ADMIN_USERNAME` | Keycloak admin username for the `AuthClient`. |
| `ACCOUNTS_ADMIN_PASSWORD` | Keycloak admin password for the `AuthClient`. |
