import os
import logging
import requests

import schemathesis as st

from cloudharness.auth import get_token

if "APP_URL" or "APP_SCHEMA_FILE" in os.environ:
    app_schema = os.environ.get("APP_SCHEMA_FILE", None)
    app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")
    logging.info("Start schemathesis tests on %s", app_url)
    schema = None
    if app_schema:
        # Test locally with harness-test -- use local schema for convenience during test development
        openapi_uri = app_schema
        try:
            schema = st.from_file(openapi_uri)
        except st.exceptions.SchemaError:
            logging.exception("The local schema file %s cannot be loaded. Attempting loading from URL", openapi_uri)

    if not schema:
        # remote testing: might be /api/openapi.json or /openapi.json
        try:
            openapi_uri = openapi_uri = app_url + "/openapi.json"
            logging.info("Using openapi spec at %s", openapi_uri)
            schema = st.from_uri(openapi_uri)
        except st.exceptions.SchemaError:
            # Use alternative configuration
            try:
                openapi_uri = app_url.replace("/api", "") + "/openapi.json"
                print(requests.get(openapi_uri))
                schema = st.from_uri(openapi_uri)
            except st.exceptions.SchemaError as e:
                raise Exception(
                    f"Cannot setup api tests: {openapi_uri} not valid. Check your deployment is up and configuration") from e

        except Exception as e:
            raise Exception(
                f"Cannot setup api tests: {openapi_uri}: {e}") from e

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
                case.headers["Authorization"] = f"Bearer {data}"
                case.headers["Cookie"] = f"kc-access={data}"
    else:
        @st.auth.register()
        class TokenAuth:
            def get(self, context):

                return ""

            def set(self, case, data, context):
                case.headers = case.headers or {}
                case.headers["Authorization"] = f"Bearer {data}"
                case.headers["Cookie"] = f"kc-access={data}"
