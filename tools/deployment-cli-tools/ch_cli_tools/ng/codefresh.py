import re
from functools import lru_cache

from .model import CHValues, register_file
from .utils import dict_merge  # type: ignore

KEY_BUILD_PARALLEL = "build_application_images"
KEY_UNIT_TESTS = "tests_unit"
KEY_CLONE_DEPENDENCIES = "post_main_clone"
KEY_WAIT_DEPLOYMENT = "wait_deployment"
KEY_API_TESTS = "tests_api"
KEY_E2E_TESTS = "tests_e2e"

_INVALID_STEP_KEY_CHARS = re.compile(r"[^a-zA-Z0-9_]")


def _clean_step_key(name: str) -> str:
    return _INVALID_STEP_KEY_CHARS.sub("_", name)


def _git_main_domain(url: str) -> str:
    try:
        host = url.split("//")[1].split("/")[0]
    except IndexError:
        return "${{ DEFAULT_REPO }}"
    if "gitlab" in host:
        return "gitlab"
    if "bitbucket" in host:
        return "bitbucket"
    return "github"


@register_file(
    "codefresh_template",
    lambda root: root / "deployment-configuration" / "codefresh-template.yaml",
)
class CHCodefreshTemplate(CHValues):
    @lru_cache
    def all_values(self):
        layer = self.containing_project
        own = self.merge_with_envs(self.project.config.envs)
        if layer.base is None:
            return own
        return dict_merge(layer.base.codefresh_template.all_values(), own)


