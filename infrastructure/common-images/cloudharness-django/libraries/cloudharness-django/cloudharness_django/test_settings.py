# Minimal settings to run the library tests (no Keycloak, no Kafka):
#   python -m django test cloudharness_django --settings=cloudharness_django.test_settings
SECRET_KEY = "test"
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "cloudharness_django"]
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True

# read at import time by cloudharness_django.services
KC_CLIENT_NAME = "test-client"
KC_ALL_ROLES = ["administrator", "standard"]
KC_PRIVILEGED_ROLES = ["administrator"]
KC_ADMIN_ROLE = "administrator"
KC_DEFAULT_USER_ROLE = "standard"
