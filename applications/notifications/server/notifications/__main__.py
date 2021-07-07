#!/usr/bin/env python3

import time
from cloudharness import log
from notifications.services.event_service import setup_event_service


def main():
    setup_event_service()

    nap_time = 30
    while True:
        time.sleep(nap_time)  # sleep xx seconds
        log.info("Running...")


if __name__ == '__main__':
    main()

