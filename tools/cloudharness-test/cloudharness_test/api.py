import os
from os.path import dirname as dn
import logging
import subprocess

from ch_cli_tools.preprocessing import get_build_paths


from cloudharness_model.models import  HarnessMainConfig, ApiTestsConfig, ApplicationHarnessConfig
from cloudharness_utils.testing.util import get_app_environment
from cloudharness_utils.testing.api import get_api_filename, get_urls_from_api_file, get_schemathesis_command

from ruamel.yaml import YAML

yaml = YAML(typ='safe')


def run_api_tests(root_paths, helm_values: HarnessMainConfig, base_domain, included_applications=[]):
    """
    Run api tests with Schemathesis and Pytest.

    See also https://schemathesis.readthedocs.io/en/stable/cli.html#schemathesis-run
    """
    artifacts = get_build_paths(
        helm_values=helm_values, root_paths=root_paths)

    failed = False
    for appkey in helm_values.apps:
        app_config: ApplicationHarnessConfig = helm_values.apps[appkey].harness

        appname = app_config.name

        if included_applications and appname not in included_applications:
            continue

        app_dir = artifacts[helm_values.apps[appkey].harness.name]
        api_config: ApiTestsConfig = app_config.test.api

        if not api_config.enabled:
            continue

        api_filename = get_api_filename(app_dir)

        if not app_config.domain and not app_config.subdomain:
            logging.warn(
                "Application %s has a api specification but no subdomain/domain is specified", appname)
            continue

        server_urls = get_urls_from_api_file(api_filename)
        for app_domain in server_urls:
            if not os.path.exists(api_filename):
                continue

            if "http" not in app_domain:
                app_domain = f"http{'s' if helm_values.tls else ''}://" +\
                    (app_config.domain or f"{app_config.subdomain}.{base_domain}{app_domain}")

            logging.info(
                "Running api tests for application %s on domain %s", appname, app_domain)

            app_env = get_app_environment(app_config, app_domain)

            if api_config.autotest:
                logging.info("Running auto api tests")
                cmd = get_schemathesis_command(api_filename, app_config, app_domain)
                logging.info("Running: %s", " ".join(cmd))
                result = subprocess.run(cmd,
                                        env=app_env, cwd=app_dir)
                if result.returncode > 0:
                    failed = True

            tests_dir = os.path.join(app_dir, "test", "api")

            if os.path.exists(tests_dir):
                logging.info("Running custom api tests")
                result = subprocess.run(
                    ["pytest", "-v", "."], cwd=tests_dir, env=app_env)

                if result.returncode > 0:
                    failed = True

    if failed:
        logging.error(
            "Some api test failed. Check output for more information.")
        exit(1)

