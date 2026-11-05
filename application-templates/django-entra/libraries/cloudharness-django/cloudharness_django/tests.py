from unittest import mock

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase, override_settings

from cloudharness.auth.entra import EntraConfig, EntraIdentity
from cloudharness.auth.exceptions import InvalidToken

from cloudharness_django.models import Member
from cloudharness_django.services import init_services, get_user_service

TENANT_ID = "11111111-1111-1111-1111-111111111111"
CLIENT_ID = "22222222-2222-2222-2222-222222222222"
OID = "33333333-3333-3333-3333-333333333333"
CONFIG = EntraConfig(tenant_id=TENANT_ID, client_id=CLIENT_ID, client_secret="secret")

ADMIN, USER = "app-administrator", "app-user"
ROLE_SETTINGS = dict(AUTH_ADMIN_ROLE=ADMIN, AUTH_ALL_ROLES=[ADMIN, USER])
MODEL_BACKEND = "django.contrib.auth.backends.ModelBackend"
ENTRA_BACKENDS = ["cloudharness_django.backends.EntraBackend"]
PASSWORD_BACKENDS = ENTRA_BACKENDS + [MODEL_BACKEND]


def claims(roles=(USER,), oid=OID, **overrides):
    result = {
        "oid": oid,
        "tid": TENANT_ID,
        "preferred_username": "jane@contoso.com",
        "name": "Jane Doe",
        "roles": list(roles),
    }
    result.update(overrides)
    return result


def identity(**kwargs):
    return EntraIdentity.from_claims(claims(**kwargs))


@override_settings(**ROLE_SETTINGS)
class EntraTestCase(TestCase):
    def setUp(self):
        cache.clear()
        init_services()
        patcher = mock.patch("cloudharness_django.backends.get_entra_config", return_value=CONFIG)
        patcher.start()
        self.addCleanup(patcher.stop)


class UserServiceTest(EntraTestCase):

    def test_creates_user_and_member(self):
        user = get_user_service().sync_user(identity())
        self.assertEqual(user.username, "jane@contoso.com")
        self.assertEqual(user.email, "jane@contoso.com")
        self.assertEqual((user.first_name, user.last_name), ("Jane", "Doe"))
        self.assertFalse(user.has_usable_password())
        self.assertEqual(user.member.oid, OID)
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_updates_existing_user(self):
        get_user_service().sync_user(identity())
        user = get_user_service().sync_user(identity(name="Jane Smith", preferred_username="jane.smith@contoso.com"))
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.username, "jane.smith@contoso.com")
        self.assertEqual(user.last_name, "Smith")

    def test_role_levels(self):
        user = get_user_service().sync_user(identity(roles=[ADMIN]))
        self.assertTrue(user.is_superuser and user.is_staff)
        user = get_user_service().sync_user(identity(roles=[USER]))
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_roles_mirrored_as_groups(self):
        user = get_user_service().sync_user(identity(roles=[ADMIN, USER, "unknown-role"]))
        other_group = Group.objects.create(name="other")
        user.groups.add(other_group)
        self.assertEqual(set(user.groups.values_list("name", flat=True)), {ADMIN, USER, "other"})

        user = get_user_service().sync_user(identity(roles=[USER]))
        self.assertEqual(set(user.groups.values_list("name", flat=True)), {USER, "other"})

    def test_deactivated_user_stays_deactivated(self):
        user = get_user_service().sync_user(identity())
        user.is_active = False
        user.save()
        user = get_user_service().sync_user(identity())
        self.assertFalse(user.is_active)

    def test_does_not_adopt_local_user_with_same_username(self):
        local = User.objects.create_superuser("jane@contoso.com", password="pwd")
        user = get_user_service().sync_user(identity())
        self.assertNotEqual(user.pk, local.pk)
        self.assertEqual(user.username, f"jane@contoso.com-{OID[:8]}")
        local.refresh_from_db()
        self.assertTrue(local.is_superuser)
        self.assertFalse(Member.objects.filter(user=local).exists())


