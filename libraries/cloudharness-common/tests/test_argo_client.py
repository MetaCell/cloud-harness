"""Exercise the installed Argo SDK across CloudHarness's REST boundary."""
import copy
import json
from unittest.mock import Mock

import pytest
from argo_workflows import Configuration, exceptions
from argo_workflows.rest import RESTResponse
from urllib3 import HTTPResponse

from cloudharness.workflows import argo_service, operations, tasks
from .test_env import set_test_environment

set_test_environment()


@pytest.fixture
def api(monkeypatch):
    client = argo_service.ApiClient(Configuration(host="http://127.0.0.1:2746"))
    monkeypatch.setattr(argo_service, "get_api_client", lambda: client)
    monkeypatch.setattr(argo_service, "namespace", "argo-sdk-test")

    def respond(payload):
        transport = Mock(return_value=RESTResponse(HTTPResponse(
            body=json.dumps(payload).encode(), status=200,
            headers={"Content-Type": "application/json"})))
        monkeypatch.setattr(client.rest_client, "request", transport)
        return transport

    yield respond, client
    client.close()


@pytest.fixture
def workflow():
    return {
        "apiVersion": "argoproj.io/v1alpha1", "kind": "Workflow",
        "metadata": {"name": "sdk-test", "creationTimestamp": "2026-10-28T00:00:00Z"},
        "spec": {},
        "status": {"phase": "Running", "finishedAt": None, "nodes": {
            "sdk-test": {"id": "sdk-test", "name": "sdk-test", "type": "Pod",
                         "phase": "Running", "progress": "2/4", "finishedAt": None}
        }},
    }


def test_submit_preserves_raw_workflow_and_future_fields(api, workflow):
    respond, _ = api
    transport = respond(workflow)
    task = tasks.CustomTask("main", "busybox", command=["sh", "-c", "echo done"])
    spec = operations.SingleTaskOperation("sdk-test-", task).to_workflow()
    spec["spec"]["futureArgoSetting"] = {"enabled": True}
    before = copy.deepcopy(spec)

    result = argo_service.submit_workflow(spec)

    assert result.name == "sdk-test"
    assert spec == before
    assert transport.call_args.kwargs["body"]["workflow"] == spec
    assert transport.call_args.args[0] == "POST"


def test_running_response_keeps_native_progress_and_optional_fields(api, workflow):
    respond, _ = api
    respond(workflow)

    result = argo_service.get_workflow("sdk-test")

    assert result.status == "Running"
    assert result.raw.status.nodes["sdk-test"].progress == "2/4"
    assert result.raw.status.nodes["sdk-test"].finished_at is None
    assert result.raw.status.nodes["sdk-test"].children is None
    assert result.raw.status.outputs is None
    assert result.pod_names == ["sdk-test"]
    assert not result.is_finished()
    assert result.create_time.year == 2026


def test_new_workflow_can_omit_status(api, workflow):
    respond, _ = api
    workflow.pop("status")
    respond(workflow)

    result = argo_service.get_workflow("sdk-test")

    assert result.status is None
    assert result.raw.status is None


def test_list_preserves_pagination_filters_and_partial_responses(api, workflow):
    respond, _ = api
    workflow.pop("spec")
    transport = respond({"items": [workflow], "metadata": {"continue": "next-page"}})

    result = argo_service.get_workflows(
        status="Running", limit=2, continue_token="previous-page",
        field_selector="metadata.name=sdk-test", fields="metadata,items.metadata,items.status")

    assert result.items[0].name == "sdk-test"
    assert result.items[0].status == "Running"
    assert result.items[0].raw.spec is None
    assert result.continue_token == "next-page"
    query = dict(transport.call_args.kwargs["query_params"])
    assert query["listOptions.limit"] == "2"
    assert query["listOptions.continue"] == "previous-page"
    assert query["listOptions.labelSelector"] == "workflows.argoproj.io/phase=Running"
    assert query["listOptions.fieldSelector"] == "metadata.name=sdk-test"
    assert query["fields"] == "metadata,items.metadata,items.status"


def test_empty_list_omits_items_and_continue_token(api):
    respond, _ = api
    respond({"metadata": {}})

    result = argo_service.get_workflows()

    assert not result.items
    assert result.continue_token is None


def test_failed_workflow_preserves_cloudharness_exception(api, workflow):
    respond, _ = api
    workflow["status"].update(phase="Failed", message="container exited with code 7")
    respond(workflow)

    with pytest.raises(argo_service.WorkflowException) as caught:
        argo_service.get_workflow("sdk-test")
    assert caught.value.status == "Workflow failed: container exited with code 7"


@pytest.mark.parametrize("action", ["get", "delete"])
def test_not_found_preserves_cloudharness_exception(api, monkeypatch, action):
    _, client = api
    error = exceptions.ApiException(status=404, reason="Not Found")
    error.body = b"not found"
    monkeypatch.setattr(client.rest_client, "request", Mock(side_effect=error))

    with pytest.raises(argo_service.WorkflowNotFound):
        getattr(argo_service, f"{action}_workflow")("missing")


def test_delete_preserves_zero_grace_period(api):
    respond, _ = api
    transport = respond({})

    argo_service.delete_workflow("sdk-test")

    assert transport.call_args.args[0] == "DELETE"
    assert dict(transport.call_args.kwargs["query_params"])["deleteOptions.gracePeriodSeconds"] == "0"


def test_list_failure_preserves_cloudharness_exception(api, monkeypatch):
    _, client = api
    error = exceptions.ApiException(status=403, reason="Forbidden")
    error.body = b"denied"
    monkeypatch.setattr(client.rest_client, "request", Mock(side_effect=error))

    with pytest.raises(argo_service.WorkflowException, match="denied") as caught:
        argo_service.get_workflows()
    assert caught.value.status == 400


def test_argo_numeric_int_or_string_fields_remain_readable(api, workflow):
    respond, _ = api
    workflow["spec"] = {"activeDeadlineSeconds": 300, "templates": [
        {"name": "main", "retryStrategy": {"limit": 0},
         "container": {"image": "busybox", "resources": {"limits": {"cpu": 1}}}},
    ]}
    respond(workflow)

    result = argo_service.get_workflow("sdk-test")

    assert result.raw.spec.active_deadline_seconds == 300
    assert result.raw.spec.templates[0].retry_strategy.limit == "0"
    assert result.raw.spec.templates[0].container.resources.limits["cpu"] == "1"
