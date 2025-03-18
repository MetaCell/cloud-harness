import os
import logging
import schemathesis as st
from schemathesis.hooks import HookContext

from cloudharness.auth import get_token

st.experimental.OPEN_API_3_1.enable()

if "APP_URL" or "APP_SCHEMA_FILE" in os.environ:
    app_schema = os.environ.get("APP_SCHEMA_FILE", None)
    app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")
    logging.info("Start schemathesis tests on %s", app_url)

    schema = None

    # First, attempt to load the local file if provided
    if app_schema:
        try:
            schema = st.from_file(app_schema)
            logging.info("Successfully loaded schema from local file: %s", app_schema)
        except st.exceptions.SchemaError:
            logging.exception("The local schema file %s cannot be loaded. Attempting loading from URL", app_schema)

    # If no schema from file, then loop over URL candidates
    if not schema:
        candidates = [
            app_url.rstrip("/") + "/openapi.json",
            app_url.rstrip("/") + "/api/openapi.json",
        ]
        for candidate in candidates:
            try:
                logging.info("Attempting to load schema from URI: %s", candidate)
                schema = st.from_uri(candidate)
                logging.info("Successfully loaded schema from %s", candidate)
                break  # Exit loop on successful load
            except st.exceptions.SchemaError as e:
                logging.warning("Failed to load schema from %s: %s", candidate, e)
            except Exception as e:
                logging.error("Unexpected error when loading schema from %s: %s", candidate, e)
        if not schema:
            raise Exception("Cannot setup API tests: No valid schema found. Check your deployment and configuration.")

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

    UNSAFE_VALUES = ("%", )

    @st.hook
    def filter_path_parameters(context: HookContext, x):
        # Extract the candidate value.
        param = x["key"] if isinstance(x, dict) and "key" in x else x

        if param is None or param == "":
            return True

        param_str = str(param)

        # Reject if any unsafe substring is present.
        if any(unsafe in param_str for unsafe in UNSAFE_VALUES):
            return False

        return True
