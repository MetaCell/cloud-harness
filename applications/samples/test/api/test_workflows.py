"""Exercise sample workflows through the deployed application and workflows APIs."""
import os
from pathlib import Path
import time
from urllib.parse import quote

import pytest
import requests

APP_URL = os.environ.get("APP_URL", "").rstrip("/")
TIMEOUT = int(os.environ.get("SAMPLES_WORKFLOW_TIMEOUT", "240"))
pytestmark = pytest.mark.skipif(not APP_URL, reason="APP_URL must identify a dedicated samples test deployment")


@pytest.fixture(scope="module")
def api():
    from cloudharness.auth import get_token
    from cloudharness.utils.env import get_cloudharness_workflows_service_url

    with requests.Session() as session:
        if os.environ.get("USERNAME") and os.environ.get("PASSWORD"):
            token = get_token(os.environ["USERNAME"], os.environ["PASSWORD"])
            session.headers["Authorization"] = f"Bearer {token}"
            session.cookies.set("kc-access", token)
        workflows_url = os.environ.get("WORKFLOWS_API_URL")
        if not workflows_url:
            workflows_url = get_cloudharness_workflows_service_url().rstrip("/") + "/api"
        yield session, workflows_url.rstrip("/")


def response_json(response, expected=200):
    assert response.status_code == expected, f"HTTP {response.status_code}: {response.text[:2000]}"
    return response.json()


def operation_url(api, name):
    return api[1] + "/operations/" + quote(name, safe="")


def result_workflow_names(api):
    session, base = api
    names = set()
    # The workflows API defaults to Pending when status is omitted.
    for phase in ("Pending", "Running", "Succeeded", "Failed", "Error", "Skipped"):
        token = None
        while True:
            params = {"limit": 50, "status": phase}
            if token:
                params["previous_search_token"] = token
            page = response_json(session.get(base + "/operations", params=params, timeout=30))
            names.update(item["name"] for item in page.get("items", [])
                         if item["name"].startswith("test-sync-op-results-"))
            token = (page.get("meta") or {}).get("continueToken")
            if not token:
                break
    return names


@pytest.fixture
def workflows(api, tmp_path):
    """Retain diagnostics and delete workflows created by this test."""
    session, _ = api
    before = result_workflow_names(api)
    names = set()
    yield names
    # The sum endpoint returns the result, rather than its workflow name.
    names.update(result_workflow_names(api) - before)
    evidence = Path(os.environ.get("SAMPLES_WORKFLOW_EVIDENCE", tmp_path))
    evidence.mkdir(parents=True, exist_ok=True)
    for name in names:
        url = operation_url(api, name)
        try:
            status = session.get(url, timeout=30)
            (evidence / f"{name}.json").write_text(status.text)
            logs = session.get(url + "/logs", timeout=30)
            (evidence / f"{name}.log").write_text(logs.text)
        except requests.RequestException as error:
            (evidence / f"{name}.error").write_text(str(error))
        deleted = session.delete(url, timeout=30)
        assert deleted.status_code in (200, 204, 404), deleted.text


def wait_for_success(api, name):
    session, _ = api
    deadline = time.monotonic() + TIMEOUT
    while time.monotonic() < deadline:
        operation = response_json(session.get(operation_url(api, name), timeout=30))
        phase = operation.get("status")
        if phase in ("Succeeded", "Failed", "Error", "Skipped"):
            assert phase == "Succeeded", f"{name}: {phase}: {operation.get('message')}"
            assert operation["workflow"]
            return operation
        time.sleep(2)
    pytest.fail(f"{name} did not complete within {TIMEOUT}s")


def test_async_workflow_reads_the_shared_file(api, workflows):
    session, _ = api
    body = response_json(session.get(APP_URL + "/operation_async", timeout=(10, TIMEOUT)), expected=202)
    name = body["task"]["name"]
    workflows.add(name)
    assert body["task"]["href"].rstrip("/").endswith("/operations/" + name)
    wait_for_success(api, name)
    logs = session.get(operation_url(api, name) + "/logs", timeout=30)
    assert logs.status_code == 200, logs.text
    assert "Displaying content for file" in logs.text


def test_sync_workflow_returns_a_completed_workflow(api, workflows):
    session, _ = api
    workflow = response_json(session.get(APP_URL + "/operation_sync", timeout=(10, TIMEOUT)))
    name = workflow["metadata"]["name"]
    workflows.add(name)
    assert workflow["status"]["phase"] == "Succeeded", workflow["status"]
    assert workflow["status"].get("finishedAt") or workflow["status"].get("finished_at")
    assert wait_for_success(api, name)["status"] == "Succeeded"


@pytest.mark.parametrize("a,b,expected", [(2, 3, 5), (-4, 1, -3)])
def test_sync_workflow_returns_the_queue_result(api, workflows, a, b, expected):
    session, _ = api
    result = response_json(session.get(APP_URL + "/operation_sync_results",
                                       params={"a": a, "b": b}, timeout=(10, TIMEOUT)))
    assert float(result) == expected
