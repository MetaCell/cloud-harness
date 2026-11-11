import asyncio

from cloudharness.middleware import bearer_token, get_authentication_token, set_authentication_token
from cloudharness.middleware.asgi import AuthMiddleware

TEST_TOKEN = "header.payload.signature"


def test_setting_and_getting_auth_token():
    set_authentication_token(TEST_TOKEN)
    assert get_authentication_token() == TEST_TOKEN


def test_setting_empty_token_resets():
    set_authentication_token(TEST_TOKEN)
    set_authentication_token(None)
    assert get_authentication_token() is None


def test_bearer_token():
    assert bearer_token(f"Bearer {TEST_TOKEN}") == TEST_TOKEN
    assert bearer_token(f"bearer {TEST_TOKEN}") == TEST_TOKEN
    assert bearer_token("Bearer undefined") is None
    assert bearer_token(f"Basic {TEST_TOKEN}") is None
    assert bearer_token("") is None
    assert bearer_token(None) is None


def test_asgi_middleware_sets_token():
    seen = {}

    async def app(scope, receive, send):
        seen["token"] = get_authentication_token()

    scope = {"type": "http", "headers": [(b"authorization", f"Bearer {TEST_TOKEN}".encode())]}
    asyncio.run(AuthMiddleware(app)(scope, None, None))
    assert seen["token"] == TEST_TOKEN
