from enum import Enum
from typing import Iterable, List

from django.contrib.auth.models import User

from cloudharness_django.exceptions import NoAdminRole


class AuthorizationLevel(Enum):
    NO_AUTHORIZATION = 1
    USER = 2
    ADMIN = 3


class AuthService:
    """
    Maps the Entra app roles of a user (the `roles` token claim) to an authorization level.

    The app roles are defined in the Entra app registration and must match the role
    names configured in the Django settings (AUTH_ADMIN_ROLE, AUTH_ALL_ROLES).
    """

    def __init__(
        self,
        client_roles: List[str],
        admin_role: str,
    ):
        if not admin_role:
            raise NoAdminRole("No admin role given.")
        self.client_roles = list(client_roles)
        self.admin_role = admin_role

    def get_admin_role(self):
        return self.admin_role

    def get_auth_level(self, roles: Iterable[str]) -> AuthorizationLevel:
        assigned_roles = set(roles or [])

        if self.admin_role in assigned_roles:
            return AuthorizationLevel.ADMIN
        if assigned_roles.intersection(self.client_roles):
            return AuthorizationLevel.USER
        return AuthorizationLevel.NO_AUTHORIZATION

    def get_user_roles(self, user: User) -> List[str]:
        """The app roles of a user, as synced to Django groups at login."""
        return list(user.groups.filter(name__in=self.client_roles).values_list("name", flat=True))

    def has_access(self, user: User) -> bool:
        """True if the user may use the application: superusers and users with any app role."""
        if not user.is_authenticated or not user.is_active:
            return False
        if user.is_superuser or not self.client_roles:
            return True
        return user.groups.filter(name__in=self.client_roles).exists()
