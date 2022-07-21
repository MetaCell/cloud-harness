from typing import List

from django.conf import settings

from cloudharness_django.exceptions import \
    KeycloakOIDCAuthServiceNotInitError, \
    KeycloakOIDUserServiceNotInitError, \
    KeycloakOIDUserServiceNotInitError

_auth_service = None
_user_service = None

def get_auth_service():
    global _auth_service
    if not _auth_service:
        raise KeycloakOIDCAuthServiceNotInitError("Auth Service not initialized")
    return _auth_service

def get_user_service():
    global _user_service
    if not _user_service:
        raise KeycloakOIDUserServiceNotInitError("User Service not initialized")
    return _user_service

def init_services(
        client_name: str = settings.KC_CLIENT_NAME,
        client_roles: List[str] = settings.KC_ALL_ROLES,
        privileged_roles: List[str] = settings.KC_PRIVILEGED_ROLES,
        admin_role: str = settings.KC_ADMIN_ROLE,
        default_user_role: str = settings.KC_DEFAULT_USER_ROLE
        ):
    from cloudharness_django.services.auth import AuthService
    from cloudharness_django.services.user import UserService
    global _auth_service, _user_service
    _auth_service = AuthService(
        client_name=client_name,
        client_roles=client_roles,
        default_user_role=default_user_role,
        privileged_roles=privileged_roles,
        admin_role=admin_role)
    _user_service = UserService(_auth_service)
    return _auth_service
