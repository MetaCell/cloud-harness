"""Opt-in CloudHarness/Emissary smoke test on Docker Desktop only."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlparse


@unittest.skipUnless(os.environ.get("ARGO_SMOKE_URL"), "set ARGO_SMOKE_URL for the local Kubernetes smoke test")
class EmissaryIntegrationTests(unittest.TestCase):
    def test_cloudharness_contract_and_live_progress(self):
        url = os.environ["ARGO_SMOKE_URL"]
        self.assertEqual(urlparse(url).hostname, "127.0.0.1")
        namespace = os.environ["ARGO_SMOKE_NAMESPACE"]
        self.assertTrue(namespace.startswith("argo-"))
        kube = ["kubectl", "--context", "docker-desktop", "-n", namespace]
        settings = json.loads(subprocess.check_output(kube + ["config", "view", "--minify", "--raw", "-o", "json"]))
        self.assertEqual(urlparse(settings["clusters"][0]["cluster"]["server"]).hostname, "127.0.0.1")
        with tempfile.TemporaryDirectory() as folder:
            config_file = Path(folder) / "kubeconfig.json"
            config_file.write_text(json.dumps(settings))
            config_file.chmod(0o600)
            values_file = Path(folder) / "values.json"
            values_file.write_text(json.dumps({"namespace": namespace, "apps": {}, "task-images": {},
                                               "registry": {"name": "", "secret": {}}}))
            with patch.dict(os.environ, {"KUBECONFIG": str(config_file), "CH_VALUES_PATH": str(values_file)}):
                self.exercise(kube, namespace, url)

    def exercise(self, kube, namespace, url):
        from argo.workflows.client import Configuration
        from cloudharness.utils.config import CloudharnessConfig
        from cloudharness.workflows import argo_service, operations, tasks
        CloudharnessConfig.allvalues = {"namespace": namespace, "apps": {}, "task-images": {},
                                        "registry": {"name": "", "secret": {}}}
        image = os.environ.get("ARGO_SMOKE_IMAGE", "busybox:1.37")
        created = []
        evidence = {"progress": [], "results": {}}

        def snapshot(name):
            return json.loads(subprocess.check_output(kube + ["get", "workflow", name, "-o", "json"]))

        def submit(command, args=None, progress=False):
            task = tasks.CustomTask("run", image, command=command, retry_limit=0)
            operation = operations.SingleTaskOperation("emissary-contract-", task, ttl_strategy=None)
            workflow = operation.to_workflow()
            spec = workflow["spec"]
            spec["serviceAccountName"] = os.environ.get("ARGO_SMOKE_SERVICE_ACCOUNT", "emissary-executor")
            spec["podGC"] = {"strategy": "OnWorkflowSuccess", "deleteDelayDuration": "600s"}
            template = next(item for item in spec["templates"] if item["name"] == "run")
            if args:
                template["container"]["args"] = args
            if progress:
                template["outputs"] = {"parameters": [{"name": "result", "globalName": "result",
                                                       "valueFrom": {"path": "/tmp/result.json"}}]}
            spec["onExit"] = "exit-handler"
            spec["templates"].append({"name": "exit-handler", "container": {
                "image": image, "command": ["sh", "-c"], "args": ["echo EXIT={{workflow.status}}"]}})
            result = argo_service.submit_workflow(workflow)
            created.append(result.name)
            return result.name

        def wait(name):
            deadline = time.monotonic() + 360
            while time.monotonic() < deadline:
                raw = snapshot(name)
                # This is the same REST Workflow object consumed by applications, not a TaskResult lookup.
                workflow = next((item for item in argo_service.get_workflows(limit=100).items if item.name == name), None)
                self.assertIsNotNone(workflow)
                if raw.get("status", {}).get("phase") in ("Succeeded", "Failed", "Error"):
                    evidence["results"][name] = raw["status"]
                    return raw
                for node in (workflow.raw.status.nodes or {}).values() if workflow.raw.status else []:
                    ratio = getattr(node, "progress", None)
                    if node.type == "Pod" and node.phase == "Running" and ratio in ("1/10", "7/10"):
                        evidence["progress"].append(ratio)
                time.sleep(3)
            self.fail(f"Workflow did not finish: {name}")

        with patch.object(argo_service, "namespace", namespace), patch.object(
                argo_service, "get_configuration", return_value=Configuration(host=url)):
            try:
                name = submit(["sh", "-c"], [
                    'echo 1/10 > "$ARGO_PROGRESS_FILE"; echo START; sleep 75; '
                    'echo 7/10 > "$ARGO_PROGRESS_FILE"; sleep 75; '
                    "echo '{\"ok\":true}' > /tmp/result.json; echo DONE"], progress=True)
                raw = wait(name)
                self.assertEqual(raw["status"]["phase"], "Succeeded")
                self.assertTrue({"1/10", "7/10"}.issubset(evidence["progress"]))
                result = argo_service.get_workflow(name)
                self.assertTrue(result.succeeded() and result.is_finished())
                self.assertEqual(json.loads(result.raw.status.outputs.parameters[0].value), {"ok": True})
                self.assertTrue(any(node.name.endswith(".onExit") and node.phase == "Succeeded"
                                    for node in result.raw.status.nodes.values()))
                self.assertIn("DONE", argo_service.get_workflow_logs(name))
                self.assertTrue(result.pod_names)
                self.assertTrue(all(subprocess.run(kube + ["get", "pod", pod], capture_output=True).returncode == 0
                                    for pod in result.pod_names))
                failed = submit(["sh", "-c"], ["echo EXPECTED_FAILURE; exit 7"])
                raw = wait(failed)
                self.assertEqual(raw["status"]["phase"], "Failed")
                self.assertTrue(any(node["name"].endswith(".onExit") and node["phase"] == "Succeeded"
                                    for node in raw["status"]["nodes"].values()))
                with self.assertRaises(argo_service.WorkflowException):
                    argo_service.get_workflow(failed)
                # No command: preserve image ENTRYPOINT/CMD resolution, used by standard CloudHarness tasks.
                implicit = submit(None, ["echo", "ENTRYPOINT_OK"])
                self.assertEqual(wait(implicit)["status"]["phase"], "Succeeded")
                self.assertIn("ENTRYPOINT_OK", argo_service.get_workflow_logs(implicit))
                cancelled = submit(["sh", "-c"], ["sleep 300"])
                argo_service.delete_workflow(cancelled)
                with self.assertRaises(argo_service.WorkflowNotFound):
                    argo_service.get_workflow(cancelled)
            finally:
                if os.environ.get("ARGO_SMOKE_EVIDENCE"):
                    Path(os.environ["ARGO_SMOKE_EVIDENCE"]).write_text(json.dumps(evidence, indent=2))
                for name in created:
                    subprocess.run(kube + ["delete", "workflow", name, "--ignore-not-found", "--wait=false"],
                                   capture_output=True)
