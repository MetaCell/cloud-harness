import pytest
import yaml
from cloudharness.utils.env import *






def test_variables():
    os.environ['CH_USE_PUBLIC'] = "False"
    assert 'CH_DOMAIN' in os.environ

    assert get_variable('CH_DOMAIN') == 'cloudharness.metacell.us'
    assert get_sub_variable('CH_DOCS', 'NAME') == 'ch-docs'
    assert get_sub_variable('CH-docs', 'NAME') == 'ch-docs'
    assert get_sub_variable('CH_DOCS', 'IMAGE_NAME') == 'ch-docs'

    assert get_sub_variable('CH_DOCS', 'PORT') == '8080'

    assert get_image_registry() == 'localhost:5000'
    assert get_auth_service_url() == 'accounts.cloudharness.metacell.us'
    assert get_auth_service_cluster_address() == 'keycloak:8080'
    assert get_cloudharness_events_client_id() == 'web-client'
    assert get_cloudharness_workflows_service_url() == 'workflows.cloudharness.metacell.us'
    assert get_image_full_tag('workflows-extract-download') == 'localhost:5000/workflows-extract-download:latest'

    with pytest.raises(VariableNotFound) as raised:
        get_variable('CH_FAKE')

    assert raised.value.variable_name == 'CH_FAKE'
