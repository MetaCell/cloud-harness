
import os
from os.path import dirname as dn

from cloudharness_model.models import ApplicationUser, ApplicationTestConfig, ApplicationHarnessConfig, E2ETestsConfig


def get_user_password(main_user: ApplicationUser):
    return main_user.password or "test"


def get_app_environment(app_config: ApplicationHarnessConfig, app_domain, use_local_env=True):
    my_env = os.environ.copy() if use_local_env else {}
    my_env["APP_URL"] = app_domain

    if app_config.accounts and app_config.accounts.users:
        main_user: ApplicationUser = app_config.accounts.users[0]
        password = get_user_password(main_user)
        my_env["USERNAME"] = main_user.username
        my_env["PASSWORD"] = password
    test_config: ApplicationTestConfig = app_config.test
    e2e_config: E2ETestsConfig = test_config.e2e
    if not e2e_config.smoketest:
        my_env["SKIP_SMOKETEST"] = "true"
    if e2e_config.ignoreConsoleErrors:
        my_env["IGNORE_CONSOLE_ERRORS"] = "true"
    if e2e_config.ignoreRequestErrors:
        my_env["IGNORE_REQUEST_ERRORS"] = "true"
    return my_env
