from django.apps import AppConfig


class cloudharness_djangoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cloudharness_django'

    def ready(self):
        from . import signals  # noqa: F401
