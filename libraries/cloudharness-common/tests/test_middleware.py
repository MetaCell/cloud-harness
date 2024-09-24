
from unittest import mock

from cloudharness.auth.keycloak import AuthClient
from cloudharness.middleware import get_authentication_token, set_authentication_token

TEST_USER_ID = "1234567890"
TEST_AUTHENTICATION_TOKEN = f"Bearer {TEST_USER_ID}"


def new_init(self):
    pass


def new_decode_token(token):
    # if everything went fine then the token contains the value of sub
    # let's return it
    return {
        'sub': token
    }


def test_setting_and_getting_auth_token():
    set_authentication_token(TEST_AUTHENTICATION_TOKEN)
    assert get_authentication_token() == TEST_AUTHENTICATION_TOKEN


def test_decoding():
    mocker = AuthClient
    mocker.decode_token = new_decode_token
    mocker.__init__ = new_init

    set_authentication_token(TEST_AUTHENTICATION_TOKEN)
    ac = AuthClient()
    cur_user_id = ac._get_keycloak_user_id()
    assert cur_user_id == TEST_USER_ID
