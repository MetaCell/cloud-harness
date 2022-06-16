import os
from pprint import pprint
import schemathesis as st
from schemathesis.checks import response_schema_conformance, not_a_server_error

from cloudharness.testing import apitest_init # include to perform default authorization

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

schema = st.from_uri(app_url + "/openapi.json")


@schema.parametrize(endpoint="/error")
def test_api(case):
    response = case.call()
    pprint(response.__dict__)
    assert response.status_code >= 500, "this api errors on purpose"

@schema.parametrize(endpoint="/valid")
def test_bearer(case):
    response = case.call()
    
    case.validate_response(response, checks=(response_schema_conformance,))

@schema.parametrize(endpoint="/valid-cookie")
def test_cookie(case):
    response = case.call()
    case.validate_response(response, checks=(response_schema_conformance,))

@schema.parametrize(endpoint="/sampleresources", method="POST")
def test_response(case):
    response = case.call()
    case.validate_response(response, checks=(response_schema_conformance,))