import os
import schemathesis as st
from cloudharness_test import apitest_init  # include to register default hooks
from cloudharness_test import apitest_auth_hooks  # include to register authentication hooks

app_url = os.environ.get("APP_URL", "http://samples.ch.local/api")

schema = st.openapi.from_url(app_url + "/openapi.json")


@schema.include(path="/ping", method="GET").parametrize()
def test_ping(case):
    response = case.call()
    assert response.status_code == 200, "this api errors on purpose"
