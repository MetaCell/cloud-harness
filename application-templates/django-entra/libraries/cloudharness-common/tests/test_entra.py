import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from cloudharness.auth import entra
from cloudharness.auth.entra import EntraConfig, EntraIdentity, decode_token
from cloudharness.auth.exceptions import EntraNotConfigured, InvalidToken

TENANT_ID = "11111111-1111-1111-1111-111111111111"
CLIENT_ID = "22222222-2222-2222-2222-222222222222"
OID = "33333333-3333-3333-3333-333333333333"

CONFIG = EntraConfig(tenant_id=TENANT_ID, client_id=CLIENT_ID)

_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
_other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def jwks(monkeypatch):
    client = SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=_key.public_key()))
    monkeypatch.setattr(entra, "_get_jwks_client", lambda uri: client)


def make_token(key=_key, **overrides):
    claims = {
        "iss": f"https://login.microsoftonline.com/{TENANT_ID}/v2.0",
        "aud": f"api://{CLIENT_ID}",
        "tid": TENANT_ID,
        "oid": OID,
        "exp": int(time.time()) + 300,
        "preferred_username": "jane@contoso.com",
        "name": "Jane Doe",
        "roles": ["app-user"],
        "scp": "access",
    }
    claims.update(overrides)
    claims = {k: v for k, v in claims.items() if v is not None}
    return jwt.encode(claims, key, algorithm="RS256")


def test_valid_token():
    claims = decode_token(make_token(), CONFIG)
    assert claims["oid"] == OID


@pytest.mark.parametrize("aud", [CLIENT_ID, f"api://{CLIENT_ID}"])
def test_accepted_audiences(aud):
    assert decode_token(make_token(aud=aud), CONFIG)["oid"] == OID


def test_v1_issuer_accepted():
    token = make_token(iss=f"https://sts.windows.net/{TENANT_ID}/")
    assert decode_token(token, CONFIG)["oid"] == OID


@pytest.mark.parametrize("overrides", [
    {"exp": int(time.time()) - 10},
    {"aud": "api://someone-else"},
    {"iss": "https://login.microsoftonline.com/other-tenant/v2.0"},
    {"tid": "other-tenant"},
    {"oid": None},
    # ID token or application token
    {"scp": None},
])
def test_invalid_claims_rejected(overrides):
    with pytest.raises(InvalidToken):
        decode_token(make_token(**overrides), CONFIG)


def test_wrong_signature_rejected():
    with pytest.raises(InvalidToken):
        decode_token(make_token(key=_other_key), CONFIG)


def test_garbage_rejected():
    with pytest.raises(InvalidToken):
        decode_token("not-a-jwt", CONFIG)


def test_identity_from_claims_splits_display_name():
    identity = EntraIdentity.from_claims(jwt.decode(make_token(), options={"verify_signature": False}))
    assert identity.oid == OID
    assert identity.username == "jane@contoso.com"
    assert identity.email == "jane@contoso.com"
    assert (identity.first_name, identity.last_name) == ("Jane", "Doe")
    assert identity.roles == ["app-user"]


def test_identity_prefers_given_and_family_name():
    identity = EntraIdentity.from_claims({"oid": OID, "preferred_username": "jd", "name": "X Y",
                                          "given_name": "Jane", "family_name": "Doe", "email": "j@d.com"})
    assert (identity.first_name, identity.last_name, identity.email) == ("Jane", "Doe", "j@d.com")


def test_config_from_environment(monkeypatch):
    entra.get_entra_config.cache_clear()
    monkeypatch.setenv("ENTRA_TENANT_ID", TENANT_ID)
    monkeypatch.setenv("ENTRA_CLIENT_ID", CLIENT_ID)
    monkeypatch.setenv("ENTRA_CLIENT_SECRET", "s3cret")
    try:
        config = entra.get_entra_config()
        assert config.authority == f"https://login.microsoftonline.com/{TENANT_ID}"
        assert config.client_secret == "s3cret"
        assert config.audiences == [CLIENT_ID, f"api://{CLIENT_ID}"]
    finally:
        entra.get_entra_config.cache_clear()


def test_config_missing(monkeypatch):
    entra.get_entra_config.cache_clear()
    monkeypatch.delenv("ENTRA_TENANT_ID", raising=False)
    monkeypatch.delenv("ENTRA_CLIENT_ID", raising=False)
    monkeypatch.setattr(entra, "_get_app_entra_values", lambda: {})
    try:
        with pytest.raises(EntraNotConfigured):
            entra.get_entra_config()
    finally:
        entra.get_entra_config.cache_clear()


def _pem_public(key):
    from cryptography.hazmat.primitives import serialization
    return key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()


_test_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
TEST_CONFIG = EntraConfig(tenant_id=TENANT_ID, client_id=CLIENT_ID, test_public_key=_pem_public(_test_key))


def make_test_token(key=_test_key, **overrides):
    token = make_token(key=key, **overrides)
    claims = jwt.decode(token, options={"verify_signature": False})
    return jwt.encode(claims, key, algorithm="RS256", headers={"kid": entra.TEST_KEY_ID})


def test_test_token_accepted_when_enabled():
    assert decode_token(make_test_token(), TEST_CONFIG)["oid"] == OID


def test_test_token_rejected_when_disabled():
    with pytest.raises(InvalidToken):
        decode_token(make_test_token(), CONFIG)


def test_test_token_signed_with_other_key_rejected():
    with pytest.raises(InvalidToken):
        decode_token(make_test_token(key=_other_key), TEST_CONFIG)


def test_test_token_claims_still_checked():
    with pytest.raises(InvalidToken):
        decode_token(make_test_token(tid="other-tenant"), TEST_CONFIG)
    with pytest.raises(InvalidToken):
        decode_token(make_test_token(aud="api://someone-else"), TEST_CONFIG)


def test_test_public_key_requires_flag(monkeypatch):
    monkeypatch.setenv("ENTRA_TEST_PUBLIC_KEY", "pem")
    monkeypatch.delenv("ENTRA_TEST_TOKENS", raising=False)
    assert entra._get_test_public_key({}) is None
    assert entra._get_test_public_key({"test_tokens": True}) == "pem"
    monkeypatch.setenv("ENTRA_TEST_TOKENS", "true")
    assert entra._get_test_public_key({}) == "pem"


def test_test_tokens_enabled_without_key(monkeypatch):
    monkeypatch.delenv("ENTRA_TEST_PUBLIC_KEY", raising=False)
    assert entra._get_test_public_key({"test_tokens": True}) is None
