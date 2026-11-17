from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User

from cloudharness.auth.entra import EntraIdentity, get_entra_config
from cloudharness.auth.exceptions import InvalidToken

from cloudharness_django.services import get_user_service


class EntraBackend(BaseBackend):
    """
    Authenticates a user from the claims of an already validated Entra token,
    creating or updating the Django user just in time.
    """

    def authenticate(self, request, entra_claims: dict = None, **kwargs):
        if not entra_claims:
            return None
        if entra_claims.get("tid") != get_entra_config().tenant_id:
            return None
        try:
            identity = EntraIdentity.from_claims(entra_claims)
        except InvalidToken:
            return None
        return get_user_service().sync_user(identity)

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if user.is_active else None
