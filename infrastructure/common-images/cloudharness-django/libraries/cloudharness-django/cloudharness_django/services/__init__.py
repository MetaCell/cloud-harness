from typing import List

from django.conf import settings
from .auth import AuthService
from .user import UserService
from cloudharness_django.exceptions import \
    KeycloakOIDCAuthServiceNotInitError, \
    KeycloakOIDUserServiceNotInitError, \
    KeycloakOIDUserServiceNotInitError

_auth_service = None
_user_service = None


def get_auth_service() -> AuthService:
    global _auth_service
    if not _auth_service:
        init_services()
    return _auth_service


def get_user_service() -> UserService:
    global _user_service
    if not _user_service:
        init_services()
    return _user_service


def init_services(
        client_name: str = settings.KC_CLIENT_NAME,
        client_roles: List[str] = settings.KC_ALL_ROLES,
        privileged_roles: List[str] = settings.KC_PRIVILEGED_ROLES,
        admin_role: str = settings.KC_ADMIN_ROLE,
        default_user_role: str = settings.KC_DEFAULT_USER_ROLE
):

    global _auth_service, _user_service
    _auth_service = AuthService(
        client_name=client_name,
        client_roles=client_roles,
        default_user_role=default_user_role,
        privileged_roles=privileged_roles,
        admin_role=admin_role)
    _user_service = UserService(_auth_service)
    return _auth_service


def init_services_in_background(
        client_name: str = settings.KC_CLIENT_NAME,
        client_roles: List[str] = settings.KC_ALL_ROLES,
        privileged_roles: List[str] = settings.KC_PRIVILEGED_ROLES,
        admin_role: str = settings.KC_ADMIN_ROLE,
        default_user_role: str = settings.KC_DEFAULT_USER_ROLE
):
    import threading
    import time
    from cloudharness import log

    def background_operation():
        services_initialized = False

        while not services_initialized:
            try:
                init_services(client_name, client_roles, privileged_roles, admin_role, default_user_role)
                services_initialized = True
            except:
                log.exception("Error initializing services. Retrying in 5 seconds...")
                time.sleep(5)

    threading.Thread(target=background_operation).start()
