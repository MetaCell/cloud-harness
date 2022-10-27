import os

from ruamel.yaml import YAML

from cloudharness_model.models import ApiTestsConfig, ApplicationHarnessConfig

yaml = YAML(typ='safe')


def get_api_filename(app_dir):
    return os.path.join(app_dir, "api", "openapi.yaml")


def get_schemathesis_command(api_filename, app_config: ApplicationHarnessConfig, app_domain: str):
    return ["st", "--pre-run", "cloudharness_test.apitest_init", "run",  api_filename, *get_schemathesis_params(app_config, app_domain)]


def get_schemathesis_params(app_config: ApplicationHarnessConfig, app_domain: str):
    params = ["--base-url", app_domain]
    api_config: ApiTestsConfig = app_config.test.api
    if api_config.checks:
        for c in api_config.checks:
            params += ["-c", c]

    return [*params, *api_config.runParams]


def get_urls_from_api_file(api_filename):
    with open(api_filename) as f:
        c = yaml.load(f)
    server_urls = c["servers"]
    return [s['url'] for s in server_urls]
