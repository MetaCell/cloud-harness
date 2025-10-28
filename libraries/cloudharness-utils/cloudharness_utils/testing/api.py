import os
import logging

from ruamel.yaml import YAML

from cloudharness_model.models import ApiTestsConfig, ApplicationHarnessConfig
from cloudharness.auth import get_token

yaml = YAML(typ='safe')


def get_api_filename(app_dir):
    return os.path.join(app_dir, "api", "openapi.yaml")


def get_schemathesis_command(api_filename, app_config: ApplicationHarnessConfig, app_domain: str, app_env: dict | None = None):
    """
    Build the schemathesis command for running API tests.

    Extended to support runtime authentication header generation directly in the command instead of relying on hooks.
    """
    return ["st", "run", api_filename, *get_schemathesis_params(app_config, app_domain, app_env)]


def _get_auth_headers(app_env: dict):
    """Return list of CLI flags setting auth & headers based on environment.

    Supported:
    - USERNAME/PASSWORD -> basic auth OR bearer token if token retrievable
    - API_KEY -> X-API-Key header
    - BEARER_TOKEN explicit -> Authorization header
    Priority order:
      1. Explicit BEARER_TOKEN
      2. USERNAME/PASSWORD -> try get_token (Keycloak) then fallback to --auth basic
      3. API_KEY header
    """
    if not app_env:
        return []
    flags = []

    bearer = app_env.get("BEARER_TOKEN")
    username = app_env.get("USERNAME")
    password = app_env.get("PASSWORD")
    api_key = app_env.get("API_KEY")

    if bearer:
        flags += ["--header", f"Authorization: Bearer {bearer}"]
    elif username and password:
        # Attempt to retrieve token; if fails, fallback to basic auth
        try:
            token = get_token(username, password)
            if token:
                flags += ["--header", f"Authorization: Bearer {token}"]
                # also cookie header if needed by backend
                flags += ["--header", f"Cookie: kc-access={token}"]
            else:
                flags += ["--auth", f"{username}:{password}"]
        except Exception as e:
            logging.warning("Failed to retrieve bearer token; fallback to basic auth: %s", e)
            flags += ["--auth", f"{username}:{password}"]

    if api_key:
        flags += ["--header", f"X-API-Key: {api_key}"]
    return flags


def get_schemathesis_params(app_config: ApplicationHarnessConfig, app_domain: str, app_env: dict | None = None):
    params = ["--url", app_domain]
    api_config: ApiTestsConfig = app_config.test.api
    if api_config.checks:
        for c in api_config.checks:
            params += ["-c", c]

    params.extend(api_config.run_params)
    params.extend(_get_auth_headers(app_env or {}))
    return params


def get_urls_from_api_file(api_filename):
    with open(api_filename) as f:
        c = yaml.load(f)
    server_urls = c["servers"]
    return [s['url'] for s in server_urls]
