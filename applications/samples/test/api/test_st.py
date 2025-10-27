import os
from pprint import pprint
import schemathesis as st
from schemathesis.specs.openapi.checks import response_schema_conformance

from cloudharness_test import apitest_init  # include to perform default authorization

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

schema = st.openapi.from_url(app_url + "/openapi.json")


@schema.include(path="/error", method="GET").parametrize()
def test_api(case):
    try:
        response = case.call()
        debug_info = (
            f"[DEBUG] Request URL: {getattr(response.request, 'url', None)}\n"
            f"[DEBUG] Request method: {getattr(response.request, 'method', None)}\n"
            f"[DEBUG] Response status: {getattr(response, 'status_code', None)}\n"
            f"[DEBUG] Response headers: {dict(getattr(response, 'headers', {}))}\n"
            f"[DEBUG] Response body: {getattr(response, 'text', None)}\n"
        )
        print(debug_info)
        assert response.status_code >= 500, "this api errors on purpose"
    except Exception as e:
        # Print debug info even if assertion fails
        if 'response' in locals():
            print("[EXCEPTION DEBUG] Request URL:", getattr(response.request, 'url', None))
            print("[EXCEPTION DEBUG] Request method:", getattr(response.request, 'method', None))
            print("[EXCEPTION DEBUG] Response status:", getattr(response, 'status_code', None))
            print("[EXCEPTION DEBUG] Response headers:", dict(getattr(response, 'headers', {})))
            print("[EXCEPTION DEBUG] Response body:", getattr(response, 'text', None))
        print("[EXCEPTION]", e)
        raise


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
