import os
from os.path import dirname as dn
import logging
from shutil import which
import subprocess

from cloudharness_model.models import ApplicationHarnessConfig

from cloudharness_utils.constants import  E2E_TESTS_PROJECT_PATH, E2E_TESTS_DIRNAME
from ch_cli_tools.preprocessing import get_build_paths
from cloudharness_utils.testing.util import get_app_environment

HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')
ROOT = dn(dn(dn(HERE)).replace(os.path.sep, '/'))

E2E_TESTS_PROJECT_ROOT = os.path.abspath(E2E_TESTS_PROJECT_PATH) if os.path.exists(
    E2E_TESTS_PROJECT_PATH) else os.path.join(ROOT, E2E_TESTS_PROJECT_PATH)

def run_e2e_tests(root_paths, helm_values, base_domain, included_applications=[], headless=False):

    if which("npm") is None:
        logging.error("npm is required to run end to end tests")
        exit(127)

    node_modules_path = os.path.join(E2E_TESTS_PROJECT_ROOT, "node_modules")
    if not os.path.exists(node_modules_path):
            logging.info("Installing Jest-Puppeteer base project")
            subprocess.run(["npm", "install"], cwd=E2E_TESTS_PROJECT_ROOT)

    artifacts = get_build_paths(
            helm_values=helm_values, root_paths=root_paths)

    failed = False
    for appkey in helm_values.apps:
        app_config: ApplicationHarnessConfig = helm_values.apps[appkey].harness

        appname = app_config.name
            
        if included_applications and appname not in included_applications:
            continue
        if not app_config.test.e2e.enabled:
            continue

        tests_dir = os.path.join(
                artifacts[appkey.replace("_", "-")], "test", E2E_TESTS_DIRNAME)
        
        if not app_config.domain and not app_config.subdomain:
            logging.warn(
                    "Application %s has a test folder but no subdomain/domain is specified", appname)
            continue

        app_domain = f"http{'s' if helm_values.tls else ''}://" + \
                (app_config.domain or f"{app_config.subdomain}.{base_domain}")
       
        
        
        env = get_app_environment(app_config, app_domain)
        if not headless and os.environ.get('DISPLAY'):
            env["PUPPETEER_DISPLAY"] = "display"
        if os.path.exists(tests_dir):
            
            app_node_modules_path = os.path.join(tests_dir, "node_modules")
            if not os.path.exists(app_node_modules_path):
                logging.info("Linking tests libraries to  %s",
                                app_node_modules_path)
                os.symlink(node_modules_path, app_node_modules_path)
            env["APP"] = artifacts[appkey.replace("_", "-")]

        logging.info(
                "Running tests for application %s on domain %s", appname, app_domain)
        result = subprocess.run(["npm", "run", "test:app"],
                           cwd=E2E_TESTS_PROJECT_ROOT, env=env)

        if result.returncode > 0:
            failed = True
    if failed:
        logging.error("Some end to end test failed. Check output for more information.")
        exit(1)