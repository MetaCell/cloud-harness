"""
WSGI config for the __APP_NAME__ project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_baseapp.settings")

application = get_wsgi_application()

# init the auth service
from cloudharness_django.services import init_services  # noqa E402

init_services()

# start the kafka event listener
from cloudharness_django.services.events import init_listener  # noqa E402

init_listener()
