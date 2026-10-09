import re
from functools import lru_cache
from pathlib import Path

from ch_cli_tools.secrets import is_cloudharness_managed, is_secret_config, secret_value
from ch_cli_tools.utils import check_image_exists_in_registry  # type: ignore

from .model import KEY_TASK_IMAGES, CHValues, register_file
from .utils import dict_merge  # type: ignore

KEY_BUILD_PARALLEL = "build_application_images"
KEY_UNIT_TESTS = "tests_unit"
KEY_CLONE_DEPENDENCIES = "post_main_clone"
KEY_WAIT_DEPLOYMENT = "wait_deployment"
KEY_API_TESTS = "tests_api"
KEY_E2E_TESTS = "tests_e2e"
KEY_PREPARE_DEPLOYMENT = "prepare_deployment"
KEY_PUBLISH = "publish"
KEY_DEPLOYMENT = "deployment"

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


_CLOUD_HARNESS_DIR_NAME = "cloud-harness"


def _to_codefresh_path(path, relative_to) -> str:
    rel_parts = path.resolve().relative_to(relative_to.resolve(), walk_up=True).parts
    if rel_parts and rel_parts[0] == "..":
        abs_parts = path.resolve().parts
        if _CLOUD_HARNESS_DIR_NAME in abs_parts:
            return str(Path(*abs_parts[abs_parts.index(_CLOUD_HARNESS_DIR_NAME) :]))
    return str(Path(*rel_parts)) if rel_parts else "."


def _env_key(name: str) -> str:
    return name.replace("-", "_").upper()


def _tag_variable(name: str) -> str:
    return f"{_env_key(name)}_TAG"


def _extract_tag(image: str) -> str:
    return image.split(":")[1] if ":" in image else "latest"


