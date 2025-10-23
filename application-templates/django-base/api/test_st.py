import os
from pprint import pprint
import schemathesis as st
from schemathesis.checks import response_schema_conformance, not_a_server_error

from cloudharness_test import apitest_init  # include to perform default authorization

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

try:
    schema = st.from_uri(app_url + "/openapi.json")
except:
    # support alternative schema location
    schema = st.from_uri(app_url.replace("/api", "") + "/openapi.json")


@schema.include(path="/ping").parametrize()
def test_ping(case):
    response = case.call()
    assert response.status_code == 200, "this api errors on purpose"


def test_state_machine():
    schema.as_state_machine().run()
# APIWorkflow = schema.as_state_machine()
# APIWorkflow.run()
# TestAPI = APIWorkflow.TestCase
