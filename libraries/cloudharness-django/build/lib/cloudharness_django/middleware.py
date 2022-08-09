import jwt

from django.contrib.auth.models import User

from keycloak.exceptions import KeycloakGetError

from cloudharness.middleware import get_authentication_token
from cloudharness_django.services import get_user_service, get_auth_service


def _get_user():
    bearer = get_authentication_token()
    if bearer:
        # found bearer token get the Django user
        try:
            token = bearer.split(" ")[1]
            payload = jwt.decode(token, algorithms=["RS256"], options={"verify_signature": False}, audience="web-client")
            kc_id = payload["sub"]
            try:
                user = User.objects.get(member__kc_id=kc_id)
            except User.DoesNotExist:
                user = get_user_service().sync_kc_user(get_auth_service().get_auth_client().get_current_user())
            return user
        except KeycloakGetError:
            # KC user not found
            return None
    return None


class BearerTokenMiddleware:
    def __init__(self, get_response = None):
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request):
        if getattr(getattr(request, "user", {}), "is_anonymous", True):
            user = _get_user()
            if user:
                # auto login, set the user
                request.user = user
                request._cached_user = user

        return self.get_response(request)


class BearerTokenAuthentication:
    def authenticate(self, request):
        user = getattr(request._request, 'user', None)
        if user and user.is_authenticated:
            return (user, None)
        return (_get_user(), None)
