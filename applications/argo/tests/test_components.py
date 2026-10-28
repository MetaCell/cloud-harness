"""Check the Argo chart's PNS compatibility without a Kubernetes cluster."""
import json
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

    def test_pns_and_all_component_versions_are_preserved(self):
        objects = self.render("--set", "controller.podWorkers=4",
                              "--set", "controller.workflowWorkers=8")
        deployments = [obj for obj in objects if obj["kind"] == "Deployment"]
        self.assertEqual(len(deployments), 2)
        for obj in deployments:
            container = obj["spec"]["template"]["spec"]["containers"][0]
            self.assertTrue(container["image"].endswith(":v3.3.10"))
            names = [item for item in container["env"] if item["name"] == "POD_NAMES"]
            self.assertEqual(names, [{"name": "POD_NAMES", "value": "v1"}])
            self.assertNotIn("--pod-workers", container["args"])
        controller = next(obj for obj in deployments if obj["metadata"]["name"].endswith("workflow-controller"))
        args = controller["spec"]["template"]["spec"]["containers"][0]["args"]
        self.assertIn("quay.io/argoproj/argoexec:v3.3.10", args)
        self.assertIn("--workflow-workers", args)
        configmap = next(obj for obj in objects if obj["kind"] == "ConfigMap")
        config = yaml.safe_load(configmap["data"]["config"])
        self.assertEqual(config["containerRuntimeExecutor"], "pns")
        self.assertNotIn("images", config)
        self.assertIn("argo-server", [obj["metadata"]["name"] for obj in objects if obj["kind"] == "Service"])

    def test_extra_env_keeps_custom_settings_and_explicit_pod_names(self):
        cases = [[], [{"name": "EXISTING_SETTING", "value": "enabled"}],
                 [{"name": "POD_NAMES", "value": "v2"}],
                 [{"name": "POD_NAMES", "valueFrom": {"configMapKeyRef": {"name": "settings", "key": "naming"}}}]]
        for extra_env in cases:
            with self.subTest(extra_env=extra_env):
                objects = self.render("--set-json", f"controller.extraEnv={json.dumps(extra_env)}",
                                      "--set-json", f"server.extraEnv={json.dumps(extra_env)}")
                for obj in objects:
                    if obj["kind"] != "Deployment":
                        continue
                    env = obj["spec"]["template"]["spec"]["containers"][0]["env"]
                    for item in extra_env:
                        self.assertIn(item, env)
                    expected = [item for item in extra_env if item["name"] == "POD_NAMES"]
                    self.assertEqual([item for item in env if item["name"] == "POD_NAMES"],
                                     expected or [{"name": "POD_NAMES", "value": "v1"}])

    def test_controller_and_executor_task_result_permissions(self):
        for single_namespace in ("true", "false"):
            with self.subTest(single_namespace=single_namespace):
                objects = self.render("--set", f"singleNamespace={single_namespace}")
                roles = [obj for obj in objects if obj["kind"] in ("Role", "ClusterRole")]
                controller = next(obj for obj in roles if obj["metadata"]["name"].endswith("-workflow-controller"))
                self.assertFalse(any("workflowtasksets/status" in rule["resources"]
                                     for rule in controller["rules"]))
                result_rules = [rule for rule in controller["rules"] if "workflowtaskresults" in rule["resources"]]
                self.assertEqual(result_rules, [{"apiGroups": ["argoproj.io"],
                                                "resources": ["workflowtaskresults"],
                                                 "verbs": ["list", "watch", "deletecollection"]}])
                workflow = next(obj for obj in roles if obj["metadata"]["name"].endswith("-workflow"))
                result_rules = [rule for rule in workflow["rules"] if "workflowtaskresults" in rule["resources"]]
                self.assertEqual(result_rules, [{"apiGroups": ["argoproj.io"],
                                                "resources": ["workflowtaskresults"],
                                                "verbs": ["create", "patch"]}])
                self.assertTrue(any("pods" in rule["resources"] and "patch" in rule["verbs"]
                                    for rule in workflow["rules"]))
                self.assertFalse(any("workflowartifactgctasks" in rule["resources"] for rule in controller["rules"]))

    def test_release_crds_support_task_results_and_native_progress(self):
        crds = {obj["metadata"]["name"]: obj for obj in
                (yaml.safe_load(path.read_text()) for path in (CHART / "crds").glob("*.yaml"))}
        self.assertEqual(len(crds), 7)
        self.assertNotIn("workflowartifactgctasks.argoproj.io", crds)
        self.assertIn("workflowtasksets.argoproj.io", crds)
        version = crds["workflowtaskresults.argoproj.io"]["spec"]["versions"][0]
        self.assertTrue(version["served"] and version["storage"])
        self.assertEqual(version["schema"]["openAPIV3Schema"]["properties"]["progress"]["type"], "string")


    def test_cloudharness_uses_built_controller_and_preserves_image_overrides(self):
        import shutil
        import tempfile

        for override in ({}, {"registry": "mirror.example", "repository": "argo/controller", "tag": "patched"}):
            with self.subTest(override=override), tempfile.TemporaryDirectory() as folder:
                parent = Path(folder)
                (parent / "Chart.yaml").write_text("apiVersion: v2\nname: cloudharness-argo-test\nversion: 0.1.0\n")
                shutil.copytree(CHART, parent / "charts" / "argo-workflows")
                shutil.copytree(CHART.parent / "templates", parent / "templates")
                values = {"apps": {"argo": {"image": "registry.example/argo:content-hash",
                                           "serviceaccount": "argo-workflows"}},
                          "registry": {"secret": {"name": "build-registry"}},
                          "argo-workflows": {"controller": {"image": override}}}
                value_file = parent / "test-values.yaml"
                value_file.write_text(yaml.safe_dump(values))
                result = subprocess.run([HELM, "template", "argo-contract", str(parent),
                                         "--namespace", "local-test", "-f", str(value_file)],
                                        check=True, capture_output=True, text=True)
                objects = [obj for obj in yaml.safe_load_all(result.stdout) if obj]
                deployments = [obj for obj in objects if obj["kind"] == "Deployment"]
                self.assertEqual(len(deployments), 2)
                controller = next(obj for obj in deployments if obj["metadata"]["name"].endswith("workflow-controller"))
                container = controller["spec"]["template"]["spec"]["containers"][0]
                expected = "mirror.example/argo/controller:patched" if override else "registry.example/argo:content-hash"
                self.assertEqual(container["image"], expected)
                if not override:
                    self.assertEqual(controller["spec"]["template"]["spec"]["imagePullSecrets"],
                                     [{"name": "build-registry"}])
                self.assertIn("quay.io/argoproj/argoexec:v3.3.10", container["args"])
                self.assertTrue(any(obj["kind"] == "ClusterRoleBinding" and obj["roleRef"]["name"] == "cluster-admin"
                                    for obj in objects))


if __name__ == "__main__":
    unittest.main()
