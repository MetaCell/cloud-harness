from typing import Optional

from django.conf import settings

from .auth import AuthService, AuthorizationLevel
from .user import UserService

_auth_service: Optional[AuthService] = None
_user_service: Optional[UserService] = None


def init_services(
        client_roles=None,
        admin_role=None,
) -> AuthService:
    """Create the services from the AUTH_* role settings, or from the given roles."""
    global _auth_service, _user_service
    _auth_service = AuthService(
        client_roles=client_roles if client_roles is not None else settings.AUTH_ALL_ROLES,
        admin_role=admin_role or settings.AUTH_ADMIN_ROLE,
    )
    _user_service = UserService(_auth_service)
    return _auth_service


def get_auth_service() -> AuthService:
    if _auth_service is None:
        init_services()
    return _auth_service


def get_user_service() -> UserService:
    if _user_service is None:
        init_services()
    return _user_service
