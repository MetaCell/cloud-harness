"""Render the vendored Argo components without changing the harness contract."""
import os
from pathlib import Path
import subprocess
import unittest

import yaml

CHART = Path(__file__).resolve().parents[1] / "deploy" / "charts"
HELM = os.environ.get("HELM", "helm")


class ArgoComponentsTests(unittest.TestCase):
    def render(self, *extra):
        result = subprocess.run(
            [HELM, "template", "argo-contract", str(CHART), "--namespace", "local-test", *extra],
            check=True, capture_output=True, text=True,
        )
        return [obj for obj in yaml.safe_load_all(result.stdout) if obj]

    def test_component_versions_and_legacy_pod_names_are_consistent(self):
        objects = self.render()
        deployments = [obj for obj in objects if obj["kind"] == "Deployment"]
        self.assertEqual(len(deployments), 2)
        for obj in deployments:
            container = obj["spec"]["template"]["spec"]["containers"][0]
            self.assertTrue(container["image"].endswith(":v3.7.18"))
            env = {item["name"]: item.get("value") for item in container["env"]}
            self.assertEqual(env["POD_NAMES"], "v1")
            self.assertNotIn("BASE_HREF", env)
            self.assertNotIn("--pod-workers", container["args"])
        controller = next(obj for obj in deployments if obj["metadata"]["name"].endswith("workflow-controller"))
        self.assertIn("quay.io/argoproj/argoexec:v3.7.18",
                      controller["spec"]["template"]["spec"]["containers"][0]["args"])
        self.assertIn("argo-server", [obj["metadata"]["name"] for obj in objects if obj["kind"] == "Service"])

    def test_config_uses_emissary_and_executor_can_report_native_progress(self):
        objects = self.render("--set", "controller.containerRuntimeExecutor=pns")
        configmap = next(obj for obj in objects if obj["kind"] == "ConfigMap")
        config = yaml.safe_load(configmap["data"]["config"]) or {}
        self.assertNotIn("containerRuntimeExecutor", config)
        self.assertNotIn("containerRuntimeExecutors", config)
        role = next(obj for obj in objects if obj["kind"] == "Role"
                    and obj["metadata"]["name"].endswith("-workflow"))
        rules = [rule for rule in role["rules"] if "workflowtaskresults" in rule.get("resources", [])]
        self.assertTrue(any({"create", "patch"}.issubset(rule["verbs"]) for rule in rules))

    def test_official_release_crds_include_task_results_and_native_progress(self):
        crds = [yaml.safe_load(path.read_text()) for path in (CHART / "crds").glob("*.yaml")]
        self.assertEqual(len(crds), 8)
        by_name = {obj["metadata"]["name"]: obj for obj in crds}
        self.assertIn("workflowartifactgctasks.argoproj.io", by_name)
        self.assertIn("workflowtasksets.argoproj.io", by_name)
        results = by_name["workflowtaskresults.argoproj.io"]
        version = next(item for item in results["spec"]["versions"] if item["name"] == "v1alpha1")
        self.assertTrue(version["served"] and version["storage"])
        self.assertEqual(version["schema"]["openAPIV3Schema"]["properties"]["progress"]["type"], "string")

    def test_custom_image_registry_and_existing_auth_configuration_still_render(self):
        objects = self.render("--set", "controller.image.registry=mirror.example",
                              "--set", "server.extraArgs[0]=--auth-mode=server")
        controller = next(obj for obj in objects if obj["kind"] == "Deployment"
                          and obj["metadata"]["name"].endswith("workflow-controller"))
        self.assertEqual(controller["spec"]["template"]["spec"]["containers"][0]["image"],
                         "mirror.example/argoproj/workflow-controller:v3.7.18")


if __name__ == "__main__":
    unittest.main()
