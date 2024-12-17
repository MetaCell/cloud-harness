
import jwt

from django.contrib.auth.models import User
from asgiref.sync import iscoroutinefunction
from django.utils.decorators import sync_and_async_middleware
from asgiref.sync import async_to_sync, iscoroutinefunction

from keycloak.exceptions import KeycloakGetError

from cloudharness.middleware import get_authentication_token
from cloudharness.auth.exceptions import InvalidToken
from cloudharness_django.services import get_user_service, get_auth_service
from cloudharness import log


async def _get_user():
    bearer = get_authentication_token()
    if bearer:
        # found bearer token get the Django user
        try:
            token = bearer.split(" ")[-1]
            payload = jwt.decode(token, algorithms=["RS256"], options={"verify_signature": False}, audience="web-client")
            kc_id = payload["sub"]
            try:
                user = await User.objects.aget(member__kc_id=kc_id)
            except User.DoesNotExist:
                user = await get_user_service().sync_kc_user(get_auth_service().get_auth_client().get_current_user())
            return user
        except KeycloakGetError:
            # KC user not found
            return None
        except InvalidToken:
            return None
        except Exception as e:
            log.exception("User mapping error, %s", payload["email"])
            return None

    return None


@sync_and_async_middleware
def BearerTokenMiddleware(get_response=None):
    # One-time configuration and initialization.
    if iscoroutinefunction(get_response):
        async def middleware(request):
            if (not request.path.startswith("/static")) and getattr(getattr(request, "user", {}), "is_anonymous", True):
                user = await _get_user()
                if user:
                    # auto login, set the user
                    request.user = user
                    request._cached_user = user

            response = await get_response(request)
            return response
    else:
        def middleware(request):
            if (not request.path.startswith("/static")) and getattr(getattr(request, "user", {}), "is_anonymous", True):
                user = async_to_sync(_get_user)()
                if user:
                    # auto login, set the user
                    request.user = user
                    request._cached_user = user

            return get_response(request)
    return middleware


class BearerTokenAuthentication:
    # for django rest framework usage
    def authenticate(self, request):
        user = getattr(request._request, 'user', None)
        if user and user.is_authenticated:
            return (user, None)
        return (_get_user(), None)
