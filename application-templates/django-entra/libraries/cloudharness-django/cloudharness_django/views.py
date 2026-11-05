"""
OpenID Connect authorization code flow (with PKCE) against Microsoft Entra ID.
"""
from urllib.parse import urlencode

import msal
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden, HttpResponseRedirect
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils.html import escape
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods

from cloudharness import log
from cloudharness.auth.entra import get_entra_config

SESSION_FLOW_KEY = "entra_auth_flow"
SESSION_NEXT_KEY = "entra_auth_next"
SCOPES = ["email"]  # msal always adds openid, profile and offline_access

# shared cache of the Entra metadata documents fetched by msal
_msal_http_cache = {}


def _get_msal_app() -> msal.ConfidentialClientApplication:
    config = get_entra_config()
    # a new application (and token cache) per login: tokens are not kept server side
    return msal.ConfidentialClientApplication(
        config.client_id,
        client_credential=config.client_secret,
        authority=config.authority,
        http_cache=_msal_http_cache,
    )


def safe_next(request, url):
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return url
    return settings.LOGIN_REDIRECT_URL


@require_GET
def login(request):
    flow = _get_msal_app().initiate_auth_code_flow(
        SCOPES,
        redirect_uri=request.build_absolute_uri(reverse("oidc_callback")),
    )
    request.session[SESSION_FLOW_KEY] = flow
    request.session[SESSION_NEXT_KEY] = safe_next(request, request.GET.get("next"))
    return HttpResponseRedirect(flow["auth_uri"])


@require_GET
def callback(request):
    flow = request.session.pop(SESSION_FLOW_KEY, None)
    next_url = request.session.pop(SESSION_NEXT_KEY, settings.LOGIN_REDIRECT_URL)
    if not flow:
        # expired session or callback replayed: start over
        return HttpResponseRedirect(reverse("oidc_login"))

    try:
        result = _get_msal_app().acquire_token_by_auth_code_flow(flow, request.GET.dict())
    except ValueError:
        # state mismatch
        return HttpResponseBadRequest("Invalid authentication response")

    if "error" in result:
        log.warning("Entra login failed: %s %s", result.get("error"), result.get("error_description"))
        return HttpResponseForbidden("Login failed")

    user = authenticate(request, entra_claims=result.get("id_token_claims"))
    if user is None or not user.is_active:
        return HttpResponseForbidden("Login failed")

    auth_login(request, user, backend="cloudharness_django.backends.EntraBackend")
    return HttpResponseRedirect(next_url)


def logout_form(request, label="Log out"):
    """HTML form posting to the logout view, with the CSRF token."""
    return (
        f'<form method="post" action="{reverse("oidc_logout")}">'
        f'<input type="hidden" name="csrfmiddlewaretoken" value="{escape(get_token(request))}">'
        f'<button type="submit">{escape(label)}</button></form>'
    )


@require_http_methods(["GET", "POST"])
def logout(request):
    if request.method == "GET":
        # only a POST with the CSRF token logs out, a GET could be triggered by any page (logout CSRF):
        # links and bookmarks to the logout page get a confirmation form
        return HttpResponse(f"<h1>Log out</h1>{logout_form(request)}")
    auth_logout(request)
    query = urlencode({"post_logout_redirect_uri": request.build_absolute_uri(settings.LOGIN_REDIRECT_URL)})
    return HttpResponseRedirect(f"{get_entra_config().logout_url}?{query}")