class BearerTokenTest(EntraTestCase):

    def get_me(self, token="valid", claims_=None, error=None):
        with mock.patch("cloudharness_django.middleware.decode_token",
                        side_effect=error, return_value=claims_ or claims()):
            return self.client.get("/api/me", HTTP_AUTHORIZATION=f"Bearer {token}")

    def test_valid_token(self):
        response = self.get_me()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "jane@contoso.com")
        self.assertEqual(response.json()["roles"], [USER])

    def test_invalid_token(self):
        response = self.get_me(error=InvalidToken("expired"))
        self.assertEqual(response.status_code, 401)

    def test_other_tenant_rejected(self):
        response = self.get_me(claims_=claims(tid="other-tenant"))
        self.assertEqual(response.status_code, 401)

    def test_no_app_role_forbidden(self):
        response = self.get_me(claims_=claims(roles=[]))
        self.assertEqual(response.status_code, 403)

    def test_user_cached(self):
        self.get_me()
        with mock.patch("cloudharness_django.backends.get_user_service") as user_service:
            self.assertEqual(self.get_me().status_code, 200)
            user_service.assert_not_called()

    def test_changed_roles_not_served_from_cache(self):
        self.assertEqual(self.get_me(claims_=claims(roles=[ADMIN])).json()["is_admin"], True)
        response = self.get_me(claims_=claims(roles=[USER]))
        self.assertEqual(response.json()["is_admin"], False)
        self.assertEqual(response.json()["roles"], [USER])

    def test_deactivated_user_rejected(self):
        self.get_me()
        user = User.objects.get(member__oid=OID)
        user.is_active = False
        user.save()  # also drops the cached user
        self.assertEqual(self.get_me().status_code, 401)


class LoginRequiredTest(EntraTestCase):

    def test_browser_redirected_to_login(self):
        response = self.client.get("/", HTTP_ACCEPT="text/html,application/xhtml+xml")
        self.assertRedirects(response, "/oidc/login/?next=/", fetch_redirect_response=False)

    def test_api_unauthorized(self):
        self.assertEqual(self.client.get("/api/me", HTTP_ACCEPT="*/*").status_code, 401)

    def test_probes_exempt(self):
        self.assertEqual(self.client.get("/api/live").status_code, 200)
        self.assertEqual(self.client.get("/api/ready").status_code, 200)

    def test_static_assets_exempt_but_not_frontend(self):
        self.assertNotEqual(self.client.get("/static/admin/css/base.css").status_code, 401)
        self.assertEqual(self.client.get("/static/www/index.html", HTTP_ACCEPT="*/*").status_code, 401)
        self.assertEqual(self.client.get("/static/www/assets/index.js", HTTP_ACCEPT="*/*").status_code, 401)

    def test_non_canonical_paths_not_exempt(self):
        # the static view normalizes these to static/www/index.html
        for path in ("/static//www/index.html", "/static/./www/index.html", "/static/admin/../www/index.html"):
            self.assertEqual(self.client.get(path, HTTP_ACCEPT="*/*").status_code, 401, path)

    @override_settings(PASSWORD_LOGIN_ENABLED=True, AUTHENTICATION_BACKENDS=PASSWORD_BACKENDS)
    def test_local_superuser_has_access(self):
        User.objects.create_superuser("admin", password="pwd")
        self.client.login(username="admin", password="pwd")
        self.assertEqual(self.client.get("/api/me").status_code, 200)


@override_settings(PASSWORD_LOGIN_ENABLED=False, AUTHENTICATION_BACKENDS=ENTRA_BACKENDS)
class AdminLoginTest(EntraTestCase):
    """The Django admin login goes through Entra, unless PASSWORD_LOGIN_ENABLED."""

    def test_anonymous_redirected_to_entra_login(self):
        response = self.client.get("/admin/", HTTP_ACCEPT="text/html")
        self.assertRedirects(response, "/oidc/login/?next=/admin/", fetch_redirect_response=False)
        # /admin/login/ is not protected by the login required middleware
        response = self.client.get("/admin/login/?next=/admin/")
        self.assertRedirects(response, "/oidc/login/?next=/admin/", fetch_redirect_response=False)

    def test_local_password_rejected(self):
        User.objects.create_superuser("admin", password="pwd")
        self.assertFalse(self.client.login(username="admin", password="pwd"))
        response = self.client.post("/admin/login/", {"username": "admin", "password": "pwd"})
        self.assertRedirects(response, "/oidc/login/?next=/admin/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/api/me").status_code, 401)

    def test_local_superuser_session_not_accepted(self):
        user = User.objects.create_superuser("admin", password="pwd")
        self.client.force_login(user, backend=MODEL_BACKEND)
        self.assertEqual(self.client.get("/api/me").status_code, 401)

    def test_administrator_redirected_to_admin(self):
        user = get_user_service().sync_user(identity(roles=[ADMIN]))
        self.client.force_login(user, backend=ENTRA_BACKENDS[0])
        response = self.client.get("/admin/login/?next=/admin/")
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/admin/").status_code, 200)

    def test_user_without_admin_role_forbidden(self):
        user = get_user_service().sync_user(identity(roles=[USER]))
        self.client.force_login(user, backend=ENTRA_BACKENDS[0])
        response = self.client.get("/admin/", HTTP_ACCEPT="text/html")
        self.assertRedirects(response, "/admin/login/?next=/admin/", fetch_redirect_response=False)
        response = self.client.get("/admin/login/?next=/admin/")
        self.assertContains(response, "requires the administrator role", status_code=403)
        self.assertContains(response, '<form method="post" action="/oidc/logout/">', status_code=403)

    @override_settings(PASSWORD_LOGIN_ENABLED=True, AUTHENTICATION_BACKENDS=PASSWORD_BACKENDS)
    def test_password_login_when_enabled(self):
        User.objects.create_superuser("admin", password="pwd")
        self.assertContains(self.client.get("/admin/login/"), 'name="password"')
        response = self.client.post("/admin/login/?next=/admin/", {"username": "admin", "password": "pwd"})
        self.assertRedirects(response, "/admin/", fetch_redirect_response=False)


