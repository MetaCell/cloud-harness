import os
import schemathesis as st
from cloudharness_test import apitest_init  # include to perform default authorization

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

try:
    schema = st.openapi.from_url(app_url + "/openapi.json")
except:
    # support alternative schema location
    schema = st.openapi.from_url(app_url.replace("/api", "") + "/openapi.json")


@schema.include(path="/ping", method="GET").parametrize()
def test_ping(case):
    response = case.call()
    assert response.status_code == 200, "this api errors on purpose"


def test_state_machine():
    schema.as_state_machine().run()
# APIWorkflow = schema.as_state_machine()
# APIWorkflow.run()
# TestAPI = APIWorkflow.TestCase
