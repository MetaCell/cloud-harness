from django.apps import AppConfig


class cloudharness_djangoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cloudharness_django'

    _listener_started = False

    def ready(self):
        import os
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
            if skip_cmd in sys.argv:
                return

        # runserver autoreloader spawns a child; only start in the reloader
        # child (RUN_MAIN=true), not the parent watcher.
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return

        # Opt-out for multi-worker contexts (gunicorn/uWSGI): set
        # CLOUDHARNESS_DISABLE_EVENT_LISTENER=true on web workers and run the
        # consumer in a dedicated process to avoid one consumer per worker.
        if os.environ.get("CLOUDHARNESS_DISABLE_EVENT_LISTENER", "").lower() in ("1", "true", "yes"):
            return

        # Only start the listener when the events (Kafka) service is part of the
        # deployment. Without it there is no broker, so the listener would just
        # crash-loop on NoBrokersAvailable. Treat a missing (or undeterminable)
        # events app as "events disabled" and skip startup entirely.
        try:
            from cloudharness.applications import get_configuration
            get_configuration("events")
        except Exception:
            from cloudharness import log
            log.info(
                "Events service is not part of the deployment; "
                "skipping the Kafka event listener."
            )
            return

        if cloudharness_djangoConfig._listener_started:
            return
        cloudharness_djangoConfig._listener_started = True

        from cloudharness_django.services.events import init_listener_in_background
        init_listener_in_background()
