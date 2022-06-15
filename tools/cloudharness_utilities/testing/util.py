from cloudharness.auth import get_token
from cloudharness.utils.config import CloudharnessConfig
from cloudharness_utilities.preprocessing import get_build_paths
from cloudharness_model.models import ApplicationUser, HarnessMainConfig, ApiTestsConfig, ApplicationConfig, ApplicationHarnessConfig
import os
from os.path import dirname as dn

def get_user_password(main_user: ApplicationUser):
    return main_user.password or "test"

def get_app_environment(app_config, app_domain, use_local_env=True):
    my_env = os.environ.copy() if use_local_env else {}
    my_env["APP_URL"] = app_domain

    if app_config.accounts and app_config.accounts.users:
        main_user: ApplicationUser = app_config.accounts.users[0]
        password = get_user_password(main_user)
        my_env["USERNAME"] = main_user.username
        my_env["PASSWORD"] = password

    return my_env