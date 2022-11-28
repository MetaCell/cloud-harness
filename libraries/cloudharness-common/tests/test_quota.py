from .test_env import set_test_environment

set_test_environment()

from cloudharness import set_debug
from cloudharness.applications import get_configuration
from cloudharness.auth.quota import get_user_quotas

set_debug()

jh_config = get_configuration("jupyterhub")
assert jh_config is not None

def test_get_quotas(mocker):
    def mock_get_admin_client(self):
        return None
    def mock_get_current_user(self):
        return {"id":"123"}
    def mock_get_user(self, user_id, with_details):
        return {
            "attributes": {
                "quota-ws-guaranteemem": [0.5]
            },
            "userGroups": [
                {"path": "/Base", "attributes": {'quota-ws-maxmem': [2.5], 'quota-ws-maxcpu': [1], 'quota-ws-open': [3], "quota-ws-guaranteemem": [0.1]} },
                {"path": "/Base/Base 1/Base 1 1", "attributes": {'quota-ws-maxcpu': [2], 'quota-ws-open': [10]}},
                {"path": "/Base/Base 2", "attributes": {'quota-ws-maxmem': [8], 'quota-ws-maxcpu': [0.25], 'quota-ws-guaranteecpu': [0.25]}},
                {"path": "/Low CU", "attributes": {'quota-ws-maxmem': [3], 'quota-ws-maxcpu': [2.5], 'quota-ws-open': [1]}}
            ]
        }
    mocker.patch('cloudharness.auth.keycloak.AuthClient.get_admin_client', mock_get_admin_client)
    mocker.patch('cloudharness.auth.keycloak.AuthClient.get_current_user', mock_get_current_user)
    mocker.patch('cloudharness.auth.keycloak.AuthClient.get_user', mock_get_user)
    user_quotas_jh = get_user_quotas(jh_config, user_id=None)
    
    assert user_quotas_jh.get("quota-ws-maxmem") == 8.0
    assert user_quotas_jh.get("quota-ws-maxcpu") == 2.5
    assert user_quotas_jh.get("quota-ws-open") == 10.0
    assert user_quotas_jh.get("quota-ws-guaranteecpu") == 0.25
    assert user_quotas_jh.get("quota-ws-guaranteemem") == 0.5
    print(user_quotas_jh)
