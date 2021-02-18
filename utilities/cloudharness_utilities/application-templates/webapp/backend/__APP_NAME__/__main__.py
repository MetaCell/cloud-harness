#!/usr/bin/env python3

from cloudharness.utils.server import init_flask, main


init_flask(title="__APP_NAME__", init_app_fn=None, webapp=True)

if __name__ == '__main__':
    main()

