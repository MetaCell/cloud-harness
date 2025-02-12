"""
ASGI config for the MNP Checkout project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_baseapp.settings")

application = get_asgi_application()

# init the auth service
from cloudharness_django.services import init_services  # noqa E402

init_services()

# start the kafka event listener
from cloudharness_django.services.events import init_listener  # noqa E402

init_listener()
