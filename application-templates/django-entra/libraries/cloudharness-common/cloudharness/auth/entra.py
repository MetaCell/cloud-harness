"""
Microsoft Entra ID (single tenant) OIDC support.

Configuration is read from the `entra` section of the current application's
deploy/values.yaml:

    entra:
      tenant_id: <directory (tenant) id>
      client_id: <application (client) id>
      api_audience: api://<client id>   # optional, the default
      authority_host: https://login.microsoftonline.com  # optional, the default

The client secret is read from the `entra-client-secret` application secret.
Every value can be overridden with an environment variable (ENTRA_TENANT_ID,
ENTRA_CLIENT_ID, ENTRA_CLIENT_SECRET, ENTRA_API_AUDIENCE, ENTRA_AUTHORITY_HOST),
which is how the application is configured when running locally.

Test deployments (deploy/values-test.yaml) can set `entra.test_tokens: true` to also accept
tokens signed with a local test key (header `kid: cloudharness-test`), whose PEM public key is
read from the `entra-test-public-key` secret or ENTRA_TEST_PUBLIC_KEY. The test tokens must
carry the same issuer, audience and tenant as the Entra ones. Never enable it in production.
"""
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import List, Optional

import jwt

from cloudharness import log
from cloudharness.middleware import get_authentication_token

from .exceptions import EntraNotConfigured, InvalidToken

DEFAULT_AUTHORITY_HOST = "https://login.microsoftonline.com"
CLIENT_SECRET_NAME = "entra-client-secret"
TEST_PUBLIC_KEY_SECRET_NAME = "entra-test-public-key"
TEST_KEY_ID = "cloudharness-test"
JWKS_CACHE_LIFESPAN = 3600


@dataclass(frozen=True)
class EntraConfig:
    tenant_id: str
    client_id: str
    client_secret: Optional[str] = None
    api_audience: Optional[str] = None
    authority_host: str = DEFAULT_AUTHORITY_HOST
    # PEM public key of the test token signing key, only set when test tokens are enabled
    test_public_key: Optional[str] = None

    @property
    def authority(self) -> str:
        return f"{self.authority_host.rstrip('/')}/{self.tenant_id}"

    @property
    def jwks_uri(self) -> str:
        return f"{self.authority}/discovery/v2.0/keys"

    @property
    def logout_url(self) -> str:
        return f"{self.authority}/oauth2/v2.0/logout"

    @property
    def issuers(self) -> List[str]:
        # v2.0 tokens and v1.0 access tokens (accessTokenAcceptedVersion unset)
        return [f"{self.authority}/v2.0", f"https://sts.windows.net/{self.tenant_id}/"]

    @property
    def audiences(self) -> List[str]:
        return [self.client_id, self.api_audience or f"api://{self.client_id}"]


@dataclass
class EntraIdentity:
    """The user described by the claims of a validated Entra token."""
    oid: str
    tenant_id: str
    username: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    roles: List[str] = field(default_factory=list)

    @classmethod
    def from_claims(cls, claims: dict) -> "EntraIdentity":
        oid = claims.get("oid")
        if not oid:
            raise InvalidToken("Token has no oid claim")
        username = claims.get("preferred_username") or claims.get("upn") or claims.get("email") or oid
        email = claims.get("email") or (username if "@" in username else "")
        first_name = claims.get("given_name")
        last_name = claims.get("family_name")
        if first_name is None and last_name is None:
            # given_name/family_name are optional claims: fall back to splitting the display name
            first_name, _, last_name = (claims.get("name") or "").partition(" ")
        return cls(
            oid=oid,
            tenant_id=claims.get("tid", ""),
            username=username,
            email=email,
            first_name=first_name or "",
            last_name=last_name or "",
            roles=list(claims.get("roles") or []),
        )


def _get_app_entra_values() -> dict:
    try:
        from cloudharness.applications import get_current_configuration
        return get_current_configuration().conf["entra"] or {}
    except Exception:
        log.warning("No entra configuration found for the current application, using environment variables only")
        return {}


