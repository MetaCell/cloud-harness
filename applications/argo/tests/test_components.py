"""Render the vendored Argo components without changing the harness contract."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

CHART = Path(__file__).resolve().parents[1] / "deploy" / "charts"
HELM = os.environ.get("HELM", "helm")


class ArgoComponentsTests(unittest.TestCase):
    def render(self, *extra, chart=CHART):
        result = subprocess.run(
            [HELM, "template", "argo-contract", str(chart), "--namespace", "local-test", *extra],
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
        role = next(obj for obj in objects if obj["kind"] == "Role" and
                    obj["metadata"]["name"].endswith("-workflow"))
        rules = [rule for rule in role["rules"] if "workflowtaskresults" in rule.get("resources", [])]
        self.assertTrue(any({"create", "patch"}.issubset(rule["verbs"]) for rule in rules))

    def test_controller_can_read_only_the_configured_workflow_pull_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            chart = Path(directory)
            shutil.copytree(CHART, chart / "charts" / "argo-workflows")
            (chart / "templates").mkdir()
            shutil.copy(CHART.parent / "templates" / "argo-image-pull-secret.yaml", chart / "templates")
            (chart / "Chart.yaml").write_text(yaml.safe_dump({
                "apiVersion": "v2", "name": "cloudharness-test", "version": "0.1.0",
                "dependencies": [{"name": "argo-workflows", "version": "0.8.0"}],
            }))
            (chart / "values.yaml").write_text(yaml.safe_dump({"registry": {"secret": {"name": ""}}}))
            for single_namespace in ("true", "false"):
                for secret_name in ("task-registry", "another-registry", ""):
                    with self.subTest(single_namespace=single_namespace, secret=secret_name):
                        objects = self.render("--set", f"argo-workflows.singleNamespace={single_namespace}",
                                              "--set", "argo-workflows.controller.serviceAccount.name=custom-controller",
                                              "--set-string", f"registry.secret.name={secret_name}", chart=chart)
                        roles = [obj for obj in objects if obj["kind"] in ("Role", "ClusterRole") and
                                 obj["metadata"]["name"].endswith("-registry")]
                        bindings = [obj for obj in objects if obj["kind"] in ("RoleBinding", "ClusterRoleBinding") and
                                    obj["metadata"]["name"].endswith("-registry")]
                        if not secret_name:
                            self.assertEqual(roles, [])
                            self.assertEqual(bindings, [])
                            continue
                        self.assertEqual(len(roles), 1)
                        self.assertEqual(len(bindings), 1)
                        role, binding = roles[0], bindings[0]
                        self.assertEqual(role["kind"], "Role")
                        self.assertEqual(role["metadata"]["namespace"], "local-test")
                        self.assertEqual(role["rules"], [{"apiGroups": [""], "resources": ["secrets"],
                                                          "resourceNames": [secret_name], "verbs": ["get"]}])
                        self.assertEqual(binding["kind"], "RoleBinding")
                        self.assertEqual(binding["metadata"]["namespace"], "local-test")
                        self.assertEqual(binding["roleRef"], {"apiGroup": "rbac.authorization.k8s.io", "kind": "Role",
                                                              "name": role["metadata"]["name"]})
                        controller = next(obj for obj in objects if obj["kind"] == "Deployment" and
                                          obj["metadata"]["name"].endswith("workflow-controller"))
                        account = controller["spec"]["template"]["spec"]["serviceAccountName"]
                        self.assertEqual(binding["subjects"], [{"kind": "ServiceAccount", "name": account,
                                                                "namespace": "local-test"}])

    def test_extra_env_overrides_preserve_legacy_pod_names(self):
        for extra_env in ([], [
            {"name": "ARGO_PROGRESS_PATCH_TICK_DURATION", "value": "3s"},
            {"name": "EXISTING_SECRET", "valueFrom": {"secretKeyRef": {"name": "settings", "key": "value"}}},
        ], [{"name": "POD_NAMES", "value": "v1"}]):
            with self.subTest(extra_env=extra_env):
                objects = self.render("--set-json", f"controller.extraEnv={json.dumps(extra_env)}",
                                      "--set-json", f"server.extraEnv={json.dumps(extra_env)}")
                for obj in objects:
                    if obj["kind"] != "Deployment":
                        continue
                    env = obj["spec"]["template"]["spec"]["containers"][0]["env"]
                    self.assertEqual([item for item in env if item["name"] == "POD_NAMES"],
                                     [{"name": "POD_NAMES", "value": "v1"}])
                    for item in extra_env:
                        if item["name"] != "POD_NAMES":
                            self.assertIn(item, env)

    def test_pod_name_version_is_shared_by_controller_and_server(self):
        objects = self.render("--set", "podNameVersion=v2",
                              "--set", "controller.extraEnv[0].name=POD_NAMES",
                              "--set-string", "controller.extraEnv[0].value=v1",
                              "--set", "server.extraEnv[0].name=POD_NAMES",
                              "--set-string", "server.extraEnv[0].value=v1")
        for obj in objects:
            if obj["kind"] == "Deployment":
                env = obj["spec"]["template"]["spec"]["containers"][0]["env"]
                self.assertEqual([item for item in env if item["name"] == "POD_NAMES"],
                                 [{"name": "POD_NAMES", "value": "v2"}])

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
        controller = next(obj for obj in objects if obj["kind"] == "Deployment" and
                          obj["metadata"]["name"].endswith("workflow-controller"))
        self.assertEqual(controller["spec"]["template"]["spec"]["containers"][0]["image"],
                         "mirror.example/argoproj/workflow-controller:v3.7.18")


if __name__ == "__main__":
    unittest.main()
