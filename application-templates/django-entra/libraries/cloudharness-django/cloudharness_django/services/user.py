from django.contrib.auth.models import Group, User
from django.db import IntegrityError, transaction

from cloudharness import log
from cloudharness.auth.entra import EntraIdentity

from cloudharness_django.models import Member
from cloudharness_django.services.auth import AuthService, AuthorizationLevel


def get_user_by_oid(oid) -> User:
    try:
        return Member.objects.using("default").select_related("user").get(oid=oid).user
    except Member.DoesNotExist:
        return None


class UserService:
    """
    Just-in-time provisioning of Django users from Entra identities.

    Users are created or updated from the token claims every time they log in
    (or, for bearer tokens, when the cached user expires). The Entra app roles
    are mirrored as Django groups and drive the superuser/staff flags.
    """

    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def sync_user(self, identity: EntraIdentity) -> User:
        try:
            return self._sync_user(identity)
        except IntegrityError:
            # concurrent first login of the same user: the other request created it
            log.warning("Concurrent creation of the user %s, retrying", identity.oid)
            return self._sync_user(identity)

    @transaction.atomic
    def _sync_user(self, identity: EntraIdentity) -> User:
        user = get_user_by_oid(identity.oid)
        if user is None:
            user = User(username=self._free_username(identity))
            user.set_unusable_password()
            user.save()
            Member.objects.create(user=user, oid=identity.oid)
        elif user.username != identity.username and not self._username_taken(identity.username, user):
            user.username = identity.username

        self._map_identity(user, identity)
        user.save()
        self._sync_role_groups(user, identity.roles)
        return user

    def _map_identity(self, user: User, identity: EntraIdentity):
        # only admins can access the Django admin site, as superusers
        is_admin = self.auth_service.get_auth_level(identity.roles) == AuthorizationLevel.ADMIN
        user.is_superuser = is_admin
        user.is_staff = is_admin
        user.first_name = identity.first_name
        user.last_name = identity.last_name
        user.email = identity.email
        # is_active is not synced: a user deactivated in Django stays deactivated
        # (new users are active by default)

    def _sync_role_groups(self, user: User, roles):
        """Mirror the app roles as Django groups, leaving any other group untouched."""
        app_roles = set(self.auth_service.client_roles)
        current = set(roles or []) & app_roles
        user.groups.remove(*user.groups.filter(name__in=app_roles - current))
        user.groups.add(*[Group.objects.get_or_create(name=role)[0] for role in current])

    @staticmethod
    def _username_taken(username, user: User = None) -> bool:
        users = User.objects.using("default").filter(username=username)
        if user is not None:
            users = users.exclude(pk=user.pk)
        return users.exists()

    def _free_username(self, identity: EntraIdentity) -> str:
        # never adopt an existing (e.g. local) account with the same username
        if not self._username_taken(identity.username):
            return identity.username
        return f"{identity.username}-{identity.oid[:8]}"
