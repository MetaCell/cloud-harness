from django.apps import AppConfig


class cloudharness_djangoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cloudharness_django'

    def ready(self):
        # imports
        import sys
        for skip_cmd in [
            "--help",
            "collectstatic",
            "compilemessages",
            "compress",
            "dbshell",
            "dumpdata",
            "loaddata",
            "makemessages",
            "makemigrations",
            "migrate",
            "reset_db",
            "showmigrations",
            "sqlmigrate",
            "squashmigrations",
            "test",
        ]:
            # for these commands we skip initializing the event listener
            if skip_cmd in sys.argv:
                return

        from cloudharness_django.services.events import init_listener_in_background
        init_listener_in_background()
