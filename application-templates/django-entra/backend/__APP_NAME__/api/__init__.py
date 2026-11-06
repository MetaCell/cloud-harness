import time
from django.http import HttpRequest
from ninja import NinjaAPI
from ninja.security import HttpBearer, SessionAuth
from cloudharness_django.services import get_auth_service
from ..exceptions import Http401, Http403
from ..schema import UserSchema


class EntraBearer(HttpBearer):
    """Entra access token, already validated by cloudharness_django.middleware.BearerTokenMiddleware."""

    def authenticate(self, request, token):
        return request.user if request.user.is_authenticated else None


# the Entra bearer token or the Entra login session (CSRF is checked for the session only)
user_auth = [EntraBearer(), SessionAuth()]

api = NinjaAPI(title='__APP_NAME__ API', version='0.1.0')


@api.exception_handler(Http401)
def unauthorized(request, exc):
    return api.create_response(
        request,
        {'message': 'Unauthorized'},
        status=401,
    )


@api.exception_handler(Http403)
def forbidden(request, exc):
    return api.create_response(
        request,
        {'message': 'Forbidden'},
        status=403,
    )


@api.get('/ping', response={200: float}, tags=['test'])
def ping(request: HttpRequest):
    return time.time()


@api.get('/live', response={200: str}, tags=['test'])
def live(request: HttpRequest):
    return 'OK'


@api.get('/ready', response={200: str}, tags=['test'])
def ready(request: HttpRequest):
    return 'OK'


@api.get('/me', response={200: UserSchema}, auth=user_auth, tags=['auth'])
def me(request: HttpRequest):
    user = request.user
    return {
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'roles': get_auth_service().get_user_roles(user),
        'is_admin': user.is_superuser,
    }
