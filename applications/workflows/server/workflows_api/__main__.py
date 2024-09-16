#!/usr/bin/env python3

from cloudharness.utils.server import init_flask, main

app = init_flask()

if __name__ == '__main__':
    main()
