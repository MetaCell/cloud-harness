import os
from pprint import pprint
import schemathesis as st
from schemathesis.checks import response_schema_conformance, not_a_server_error

from cloudharness_test import apitest_init # include to perform default authorization

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

schema = st.from_uri(app_url + "/openapi.json")


@schema.parametrize(endpoint="/ping")
def test_ping(case):
    response = case.call()
    pprint(response.__dict__)
    assert response.status_code == 200, "this api errors on purpose"

