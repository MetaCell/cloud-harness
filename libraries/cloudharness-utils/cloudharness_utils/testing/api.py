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
    """Return schemathesis CLI flags for auth."""
    if not app_env:
        return []
    username = app_env.get("USERNAME")
    password = app_env.get("PASSWORD")
    if not (username and password):
        return []
    try:
        token = get_token(username, password)
        if not token:
            logging.warning("Token retrieval returned empty token for user %s", username)
            return []
        return ["--header", f"Authorization: Bearer {token}", "--header", f"Cookie: kc-access={token}"]
    except Exception as e:
        logging.warning("Failed to retrieve bearer token for user %s: %s", username, e)
        return []


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
