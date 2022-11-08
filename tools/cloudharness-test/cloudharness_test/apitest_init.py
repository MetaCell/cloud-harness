import os
import logging

import schemathesis as st

from cloudharness.auth import get_token

if "APP_URL" in os.environ:

    app_url = os.environ["APP_URL"]

    try:
        openapi_uri = app_url + "/openapi.json"
        logging.info("Using openapi spec at %s", openapi_uri)
        schema = st.from_uri(openapi_uri)
    except Exception as e:
        raise Exception(f"Cannot setup api tests: {openapi_uri} not reachable. Check your deployment is up and configuration") from e

    if "USERNAME" in os.environ and "PASSWORD" in os.environ:
        logging.info("Setting token from username and password")
        @st.auth.register()
        class TokenAuth:
            def get(self, context):
                
                username = os.environ["USERNAME"]
                password = os.environ["PASSWORD"]  
        
                return get_token(username, password)

            def set(self, case, data, context):
                case.headers = case.headers or {}
                case.headers["Authorization"]  = f"Bearer {data}"
                case.headers["Cookie"]  = f"kc-access={data}"
    else:
        @st.auth.register()
        class TokenAuth:
            def get(self, context):
                
                return ""

            def set(self, case, data, context):
                case.headers = case.headers or {}
                case.headers["Authorization"]  = f"Bearer {data}"
                case.headers["Cookie"]  = f"kc-access={data}"