#!/usr/bin/env python3

from cloudharness.utils.server import init_flask, main


init_flask(webapp=True)

if __name__ == '__main__':
    main()