@register_file(
    "codefresh", lambda root: root / "deployment" / "codefresh.yaml", only_env=True
)
class CHCodefresh(CHValues):
    def qualify(self, image_name):
        return self.project.qualify(image_name)

    def _context_for(self, entity):
        return entity.dockerfile.resolve_context(self.path.parent).resolve_for_build(
            self.path.parent
        )

    def _repo_relative(self, path) -> str:
        return str(path.resolve().relative_to(self.path.parent.resolve(), walk_up=True))

    def _build_arguments(self, entity) -> list[str]:
        args: dict[str, str] = {}
        if self.project.config.local or self.project.config.debug:
            args["DEBUG"] = "true"
        for dep in self.project._combined_dependencies(entity):
            if isinstance(dep, str):
                continue
            args[dep.name.upper().replace("-", "_")] = self.qualify(dep.image_name)
        args.update(self.project.all_source_images())
        return [f"{key}={value}" for key, value in args.items()]

    def _collect_build_step(self, entity):
        context = self._context_for(entity)
        step = {
            "title": f"Building {entity.name}",
            "type": "build",
            "image_name": self.qualify(entity.image_name),
            "working_directory": str(context.path),
            "dockerfile": str(context.dockerfile.path),
            "tag": "${{CF_SHORT_REVISION}}",
        }
        build_arguments = self._build_arguments(entity)
        if build_arguments:
            step["build_arguments"] = build_arguments
        # MISSING: a `stage:` assignment (no `stages` pipeline scaffolding is
        # modeled here). `registry_secret_name`/`domain` are on CHDeployConfig
        # now but have nothing to plug into yet either: registry auth for a
        # push is a Codefresh registry integration reference, not a k8s secret
        # name (that's a Helm-values concern), and `domain` only matters for
        # e2e test steps, not generated yet.
        return entity.name, step

    def _collect_git_clone_steps(self, project):
        steps = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            for dep in app.git_dependencies:
                url = dep["url"]
                branch_tag = dep.get("branch_tag")
                repo_name = url.rsplit("/", 1)[-1]
                step_name = _clean_step_key(
                    f"clone_{repo_name}_{branch_tag}_{app.name}"
                )
                destination = app.path / "dependencies" / (dep.get("path") or "")
                steps[step_name] = {
                    "title": f"Cloning {repo_name} repository...",
                    "type": "git-clone",
                    "repo": url,
                    "revision": branch_tag,
                    "working_directory": self._repo_relative(destination),
                    "git": _git_main_domain(url),
                }
        return steps

    def _collect_task_build_steps(self, app):
        steps = {}
        for task in app.tasks.values():
            if not task.dockerfile.path.exists():
                continue
            key, step = self._collect_build_step(task)
            steps[key] = step
        return steps

    def _collect_base_image_build_steps(self, project):
        steps = {}
        for base_image in project.base_images.values():
            if not base_image.dockerfile.path.exists():
                continue
            key, step = self._collect_build_step(base_image)
            steps[key] = step
        return steps

    def _collect_unit_test_steps(self, project):
        steps = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            commands = app.test.unit.commands
            if not commands:
                continue
            steps[f"{app.name}_ut"] = {
                "title": f"Unit tests for {app.name}",
                "commands": commands,
                "image": self.qualify(app.image_name),
            }
        return steps

    def _collect_rollout_wait_commands(self, project) -> list[str]:
        secured_gatekeepers = project.config.secured_gatekeepers
        commands = []
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            deployment = app.deployment_config
            if deployment.get("auto"):
                kind = "statefulset" if deployment.get("statefulset") else "deployment"
                name = deployment.get("name") or app.name
                commands.append(f"kubectl rollout status {kind}/{name}")
            if app.harness_config.get("secured") and secured_gatekeepers:
                # gatekeepers are always rendered as deployments
                subdomain = app.harness_config.get("subdomain")
                commands.append(f"kubectl rollout status deployment/{subdomain}-gk")
        if commands:
            commands.append("sleep 60")  # give the certificates time to settle
        return commands

    def _app_domain(self, app) -> str:
        subdomain = app.harness_config.get("subdomain")
        return f"https://{subdomain}." + "${{DOMAIN}}"

    def _test_environment(self, app, app_domain: str) -> list[str]:
        env: dict[str, str] = {"APP_URL": app_domain}
        users = app.harness_config.get("accounts", {}).get("users") or []
        if users:
            main_user = users[0]
            env["USERNAME"] = main_user.get("username")
            env["PASSWORD"] = main_user.get("password") or "test"
        e2e = app.test.e2e
        if not e2e.smoketest:
            env["SKIP_SMOKETEST"] = "true"
        if e2e.ignore_console_errors:
            env["IGNORE_CONSOLE_ERRORS"] = "true"
        if e2e.ignore_request_errors:
            env["IGNORE_REQUEST_ERRORS"] = "true"
        return [f"{key}={value}" for key, value in env.items()]

    def _schemathesis_command(self, app, app_domain: str) -> str:
        api = app.test.api
        params = ["--base-url", app_domain]
        for check in api.checks:
            params += ["-c", check]
        params += api.run_params
        return " ".join(
            ["st", "--pre-run", "cloudharness_test.apitest_init", "run", "api/openapi.yaml", *params]
        )

    def _api_test_commands(self, app, app_domain: str) -> list[str]:
        commands = []
        if app.test.api.autotest:
            commands.append(self._schemathesis_command(app, app_domain))
        if (app.path / "test" / "api").exists():
            commands.append("pytest -v test/api")
        return commands

    def _api_test_volumes(self, app) -> list[str]:
        app_path = self._repo_relative(app.path)
        return [
            "${{CF_REPO_NAME}}/" + f"{app_path}:/home/test",
            "${{CF_REPO_NAME}}/deployment/helm/values.yaml:/opt/cloudharness/resources/allvalues.yaml",
        ]

    def _e2e_test_volumes(self, app) -> list[str]:
        app_path = self._repo_relative(app.path)
        return ["${{CF_REPO_NAME}}/" + f"{app_path}/test/e2e:/home/test/__tests__/{app.name}"]

    def _collect_api_test_steps(self, project) -> dict:
        scale = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            if not (app.test.api.enabled and app.harness_config.get("subdomain")):
                continue
            server_urls = app.openapi.server_urls
            if not server_urls:
                continue
            app_domain = server_urls[-1]
            if "http" not in app_domain:
                app_domain = self._app_domain(app) + app_domain
            scale[f"{app.name}_api_test"] = {
                "title": f"{app.name} api test",
                "volumes": self._api_test_volumes(app),
                "environment": self._test_environment(app, app_domain),
                "commands": self._api_test_commands(app, app_domain),
            }
        return scale

    def _collect_e2e_test_steps(self, project) -> dict:
        scale = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            if not (app.test.e2e.enabled and app.harness_config.get("subdomain")):
                continue
            app_domain = self._app_domain(app)
            scale[f"{app.name}_e2e_test"] = {
                "title": f"{app.name} e2e test",
                "volumes": self._e2e_test_volumes(app),
                "environment": self._test_environment(app, app_domain),
            }
        return scale

    def _wire_test_image(self, project, steps, key, name):
        """Only builds/wires the test-api/test-e2e runner image once its scale
        actually needs it - matches legacy, which never builds these for a
        project that enables neither api nor e2e testing."""
        if not steps[key]["scale"]:
            del steps[key]
            return
        test_image = project.test_images.get(name)
        if test_image is None or not test_image.dockerfile.path.exists():
            return
        build_key, build_step = self._collect_build_step(test_image)
        steps[KEY_BUILD_PARALLEL].setdefault("steps", {})[build_key] = build_step
        steps[key]["image"] = self.qualify(test_image.image_name)

    def generate(self, write_on_disk=True, output_path=None):
        project = self.project

        base = project.codefresh_template.all_values()
        steps = base.setdefault("steps", {})

        build_steps = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue

            if app.dockerfile.path.exists():
                key, step = self._collect_build_step(app)
                build_steps[key] = step

            build_steps.update(self._collect_task_build_steps(app))
        build_steps.update(self._collect_base_image_build_steps(project))

        steps.setdefault(KEY_BUILD_PARALLEL, {"type": "parallel", "steps": {}})
        steps[KEY_BUILD_PARALLEL].setdefault("steps", {}).update(build_steps)

        unit_test_steps = self._collect_unit_test_steps(project)
        steps.setdefault(KEY_UNIT_TESTS, {"type": "parallel", "steps": {}})
        steps[KEY_UNIT_TESTS].setdefault("steps", {}).update(unit_test_steps)

        clone_steps = self._collect_git_clone_steps(project)
        if clone_steps:
            steps.setdefault(KEY_CLONE_DEPENDENCIES, {"type": "parallel", "steps": {}})
            steps[KEY_CLONE_DEPENDENCIES].setdefault("steps", {}).update(clone_steps)

        # Only extends/prunes already template-provided tests_api/tests_e2e
        # steps (their image/volumes/when-condition scaffolding is template-
        # driven) - matches legacy, which deletes either step entirely once
        # its scale ends up empty.
        if KEY_API_TESTS in steps:
            steps[KEY_API_TESTS].setdefault("scale", {}).update(
                self._collect_api_test_steps(project)
            )
            self._wire_test_image(project, steps, KEY_API_TESTS, "test-api")

        if KEY_E2E_TESTS in steps:
            steps[KEY_E2E_TESTS].setdefault("scale", {}).update(
                self._collect_e2e_test_steps(project)
            )
            self._wire_test_image(project, steps, KEY_E2E_TESTS, "test-e2e")

        if KEY_WAIT_DEPLOYMENT in steps:
            steps[KEY_WAIT_DEPLOYMENT].setdefault("commands", []).extend(
                self._collect_rollout_wait_commands(project)
            )

        # MISSING: `version`/`stages` pipeline scaffolding (present when the
        # template itself declares them, not computed here), the
        # prepare_deployment/deploy steps (entirely template-driven already),
        # secrets/db-connect-string/registry-secret wiring into the deployment
        # step's arguments, and parallel-step batching + stage ordering
        # (sort_parallel_steps/order_steps_by_stage in legacy) - none of that
        # is reproduced here yet.

        if write_on_disk:
            self.write(base, output_path=output_path)

        return base
