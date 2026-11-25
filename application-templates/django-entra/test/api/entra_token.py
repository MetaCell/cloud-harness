"""
Test tokens for the API tests.

The test deployment (deploy/values-test.yaml, `entra.test_tokens: true`) accepts tokens signed
with a test key, besides the real Entra ones. This module signs them with the private key in
ENTRA_TEST_PRIVATE_KEY; the deployment gets the public key from the `entra-test-public-key` secret.

Generate a key pair with:

    python entra_token.py keygen
"""
import os
import sys
import time
import uuid

import jwt
import yaml
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

TEST_KEY_ID = "cloudharness-test"
HERE = os.path.dirname(os.path.realpath(__file__))
DEPLOY_DIR = os.path.join(HERE, "..", "..", "deploy")


def _entra_values() -> dict:
    """The entra section of deploy/values.yaml, overridden by deploy/values-test.yaml."""
    values = {}
    for name in ("values.yaml", "values-test.yaml"):
        path = os.path.join(DEPLOY_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                values.update((yaml.safe_load(f) or {}).get("entra") or {})
    return values


def get_tenant_id() -> str:
    return os.getenv("ENTRA_TENANT_ID") or _entra_values().get("tenant_id")


def get_client_id() -> str:
    return os.getenv("ENTRA_CLIENT_ID") or _entra_values().get("client_id")


def create_token(roles=(), oid=None, username="test-user@example.com", name="Test User", expires_in=3600) -> str:
    private_key = os.environ["ENTRA_TEST_PRIVATE_KEY"]
    tenant_id, client_id = get_tenant_id(), get_client_id()
    if not tenant_id or not client_id:
        raise RuntimeError("Set entra.tenant_id and entra.client_id in deploy/values.yaml "
                           "or ENTRA_TENANT_ID and ENTRA_CLIENT_ID")
    claims = {
        "iss": f"https://login.microsoftonline.com/{tenant_id}/v2.0",
        "aud": f"api://{client_id}",
        "tid": tenant_id,
        # stable per username, so that the tests reuse the same Django user
        "oid": oid or str(uuid.uuid5(uuid.NAMESPACE_DNS, username)),
        "preferred_username": username,
        "name": name,
        "roles": list(roles),
        # a delegated access token for the API scope
        "scp": "access",
        "iat": int(time.time()),
        "exp": int(time.time()) + expires_in,
    }
    return jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": TEST_KEY_ID})


def keygen():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    print("# ENTRA_TEST_PRIVATE_KEY (test runner, keep secret)")
    print(private_pem)
    print("# entra-test-public-key (test deployment secret)")
    print(public_pem)


if __name__ == "__main__" and sys.argv[1:] == ["keygen"]:
    keygen()
