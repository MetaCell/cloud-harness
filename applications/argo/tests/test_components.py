"""Check the unmodified upstream chart with CloudHarness integration values."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[3]
DEPLOY = ROOT / "applications" / "argo" / "deploy"
CHART = DEPLOY / "charts"
HELM = os.environ.get("HELM", "helm")
# Release tree digest: sorted relative path + NUL + file bytes + NUL.
UPSTREAM_TREE_SHA256 = "dd27933fe68b05ff59ed5b0e41b6db7280b01727807131671eda83197d23605b"


class ArgoComponentsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = tempfile.TemporaryDirectory()
        cls.parent = Path(cls.directory.name)
        (cls.parent / "Chart.yaml").write_text(
            "apiVersion: v2\nname: cloudharness-argo-test\nversion: 0.1.0\n")
        shutil.copytree(CHART, cls.parent / "charts" / "argo-workflows")
        shutil.copytree(DEPLOY / "templates", cls.parent / "templates")
        cls.values = yaml.safe_load((ROOT / "deployment-configuration" / "values-template.yaml").read_text())
        cls.values["apps"] = {"argo": {"serviceaccount": "argo-workflows"}}
        (cls.parent / "test-values.yaml").write_text(yaml.safe_dump(cls.values))

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def render(self, *extra):
        result = subprocess.run(
            [HELM, "template", "argo-contract", str(self.parent), "--namespace", "local-test",
             "-f", str(self.parent / "test-values.yaml"), *extra],
            check=True, capture_output=True, text=True)
        return [obj for obj in yaml.safe_load_all(result.stdout) if obj]

    def test_chart_is_the_unmodified_official_release(self):
        digest = hashlib.sha256()
        for path in sorted(CHART.rglob("*")):
            if path.is_file():
                digest.update(path.relative_to(CHART).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
        self.assertEqual(digest.hexdigest(), UPSTREAM_TREE_SHA256)
        metadata = yaml.safe_load((CHART / "Chart.yaml").read_text())
        self.assertEqual(metadata["version"], "2.0.14")
        self.assertEqual(metadata["appVersion"], "v4.1.6")

    def test_official_components_and_cloudharness_defaults(self):
        objects = self.render("--set", "argo-workflows.controller.podWorkers=4",
                              "--set", "argo-workflows.controller.workflowWorkers=8")
        deployments = [obj for obj in objects if obj["kind"] == "Deployment"]
        self.assertEqual(len(deployments), 2)
        for obj in deployments:
            container = obj["spec"]["template"]["spec"]["containers"][0]
            self.assertTrue(container["image"].endswith(":v4.1.6"))
            self.assertNotIn("--pod-workers", container["args"])
            self.assertIn({"configMapRef": {"name": "argo-cloudharness-env"}}, container["envFrom"])
        config = next(obj for obj in objects if obj["kind"] == "ConfigMap" and
                      obj["metadata"]["name"] == "argo-cloudharness-env")
        self.assertEqual(config["data"]["POD_NAMES"], "v1")
        controller = next(obj for obj in deployments if obj["metadata"]["name"].endswith("-workflow-controller"))
        args = controller["spec"]["template"]["spec"]["containers"][0]["args"]
        self.assertIn("quay.io/argoproj/argoexec:v4.1.6", " ".join(args))
        self.assertIn("--workflow-workers", args)
        configmap = next(obj for obj in objects if obj["kind"] == "ConfigMap" and "config" in obj.get("data", {}))
        config = yaml.safe_load(configmap["data"]["config"]) or {}
        self.assertNotIn("containerRuntimeExecutor", config)
        self.assertNotIn("containerRuntimeExecutors", config)
        server = next(obj for obj in deployments if obj["metadata"]["name"].endswith("-server"))
        container = server["spec"]["template"]["spec"]["containers"][0]
        self.assertIn("--auth-mode=server", container["args"])
        self.assertIn("--secure=false", container["args"])
        alias = next(obj for obj in objects if obj["kind"] == "Service" and obj["metadata"]["name"] == "argo-server")
        labels = server["spec"]["template"]["metadata"]["labels"]
        self.assertTrue(all(labels[key] == value for key, value in alias["spec"]["selector"].items()))
        self.assertEqual(alias["spec"]["ports"][0]["port"], 2746)

    def test_extra_env_preserves_settings_and_explicit_pod_names(self):
        cases = [[], [{"name": "EXISTING_SETTING", "value": "enabled"}],
                 [{"name": "POD_NAMES", "value": "v2"}],
                 [{"name": "POD_NAMES", "valueFrom": {"configMapKeyRef": {"name": "settings", "key": "naming"}}}]]
        for extra_env in cases:
            with self.subTest(extra_env=extra_env):
                objects = self.render("--set-json", f"argo-workflows.controller.extraEnv={json.dumps(extra_env)}",
                                      "--set-json", f"argo-workflows.server.extraEnv={json.dumps(extra_env)}")
                for obj in objects:
                    if obj["kind"] != "Deployment":
                        continue
                    container = obj["spec"]["template"]["spec"]["containers"][0]
                    for item in extra_env:
                        self.assertIn(item, container["env"])
                    self.assertEqual([item for item in container["env"] if item["name"] == "POD_NAMES"],
                                     [item for item in extra_env if item["name"] == "POD_NAMES"])
                    self.assertIn({"configMapRef": {"name": "argo-cloudharness-env"}}, container["envFrom"])

    def test_native_task_result_and_existing_secret_read_permissions(self):
        for single_namespace in ("true", "false"):
            with self.subTest(single_namespace=single_namespace):
                objects = self.render("--set", f"argo-workflows.singleNamespace={single_namespace}")
                roles = [obj for obj in objects if obj["kind"] in ("Role", "ClusterRole")]
                controller = next(obj for obj in roles if obj["metadata"]["name"].endswith("-workflow-controller"))
                rules = [rule for rule in controller["rules"] if "workflowtaskresults" in rule["resources"]]
                self.assertTrue(rules)
                self.assertTrue({"list", "watch", "deletecollection"}.issubset(rules[0]["verbs"]))
                workflow = next(obj for obj in roles if obj["metadata"]["name"].endswith("-workflow"))
                self.assertTrue(any("workflowtaskresults" in rule["resources"] and
                                    {"create", "patch"}.issubset(rule["verbs"]) for rule in workflow["rules"]))
                image_role = next(obj for obj in roles if obj["metadata"]["name"].endswith("-image-commands"))
                self.assertEqual(image_role["rules"], [{"apiGroups": [""], "resources": ["secrets"], "verbs": ["get"]}])
                self.assertEqual(image_role["kind"], "Role" if single_namespace == "true" else "ClusterRole")
                binding = next(obj for obj in objects if obj["kind"] in ("RoleBinding", "ClusterRoleBinding") and
                               obj["metadata"]["name"] == image_role["metadata"]["name"])
                controller_deploy = next(obj for obj in objects if obj["kind"] == "Deployment" and
                                         obj["metadata"]["name"].endswith("-workflow-controller"))
                self.assertEqual(binding["subjects"][0]["name"],
                                 controller_deploy["spec"]["template"]["spec"]["serviceAccountName"])

    def test_official_crd_install_and_upgrade_hook(self):
        objects = self.render()
        job = next(obj for obj in objects if obj["kind"] == "Job")
        self.assertEqual(job["metadata"]["annotations"]["helm.sh/hook"], "pre-install,pre-upgrade")
        self.assertEqual(job["spec"]["template"]["spec"]["containers"][0]["image"],
                         "quay.io/argoproj/argo-workflows-crdinstaller:v4.1.6")
        self.assertFalse(any(obj["kind"] == "CustomResourceDefinition" for obj in objects))
        objects = self.render("--set", "argo-workflows.crds.full=false")
        crds = {obj["metadata"]["name"]: obj for obj in objects if obj["kind"] == "CustomResourceDefinition"}
        self.assertEqual(len(crds), 8)
        self.assertIn("workflowartifactgctasks.argoproj.io", crds)
        self.assertIn("workflowtasksets.argoproj.io", crds)
        version = crds["workflowtaskresults.argoproj.io"]["spec"]["versions"][0]
        self.assertTrue(version["served"] and version["storage"])
        self.assertEqual(version["schema"]["openAPIV3Schema"]["properties"]["progress"]["type"], "string")

    def test_image_overrides_and_existing_argo_server_name(self):
        objects = self.render("--set", "argo-workflows.controller.image.registry=mirror.example",
                              "--set", "argo-workflows.controller.image.repository=argo/controller",
                              "--set", "argo-workflows.controller.image.tag=patched",
                              "--set", "argo-workflows.fullnameOverride=argo")
        controller = next(obj for obj in objects if obj["kind"] == "Deployment" and
                          obj["metadata"]["name"].endswith("-workflow-controller"))
        self.assertEqual(controller["spec"]["template"]["spec"]["containers"][0]["image"],
                         "mirror.example/argo/controller:patched")
        self.assertEqual(len([obj for obj in objects if obj["kind"] == "Service" and
                              obj["metadata"]["name"] == "argo-server"]), 1)


if __name__ == "__main__":
    unittest.main()
