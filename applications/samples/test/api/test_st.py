import os
from pprint import pprint
import schemathesis as st
from schemathesis.specs.openapi.checks import response_schema_conformance

from cloudharness_test import apitest_init  # include to perform default authorization

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

schema = st.openapi.from_url(app_url + "/openapi.json")


@schema.include(path="/error", method="GET").parametrize()
def test_api(case):
    response = case.call()
    
    if case.method == "GET":
        # Assert that this endpoint returns a 500 error as expected
        assert response.status_code == 500, f"Expected 500 error, got {response.status_code}. This api errors on purpose."
    elif case.method == "OPTIONS":
        # OPTIONS requests typically return 200 OK
        assert response.status_code == 200, f"Expected 200 OK for OPTIONS, got {response.status_code}."
    else:
        # Other methods should return 405 (Method Not Allowed)
        assert response.status_code == 405, f"Expected 405 (Method Not Allowed) for {case.method}, got {response.status_code}."


@schema.include(path="/valid", method="GET").parametrize()
def test_bearer(case):
    response = case.call()
    case.validate_response(response, checks=(response_schema_conformance,))


@schema.include(path="/valid-cookie", method="GET").parametrize()
def test_cookie(case):
    response = case.call()
    case.validate_response(response, checks=(response_schema_conformance,))


@schema.include(path="/sampleresources", method="POST").parametrize()
def test_response(case):
    response = case.call()
    case.validate_response(response, checks=(response_schema_conformance,))
