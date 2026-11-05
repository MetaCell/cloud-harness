"""
API tests, authenticated with test tokens (see entra_token.py).

Requires ENTRA_TEST_PRIVATE_KEY and a deployment with `entra.test_tokens: true` (deploy/values-test.yaml).
"""
import os

import requests
import schemathesis as st

from entra_token import create_token

# django-ninja generates Open API 3.1 schemas
st.experimental.OPEN_API_3_1.enable()

# the application name, as in backend/django_baseapp/settings.py
APP_NAME = "__APP_NAME__".replace("_", "-")
app_url = os.environ.get("APP_URL", f"http://{APP_NAME}.ch.local/api").rstrip("/")

# the app roles, see AUTH_ADMIN_ROLE and AUTH_USER_ROLE in backend/django_baseapp/settings.py
ADMIN_ROLE = f"{APP_NAME}-administrator"
USER_ROLE = f"{APP_NAME}-user"

admin_token = create_token(roles=[ADMIN_ROLE], username="test-admin@example.com", name="Test Admin")
user_token = create_token(roles=[USER_ROLE], username="test-user@example.com", name="Test User")
no_role_token = create_token(roles=[], username="test-norole@example.com", name="Test Norole")


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


schema = st.from_uri(app_url + "/openapi.json", headers=bearer(admin_token))


@schema.auth()
class AdminTokenAuth:
    def get(self, case, context):
        return admin_token

    def set(self, case, data, context):
        case.headers = case.headers or {}
        case.headers["Authorization"] = f"Bearer {data}"
        # authenticate with the token only: no generated (possibly invalid) session cookie
        case.cookies = {}


def test_unauthenticated():
    assert requests.get(app_url + "/me").status_code == 401


def test_invalid_token():
    assert requests.get(app_url + "/me", headers=bearer("not-a-token")).status_code == 401


def test_no_app_role_forbidden():
    assert requests.get(app_url + "/me", headers=bearer(no_role_token)).status_code == 403


def test_me():
    response = requests.get(app_url + "/me", headers=bearer(user_token))
    assert response.status_code == 200
    assert response.json()["username"] == "test-user@example.com"
    assert response.json()["roles"] == [USER_ROLE]
    assert response.json()["is_admin"] is False


@schema.parametrize()
def test_api(case):
    response = case.call()
    case.validate_response(response)

