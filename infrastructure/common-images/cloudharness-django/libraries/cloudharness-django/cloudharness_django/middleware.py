
import jwt

from django.contrib.auth.models import User
from django.contrib.auth import logout
from keycloak.exceptions import KeycloakGetError

from cloudharness.auth.exceptions import InvalidToken
from cloudharness_django.services import get_user_service
from cloudharness import log
from cloudharness.auth.keycloak import get_current_user_id, User as KcUser


def _get_user(kc_user_id: str) -> User:

    if kc_user_id is None:
        return None
        # found bearer token get the Django user
    try:
        try:
            user = User.objects.get(member__kc_id=kc_user_id)
        except User.DoesNotExist:
            user_svc = get_user_service()
            kc_user = user_svc.get_auth_client().get_current_user()
            user = user_svc.sync_kc_user(kc_user)
            user_svc.sync_kc_user_groups(kc_user)
        return user
    except KeycloakGetError:
        # KC user not found
        return None
    except InvalidToken:
        return None
    except Exception as e:
        log.exception("User mapping error, %s", kc_user.email)
        return None


class BearerTokenMiddleware:
    def __init__(self, get_response=None):
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, "user", None)
        kc_user = get_current_user_id()
        if kc_user:
            if not user or user.is_anonymous or user.member.kc_id != kc_user.id:
                user = _get_user(kc_user)
                if user:
                    # auto login, set the user
                    request.user = user
                    request._cached_user = user
        else:
            logout(request)

        return self.get_response(request)


class BearerTokenAuthentication:
    # for django rest framework usage
    def authenticate(self, request):
        kc_user = get_current_user_id()
        if not kc_user:
            return None
        user: User = getattr(request._request, 'user', None)
        if user and user.is_authenticated:
            return (user, None)
        return (_get_user(kc_user), None)
