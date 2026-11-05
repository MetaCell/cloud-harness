import hashlib
import json
import posixpath
import re

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import AnonymousUser, User
from django.contrib.auth.views import redirect_to_login
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse

from cloudharness import log
from cloudharness.auth.entra import decode_token
from cloudharness.auth.exceptions import EntraNotConfigured, InvalidToken
from cloudharness.middleware import get_authentication_token

from cloudharness_django.services import get_auth_service
from cloudharness_django.views import logout_form


USER_CACHE_TTL = getattr(settings, "BEARER_TOKEN_USER_CACHE_TTL", 60)

# paths reachable without being logged in
DEFAULT_AUTH_EXEMPT_URLS = [
    r"^/api/live$",
    r"^/api/ready$",
    r"^/oidc/",
    r"^/admin/login/",
    # assets of the admin login page; not the frontend build (static/www), served to logged in users only
    r"^/static/(?!www/)",
]


# the claims synced to the Django user: a token with different values syncs the user again
SYNCED_CLAIMS = ("roles", "preferred_username", "upn", "email", "name", "given_name", "family_name")


def _get_bearer_cache_key(oid: str) -> str:
    return f"bearer_token_user:{oid}"


def _claims_fingerprint(claims: dict) -> str:
    synced = {name: claims.get(name) for name in SYNCED_CLAIMS}
    synced["roles"] = sorted(synced["roles"] or [])
    return hashlib.sha256(json.dumps(synced, sort_keys=True).encode()).hexdigest()


def invalidate_user_cache(oid: str) -> None:
    """
    Remove a user from the bearer-token cache (e.g. after deactivation).

    The cache is local to the process (LocMemCache by default): other processes
    drop the user after BEARER_TOKEN_USER_CACHE_TTL.
    """
    cache.delete(_get_bearer_cache_key(oid))


def _get_bearer_user(token: str):
    """The Django user of a bearer token, or None if the token is not valid."""
    try:
        claims = decode_token(token)
    except InvalidToken as e:
        log.info("Invalid bearer token: %s", e)
        return None
    except EntraNotConfigured:
        log.exception("Cannot validate the bearer token")
        return None

    # the user is cached with the claims it was synced from: a token with other roles
    # or names (e.g. a role removed in Entra) syncs the user again
    cache_key = _get_bearer_cache_key(claims["oid"])
    fingerprint = _claims_fingerprint(claims)
    cached = cache.get(cache_key)
    if cached is not None and cached[0] == fingerprint:
        return cached[1]
    user = authenticate(request=None, entra_claims=claims)
    if user is None or not user.is_active:
        cache.delete(cache_key)
        return None
    cache.set(cache_key, (fingerprint, user), timeout=USER_CACHE_TTL)
    return user


class BearerTokenMiddleware:
    """
    Authenticates the requests carrying an Entra access token in the Authorization header.

    Must come after AuthenticationMiddleware and CloudharnessMiddleware.
    A request with an invalid token is anonymous, even if it has a session.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        token = get_authentication_token()
        if token:
            user = _get_bearer_user(token)
            request.user = user or AnonymousUser()
            request._cached_user = request.user
        return self.get_response(request)


class LoginRequiredMiddleware:
    """
    Replaces the gatekeeper: every path requires a logged in user with one of the
    application roles (AUTH_ALL_ROLES), except AUTH_EXEMPT_URLS.

    Browser navigations are redirected to the Entra login, other requests get a 401.
    Set AUTH_REQUIRED = False to disable it and protect the views individually.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.exempt_urls = [re.compile(url) for url in getattr(settings, "AUTH_EXEMPT_URLS", DEFAULT_AUTH_EXEMPT_URLS)]

    def __call__(self, request):
        if not getattr(settings, "AUTH_REQUIRED", True) or self._is_exempt(request.path_info):
            return self.get_response(request)

        user = request.user
        if not user.is_authenticated:
            if self._is_browser_navigation(request):
                return redirect_to_login(request.get_full_path(), settings.LOGIN_URL)
            return JsonResponse({"message": "Unauthorized"}, status=401)

        if not get_auth_service().has_access(user):
            if self._is_browser_navigation(request):
                return HttpResponse(
                    "<h1>403 Permission Denied</h1>"
                    "<p>You do not have access to this application, please contact your administrator.</p>"
                    f'{logout_form(request, "Log in as a different user")}',
                    status=403)
            return JsonResponse({"message": "Forbidden"}, status=403)

        return self.get_response(request)

    def _is_exempt(self, path):
        # Only canonical paths can be exempt: the views may normalize a path like /static//www/ or
        # /static/./www/ to a protected one (/static/www/), so a non canonical path requires a login.
        canonical = posixpath.normpath(path)
        if path.endswith("/") and canonical != "/":
            canonical += "/"
        if canonical != path:
            return False
        return any(url.match(path) for url in self.exempt_urls)

    @staticmethod
    def _is_browser_navigation(request):
        return request.method == "GET" and "text/html" in request.headers.get("Accept", "") \
            and not request.headers.get("Authorization")