def write_env_file(helm_values, filename, image_cache_endpoint_url=None) -> None:
    env: dict[str, int | str] = {}

    def record(name: str, image: str) -> None:
        tag = _extract_tag(image)
        env[_tag_variable(name)] = tag
        chunks = image.split(":")[0].split("/")
        has_registry_host = "." in chunks[0]
        registry = chunks[0] if has_registry_host else "docker.io"
        image_name = "/".join(chunks[1:] if has_registry_host else chunks)
        exists = check_image_exists_in_registry(
            registry, image_name, tag, endpoint_url=image_cache_endpoint_url
        )
        env[_tag_variable(name) + ("_EXISTS" if exists else "_NEW")] = 1

    for app_name, app in helm_values.apps.items():
        if app.harness and app.harness.deployment.image:
            record(app_name, app.harness.deployment.image)

    for name, image in helm_values[KEY_TASK_IMAGES].items():
        record(name, image)

    project = helm_values._ch_project
    for name, test_image in project.test_images.items():
        if not test_image.dockerfile.exists():
            continue
        record(name, project.qualify_image(test_image))

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(f"{key}={value}\n" for key, value in env.items())


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
            args[_env_key(dep.name)] = self.qualify(dep.image_name)
        args.update(self.project.all_source_images())
        return [f"{key}={value}" for key, value in args.items()]

    def _build_skip_when_condition(self, name) -> dict:
        tag_var = _tag_variable(name)
        exists_var = f"{tag_var}_EXISTS"
        force_var = f"{tag_var}_FORCE_BUILD"
        return {
            "condition": {
                "any": {
                    "buildDoesNotExist": "includes('${{%s}}', '{{%s}}') == true"
                    % (exists_var, exists_var),
                    "forceNoCache": "includes('${{%s}}', '{{%s}}') == false"
                    % (force_var, force_var),
                }
            }
        }

    def _collect_build_step(self, entity):
        context = self._context_for(entity)
        step = {
            "title": f"Building {entity.name}",
            "type": "build",
            "stage": "build",
            "registry": "${{CODEFRESH_REGISTRY}}",
            "buildkit": True,
            "image_name": self.qualify(entity.image_name),
            "working_directory": str(context.path),
            "dockerfile": str(context.dockerfile.path),
            "tag": "${{CF_SHORT_REVISION}}",
            "build_arguments": [
                "NOCACHE=${{CF_BUILD_ID}}",
                *self._build_arguments(entity),
            ],
            "when": self._build_skip_when_condition(entity.name),
        }
        step["dependencies"] = [
            dep.name
            for dep in self.project._combined_dependencies(entity)
            if not isinstance(dep, str)
        ]
        # MISSING: `registry_secret_name`/`domain` are on CHDeployConfig now
        # but have nothing to plug into yet either: registry auth for a push
        # is a Codefresh registry integration reference, not a k8s secret name
        # (that's a Helm-values concern), and `domain` only matters for e2e
        # test steps, not generated yet. No support for a project overriding
        # codefresh-build-template.yaml itself - these fields are
        # cloud-harness's own shipped defaults, hardcoded (no fixture
        # exercises an override with different content).
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

    def _collect_publish_step(self, entity):
        title = (
            entity.name.capitalize()
            .replace("-", " ")
            .replace("/", " ")
            .replace(".", " ")
            .strip()
        )
        skip_variable = f"{_env_key(entity.name)}_PUBLISH_SKIP"
        step = {
            "title": title,
            "type": "push",
            "stage": "publish",
            "candidate": f"{self.qualify(entity.image_name)}:${{{{CF_SHORT_REVISION}}}}",
            "tags": ["${{DEPLOYMENT_PUBLISH_TAG}}", "latest"],
            "registry": "${{REGISTRY_PUBLISH_URL}}",
            "when": {
                "condition": {
                    "all": {
                        "skipPublish": "includes('${{%s}}', '{{%s}}') == true"
                        % (skip_variable, skip_variable),
                    }
                }
            },
        }
        return f"publish_{entity.name}", step

    def _collect_task_build_steps(self, app):
        build_steps, publish_steps = {}, {}
        for task in app.tasks.values():
            if not task.dockerfile.exists():
                continue
            key, step = self._collect_build_step(task)
            build_steps[key] = step
            pkey, pstep = self._collect_publish_step(task)
            publish_steps[pkey] = pstep
        return build_steps, publish_steps

    def _collect_base_image_build_steps(self, project):
        build_steps, publish_steps = {}, {}
        for base_image in project.base_images.values():
            if not base_image.dockerfile.exists():
                continue
            key, step = self._collect_build_step(base_image)
            build_steps[key] = step
            pkey, pstep = self._collect_publish_step(base_image)
            publish_steps[pkey] = pstep
        return build_steps, publish_steps

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

    def _collect_deployment_secret_values(self, project) -> list[str]:
        values = []
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            app_key = app.name.replace("_", "__")
            for secret, definition in app.secrets.items():
                if (
                    not is_cloudharness_managed(definition)
                    or secret_value(definition) == ""
                ):
                    continue
                secret_name = secret.replace("_", "__")
                # the rich form nests the value under `default`
                value_path = (
                    f"{secret_name}_default"
                    if is_secret_config(definition)
                    else secret_name
                )
                values.append(
                    'apps_%s_harness_secrets_%s="${{%s}}"'
                    % (app_key, value_path, secret_name.upper())
                )
            if app.database.get("connect_string") == "":
                var_name = f"{_env_key(app.name)}_DB_CONNECT_STRING"
                values.append(
                    'apps_%s_harness_database_connect__string="${{%s}}"'
                    % (app_key, var_name)
                )
        if project.config.registry_secret_name:
            values.append('registry_secret_value="${{K8S_SA_JSON}}"')
        return values

    def _substitute_prepare_deployment_placeholders(
        self, project, commands
    ) -> list[str]:
        config = project.config
        params = [f"-i {inc}" for inc in config.includes] + [
            f"-ex {exc}" for exc in config.excludes
        ]
        paths = " ".join(
            _to_codefresh_path(layer.root, project.root)
            for layer in reversed(project.all_layers())
        )
        replacements = {
            "$ENV": "-".join(config.envs),
            "$PARAMS": " ".join(params),
            "$PATHS": paths,
        }
        result = []
        for command in commands:
            for placeholder, value in replacements.items():
                command = command.replace(placeholder, value)
            result.append(command)
        return result

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
            [
                "st",
                "--pre-run",
                "cloudharness_test.apitest_init",
                "run",
                "api/openapi.yaml",
                *params,
            ]
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
        return [
            "${{CF_REPO_NAME}}/"
            + f"{app_path}/test/e2e:/home/test/__tests__/{app.name}"
        ]

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

    def _wire_test_image(self, project, steps, key, name, build_steps):
        if not steps[key]["scale"]:
            del steps[key]
            return
        test_image = project.test_images.get(name)
        if test_image is None or not test_image.dockerfile.exists():
            return
        build_key, build_step = self._collect_build_step(test_image)
        build_steps[build_key] = build_step
        steps[key]["image"] = self.qualify(test_image.image_name)

    def _batch_build_steps(self, build_steps: dict) -> list[dict]:
        remaining = dict(build_steps)
        groups = []
        while remaining:
            group = {
                name: step
                for name, step in remaining.items()
                if not any(dep in remaining for dep in step.get("dependencies") or ())
            }
            if not group:
                # Dependency cycle - legacy recurses forever on this; we don't.
                group, remaining = dict(remaining), {}
            for name, step in group.items():
                step.pop("dependencies", None)
                remaining.pop(name, None)
            groups.append(group)
        return groups

    def _prune_build_group_placeholders(self, steps: dict) -> dict:
        pruned = dict(steps)
        if not pruned.get(KEY_BUILD_PARALLEL, {}).get("steps"):
            pruned.pop(KEY_BUILD_PARALLEL, None)
        for name in [
            n
            for n in pruned
            if n.startswith(f"{KEY_BUILD_PARALLEL}_") and not pruned[n]
        ]:
            del pruned[name]
        return pruned

    def _sort_parallel_steps(self, steps: dict) -> dict:
        result = {}
        for name, step in steps.items():
            if (
                isinstance(step, dict)
                and step.get("type") == "parallel"
                and isinstance(step.get("steps"), dict)
            ):
                step = {**step, "steps": dict(sorted(step["steps"].items()))}
            result[name] = step
        return result

    def _order_steps_by_stage(self, steps: dict, stages: list) -> dict:
        stage_order = {stage: i for i, stage in enumerate(stages)}
        unknown = len(stages)

        def stage_key(item):
            step = item[1]
            return (
                stage_order.get(step.get("stage"), unknown)
                if isinstance(step, dict)
                else unknown
            )

        return dict(sorted(steps.items(), key=stage_key))

    def generate(self, write_on_disk=True, output_path=None):
        project = self.project

        base = project.codefresh_template.all_values()
        steps = base.setdefault("steps", {})

        build_steps = {}
        publish_steps = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue

            # Not just dockerfile.exists(): an app with an explicit
            # harness.deployment.image uses that pre-built image instead,
            # even if it also happens to have a Dockerfile checked in.
            if project._is_buildable_app(app):
                key, step = self._collect_build_step(app)
                build_steps[key] = step
                pkey, pstep = self._collect_publish_step(app)
                publish_steps[pkey] = pstep

            task_builds, task_publishes = self._collect_task_build_steps(app)
            build_steps.update(task_builds)
            publish_steps.update(task_publishes)
        base_builds, base_publishes = self._collect_base_image_build_steps(project)
        build_steps.update(base_builds)
        publish_steps.update(base_publishes)

        steps.setdefault(KEY_PUBLISH, {"type": "parallel", "steps": {}})
        steps[KEY_PUBLISH].setdefault("steps", {}).update(publish_steps)

        unit_test_steps = self._collect_unit_test_steps(project)
        steps.setdefault(KEY_UNIT_TESTS, {"type": "parallel", "steps": {}})
        steps[KEY_UNIT_TESTS].setdefault("steps", {}).update(unit_test_steps)

        clone_steps = self._collect_git_clone_steps(project)
        if clone_steps:
            steps.setdefault(KEY_CLONE_DEPENDENCIES, {"type": "parallel", "steps": {}})
            steps[KEY_CLONE_DEPENDENCIES].setdefault("steps", {}).update(clone_steps)

        for key, image_name, collect in (
            (KEY_API_TESTS, "test-api", self._collect_api_test_steps),
            (KEY_E2E_TESTS, "test-e2e", self._collect_e2e_test_steps),
        ):
            if key in steps:
                steps[key].setdefault("scale", {}).update(collect(project))
                self._wire_test_image(project, steps, key, image_name, build_steps)

        steps.setdefault(KEY_BUILD_PARALLEL, {"type": "parallel", "steps": {}})
        for index, group in enumerate(self._batch_build_steps(build_steps)):
            group_step = dict(steps[KEY_BUILD_PARALLEL])
            group_step["title"] = f"Build parallel step {index + 1}"
            group_step["steps"] = group
            steps[f"{KEY_BUILD_PARALLEL}_{index}"] = group_step

        if KEY_WAIT_DEPLOYMENT in steps:
            steps[KEY_WAIT_DEPLOYMENT].setdefault("commands", []).extend(
                self._collect_rollout_wait_commands(project)
            )

        deployment_step = steps.get(KEY_DEPLOYMENT)
        if deployment_step is not None:
            arguments = deployment_step.setdefault("arguments", {})
            arguments.setdefault("custom_values", []).extend(
                self._collect_deployment_secret_values(project)
            )

        prepare_deployment = steps.get(KEY_PREPARE_DEPLOYMENT)
        if prepare_deployment and prepare_deployment.get("commands"):
            prepare_deployment["commands"] = (
                self._substitute_prepare_deployment_placeholders(
                    project, prepare_deployment["commands"]
                )
            )

        steps = self._prune_build_group_placeholders(steps)
        steps = self._sort_parallel_steps(steps)
        stages = base.get("stages")
        if stages:
            steps = self._order_steps_by_stage(steps, stages)
        base["steps"] = steps

        # MISSING: `version`/`stages` pipeline scaffolding (present when the
        # template itself declares them, not computed here) and the deploy
        # step's own fields (entirely template-driven already, beyond
        # custom_values) aren't reproduced here. Pruning of other empty
        # containers (tests_unit/post_main_clone/etc, as legacy's generic
        # "remove useless steps" filter does) is deliberately NOT done here -
        # only the build-group placeholders are, to avoid touching containers
        # whose emptiness behavior isn't covered by a test yet.

        if write_on_disk:
            self.write(base, output_path=output_path)

        return base
