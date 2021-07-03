#!/usr/bin/env python3

from cloudharness.utils.server import init_flask, main
from .services.event_service import setup_event_service


def init_notifications(app):
    # start event services listeners for the, in the values.yaml, defined notifications
    setup_event_service()

app = init_flask(title="notifications", init_app_fn=init_notifications, webapp=False)

if __name__ == '__main__':
    main()

