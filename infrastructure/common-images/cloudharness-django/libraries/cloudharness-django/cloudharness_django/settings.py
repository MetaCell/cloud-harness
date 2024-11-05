import os
from django.conf import settings


# ***********************************************************************
# * CloudHarness Django settings
# ***********************************************************************
from cloudharness import applications, log
from cloudharness.utils.config import CloudharnessConfig as conf

# add the 3rd party apps
INSTALLED_APPS = getattr(
    settings,
    'INSTALLED_APPS',
    []) + ['admin_extra_buttons', ]

# add the local apps
INSTALLED_APPS += ['cloudharness_django', ]

# add the CloudHarness Django auto login middleware
MIDDLEWARE = getattr(
    settings,
    'MIDDLEWARE',
    []
) + [
    'cloudharness_django.middleware.BearerTokenMiddleware',
]

USER_CHANGE_ENABLED = False

# test if the kubernetes CH all values exists, if so then set up specific k8s stuff
# IMPROTANT NOTE:
#   when testing/debugging with Kafka then copy the deployment/helm/values.yaml to the ALLVALUES_PATH
#   see also the README.md

# get the application CH config
app_name = settings.PROJECT_NAME.lower()
try:
    current_app = applications.get_current_configuration()

    # if secured then set USE_X_FORWARDED_HOST because we are behind the GK proxy
    USE_X_FORWARDED_HOST = current_app.harness.secured

    # CSRF, set CSRF_TRUSTED_ORIGINS
    CH_DOMAIN = conf.get_domain()
    CSRF_TRUSTED_ORIGINS = getattr(
        settings,
        'CSRF_TRUSTED_ORIGINS',
        []) + [f"https://{CH_DOMAIN}", f"https://*.{CH_DOMAIN}"]
except:
    # no current app found, fall back to the default settings, there is a god change that
    # we are running on a developers local machine
    log.warning("Error setting current app configuration, continuing...")

    current_app = applications.ApplicationConfiguration({
        "name": app_name,
        "harness": {
            "database": {
                "name": app_name,
                "type": "sqlite3",
                "host": None,
            }
        }
    })
    # CSRF
    CSRF_TRUSTED_ORIGINS = ["http://localhost:8080"]

if current_app.harness.database.type == "sqlite3":
    DATABASE_ENGINE = "django.db.backends.sqlite3"
    DATABASE_NAME = os.path.join(getattr(settings, "PERSISTENT_ROOT", "."), f"{app_name}.sqlite3")
    DATABSE_HOST = None
    DATABASE_PORT = None
elif current_app.harness.database.type == "postgres":
    DATABASE_ENGINE = "django.db.backends.postgresql"
    DATABASE_NAME = current_app.harness.database.postgres.initialdb
    DATABSE_HOST = current_app.harness.database.name
    DATABASE_PORT = current_app.harness.database.postgres.ports[0].port

# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": DATABASE_ENGINE,
        "NAME": DATABASE_NAME,
        "USER": getattr(current_app.harness.database, "user", None),
        "PASSWORD": getattr(current_app.harness.database, "pass", None),
        "HOST": DATABSE_HOST,
        "PORT": DATABASE_PORT,
        "TEST": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(getattr(settings, "PERSISTENT_ROOT", "."), "testdb.sqlite3"),
        },
    },
}
