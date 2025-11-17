import os
import logging
from urllib.parse import urlparse
import schemathesis as st
from schemathesis.hooks import HookContext


if "APP_URL" or "APP_SCHEMA_FILE" in os.environ:
    app_schema = os.environ.get("APP_SCHEMA_FILE", None)
    app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

    parsed_url = urlparse(app_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}".rstrip("/")

    logging.info("Start schemathesis tests on %s", base_url)

    schema = None

    # First, attempt to load the local file if provided
    if app_schema:
        try:
            schema = st.openapi.from_file(app_schema)
            logging.info("Successfully loaded schema from local file: %s", app_schema)
        except st.errors.LoaderError:
            logging.exception("The local schema file %s cannot be loaded. Attempting loading from URL", app_schema)

    # If no schema from file, then loop over URL candidates
    if not schema:
        candidates = [
            base_url + "/openapi.json",
            base_url + "/api/openapi.json",
        ]
        for candidate in candidates:
            try:
                logging.info("Attempting to load schema from URI: %s", candidate)
                schema = st.openapi.from_url(candidate)
                logging.info("Successfully loaded schema from %s", candidate)
                break  # Exit loop on successful load
            except st.errors.LoaderError as e:
                logging.warning("Failed to load schema from %s: %s", candidate, e)
            except Exception as e:
                logging.error("Unexpected error when loading schema from %s: %s", candidate, e)
        if not schema:
            raise Exception("Cannot setup API tests: No valid schema found. Check your deployment and configuration.")

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
