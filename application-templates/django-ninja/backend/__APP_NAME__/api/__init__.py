import time
from django.http import HttpRequest
from ninja import NinjaAPI
from ..exceptions import Http401, Http403


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
