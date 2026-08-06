import threading
import time
from contextvars import ContextVar
from typing import List, Optional

from django.conf import settings
from .auth import AuthService
from .user import UserService
from cloudharness_django.exceptions import \
    KeycloakOIDCAuthServiceNotInitError, \
    KeycloakOIDUserServiceNotInitError

# Per-context (per-thread / per-coroutine) service references.
# Each execution context lazy-initialises its own instances on first access,
# so no locking is required.
_auth_service: ContextVar[Optional[AuthService]] = ContextVar('cloudharness_auth_service', default=None)
_user_service: ContextVar[Optional[UserService]] = ContextVar('cloudharness_user_service', default=None)


def get_auth_service() -> AuthService:
    svc = _auth_service.get()
    if svc is None:
        init_services()
        svc = _auth_service.get()
    return svc


def get_user_service() -> UserService:
    svc = _user_service.get()
    if svc is None:
        init_services()
        svc = _user_service.get()
    return svc


def init_services(
        client_name: str = settings.KC_CLIENT_NAME,
        client_roles: List[str] = settings.KC_ALL_ROLES,
        privileged_roles: List[str] = settings.KC_PRIVILEGED_ROLES,
        admin_role: str = settings.KC_ADMIN_ROLE,
        default_user_role: str = settings.KC_DEFAULT_USER_ROLE
):
    auth_svc = AuthService(
        client_name=client_name,
        client_roles=client_roles,
        default_user_role=default_user_role,
        privileged_roles=privileged_roles,
        admin_role=admin_role)
    _auth_service.set(auth_svc)
    _user_service.set(UserService(auth_svc))
    return auth_svc


def init_services_in_background(
        client_name: str = settings.KC_CLIENT_NAME,
        client_roles: List[str] = settings.KC_ALL_ROLES,
        privileged_roles: List[str] = settings.KC_PRIVILEGED_ROLES,
        admin_role: str = settings.KC_ADMIN_ROLE,
        default_user_role: str = settings.KC_DEFAULT_USER_ROLE
):
    from cloudharness import log

    def background_operation():
        services_initialized = False

        while not services_initialized:
            try:
                init_services(client_name, client_roles, privileged_roles, admin_role, default_user_role)
                services_initialized = True
            except Exception:
                log.exception("Error initializing services. Retrying in 5 seconds...")
                time.sleep(5)

    threading.Thread(target=background_operation, daemon=True).start()
