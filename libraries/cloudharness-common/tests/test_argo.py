import os

import yaml
from .test_env import HERE, set_test_environment

from argo_workflows.api.workflow_service_api import IoArgoprojWorkflowV1alpha1Workflow

set_test_environment()

from cloudharness.utils.config import CloudharnessConfig
from cloudharness.workflows import argo


assert 'registry' in CloudharnessConfig.get_configuration()

def test_submit():
    with open(os.path.join(HERE, "wf.yaml")) as f:
        wfy = yaml.safe_load(f)
        wfd = dict(wfy)
    wf = IoArgoprojWorkflowV1alpha1Workflow._new_from_openapi_data(**wfd, _check_type=False)
    w = argo.submit_workflow(wf)

    assert "hello-world-" in w.name

    wg = argo.get_workflow(w.name)
    assert wg

    wfs = argo.get_workflows()