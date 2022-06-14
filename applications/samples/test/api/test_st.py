import schemathesis as st
from schemathesis.checks import response_schema_conformance
import os

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

schema = st.from_uri(app_url + "/openapi.json")


@schema.parametrize(endpoint="/operation_sync_results")
def test_api(case):
    response = case.call()
    case.validate_response(response, checks=(response_schema_conformance,))