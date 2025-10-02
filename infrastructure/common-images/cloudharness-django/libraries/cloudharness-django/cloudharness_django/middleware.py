
import jwt

from django.contrib.auth.models import User
from django.contrib.auth import logout
from keycloak.exceptions import KeycloakGetError

from cloudharness.auth.exceptions import InvalidToken
from cloudharness_django.services import get_user_service
from .models import Member
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
            kc_user = user_svc.auth_client.get_current_user()
            try:
                user = user_svc.sync_kc_user(kc_user)
                user_svc.sync_kc_user_groups(kc_user)
            except Exception as e:
                log.exception("User sync error, %s", kc_user.email)
                return None
        except User.MultipleObjectsReturned:
            # Race condition, multiple users created for the same kc_id
            log.warning("Multiple users found for kc_id %s, cleaning up...", kc_user_id)
            user = User.objects.filter(member__kc_id=kc_user_id).order_by('id').first()
            User.objects.filter(member__kc_id=kc_user_id).exclude(id=user.id).delete()
            return user
        return user
    except KeycloakGetError:
        # KC user not found
        return None
    except InvalidToken:
        return None
    except Exception as e:
        log.exception("User %s mapping error, %s", kc_user_id, e)
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