class FakeMsalApp:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error

    def initiate_auth_code_flow(self, scopes, redirect_uri):
        return {"auth_uri": f"https://login.example/authorize?redirect_uri={redirect_uri}", "state": "abc"}

    def acquire_token_by_auth_code_flow(self, flow, response):
        if self.error:
            raise self.error
        return self.result


class OidcViewsTest(EntraTestCase):

    def login(self, next_url="/somewhere"):
        with mock.patch("cloudharness_django.views._get_msal_app", return_value=FakeMsalApp()):
            return self.client.get("/oidc/login/", {"next": next_url})

    def callback(self, app):
        with mock.patch("cloudharness_django.views._get_msal_app", return_value=app):
            return self.client.get("/oidc/callback/", {"code": "c", "state": "abc"})

    def test_login_redirects_to_entra(self):
        response = self.login()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("https://login.example/authorize"))
        self.assertIn("oidc%2Fcallback%2F", response["Location"].replace("/", "%2F"))

    def test_callback_logs_in(self):
        self.login()
        response = self.callback(FakeMsalApp(result={"id_token_claims": claims()}))
        self.assertRedirects(response, "/somewhere", fetch_redirect_response=False)
        self.assertEqual(self.client.get("/api/me").json()["username"], "jane@contoso.com")

    def test_unsafe_next_ignored(self):
        self.login(next_url="https://evil.example/")
        response = self.callback(FakeMsalApp(result={"id_token_claims": claims()}))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_callback_error(self):
        self.login()
        response = self.callback(FakeMsalApp(result={"error": "access_denied"}))
        self.assertEqual(response.status_code, 403)

    def test_callback_state_mismatch(self):
        self.login()
        response = self.callback(FakeMsalApp(error=ValueError("state mismatch")))
        self.assertEqual(response.status_code, 400)

    def test_callback_without_flow_restarts_login(self):
        response = self.callback(FakeMsalApp(result={"id_token_claims": claims()}))
        self.assertRedirects(response, "/oidc/login/", fetch_redirect_response=False)

    def test_logout(self):
        self.login()
        self.callback(FakeMsalApp(result={"id_token_claims": claims()}))
        with mock.patch("cloudharness_django.views.get_entra_config", return_value=CONFIG):
            response = self.client.post("/oidc/logout/")
        self.assertTrue(response["Location"].startswith(f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"))
        self.assertEqual(self.client.get("/api/me").status_code, 401)

    def test_logout_requires_post_with_csrf_token(self):
        self.login()
        self.callback(FakeMsalApp(result={"id_token_claims": claims()}))
        # a GET only shows the logout form
        response = self.client.get("/oidc/logout/")
        self.assertContains(response, '<form method="post" action="/oidc/logout/">')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.assertEqual(self.client.get("/api/me").status_code, 200)
        csrf_client = self.client_class(enforce_csrf_checks=True)
        csrf_client.cookies = self.client.cookies
        self.assertEqual(csrf_client.post("/oidc/logout/").status_code, 403)
        self.assertEqual(self.client.get("/api/me").status_code, 200)

    def test_deactivated_user_cannot_log_in(self):
        self.login()
        self.callback(FakeMsalApp(result={"id_token_claims": claims()}))
        User.objects.filter(member__oid=OID).update(is_active=False)
        self.client.logout()
        self.login()
        response = self.callback(FakeMsalApp(result={"id_token_claims": claims()}))
        self.assertEqual(response.status_code, 403)