def _get_secret_value(env_name: str, secret_name: str) -> Optional[str]:
    if os.getenv(env_name):
        return os.getenv(env_name)
    try:
        from cloudharness.utils.secrets import get_secret
        return get_secret(secret_name).strip() or None
    except Exception:
        return None


def _get_test_public_key(values: dict) -> Optional[str]:
    enabled = os.getenv("ENTRA_TEST_TOKENS", "").lower() in ("1", "true", "yes") or values.get("test_tokens") is True
    if not enabled:
        return None
    public_key = _get_secret_value("ENTRA_TEST_PUBLIC_KEY", TEST_PUBLIC_KEY_SECRET_NAME)
    if not public_key:
        log.error("Entra test tokens are enabled but no test public key is set: test tokens are rejected")
        return None
    log.warning("Entra test tokens are ENABLED: tokens signed with the test key are accepted. Never enable in production.")
    return public_key


@lru_cache(maxsize=1)
def get_entra_config() -> EntraConfig:
    values = _get_app_entra_values()
    tenant_id = os.getenv("ENTRA_TENANT_ID") or values.get("tenant_id")
    client_id = os.getenv("ENTRA_CLIENT_ID") or values.get("client_id")
    if not tenant_id or not client_id:
        raise EntraNotConfigured()
    return EntraConfig(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=_get_secret_value("ENTRA_CLIENT_SECRET", CLIENT_SECRET_NAME),
        api_audience=os.getenv("ENTRA_API_AUDIENCE") or values.get("api_audience"),
        authority_host=os.getenv("ENTRA_AUTHORITY_HOST") or values.get("authority_host") or DEFAULT_AUTHORITY_HOST,
        test_public_key=_get_test_public_key(values),
    )


@lru_cache(maxsize=4)
def _get_jwks_client(jwks_uri: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(jwks_uri, cache_keys=True, lifespan=JWKS_CACHE_LIFESPAN)


def _get_signing_key(token: str, config: EntraConfig):
    if jwt.get_unverified_header(token).get("kid") == TEST_KEY_ID:
        if not config.test_public_key:
            raise InvalidToken("Test tokens are not enabled")
        return config.test_public_key
    return _get_jwks_client(config.jwks_uri).get_signing_key_from_jwt(token).key


def decode_token(token: str, config: EntraConfig = None) -> dict:
    """
    Validate an Entra access token issued for this application and return its claims.

    Checks the signature against the tenant signing keys, the expiration, the issuer,
    the audience and the tenant, and that it is a delegated (user) access token: it has
    the `scp` claim. ID tokens (same audience in v2.0) and application (client credentials)
    tokens have no `scp` and are rejected.

    :raises InvalidToken: if the token is not valid
    """
    config = config or get_entra_config()
    try:
        claims = jwt.decode(
            token,
            _get_signing_key(token, config),
            algorithms=["RS256"],
            audience=config.audiences,
            issuer=config.issuers,
            options={"require": ["exp", "iss", "aud", "oid"]},
        )
    except (jwt.exceptions.InvalidTokenError, jwt.exceptions.PyJWKClientError) as e:
        raise InvalidToken(e) from e
    if claims.get("tid") != config.tenant_id:
        raise InvalidToken("Token issued for another tenant")
    if not claims.get("scp"):
        raise InvalidToken("Not a delegated access token (no scp claim)")
    return claims


def get_current_user_claims() -> Optional[dict]:
    """Claims of the bearer token of the current request, or None if missing or invalid."""
    token = get_authentication_token()
    if not token:
        return None
    try:
        return decode_token(token)
    except InvalidToken:
        return None


def get_current_user_id() -> Optional[str]:
    claims = get_current_user_claims()
    return claims.get("oid") if claims else None


__all__ = [
    "EntraConfig",
    "EntraIdentity",
    "get_entra_config",
    "decode_token",
    "get_current_user_claims",
    "get_current_user_id",
]
