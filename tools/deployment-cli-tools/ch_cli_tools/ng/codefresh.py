"""Generates codefresh.yaml from a CHProject.

Codefresh is the CI/CD pipeline that actually builds, tests, publishes and
deploys a CH project, but unlike `skaffold dev` (used locally, right after
being generated, on the same machine) codefresh.yaml is generated once
(dev-time or a CI pre-step) and then committed - Codefresh parses the whole
pipeline definition before any step of it runs, so there's no regenerating it
mid-run. Generation must therefore statically lay out every build/publish/test
step the deployment could need, in dependency order, batched into parallel
groups, with the pieces that can only be known at pipeline-run time (which
images already exist, what the registry currently resolves to) left as
Codefresh's own `${{VAR}}` pipeline-variable references rather than baked-in
values - a value resolved at generation time instead would silently go stale
the next time that variable changes without a matching regeneration.

CH model concepts this relies on:
- CHProject.involved_apps / `._is_buildable_app` scope build+publish steps to
  what's actually deployed and buildable, the same closure skaffold.py uses.
- CHProject._combined_dependencies gives each build step's `dependencies:`
  (explicit harness.dependencies.build plus the Dockerfile's own guessed
  FROM/ARG chain), used both for build args and for ordering.
- Every task under an involved app and every base image in the project gets
  its own build+publish step unconditionally, regardless of whether its
  owning app is itself deployed - codefresh always builds/publishes the full
  image universe a deployment might later reuse, a wider net than skaffold's
  manage_task_images gate.
- app.test.unit/api/e2e (commands, autotest, checks, run_params, smoketest/
  console/request-error flags) and app.openapi.server_urls drive the unit,
  API and E2E test steps; app.harness_config (subdomain, secured, accounts)
  drives their domain URLs, credentials and the gatekeeper/rollout-wait
  commands.
- app.secrets/app.database and CHDeployConfig.registry_secret_name decide
  which cloudharness-managed secret/connect-string/registry-secret values
  need exporting into the deployment step's custom_values, each as a
  reference to a Codefresh pipeline variable, not a resolved value.
- app.git_dependencies become pre-build git-clone steps.
- CHDeployConfig (includes/excludes/envs/local/debug/secured_gatekeepers)
  holds the deployment-target knobs substituted into prepare_deployment's
  harness-deployment command and the build args.
- pipeline_relative_path rewrites any path that crosses the project's own
  root into the literal "cloud-harness/..." alias - codefresh.yaml is
  committed and may run against a differently laid out checkout, unlike a
  skaffold.yaml path (consumed immediately, same machine, real path only).

CHCodefresh.generate() algorithm:

1. Start from the merged codefresh-template.yaml (CH default + project
   override, composed across the full project layer chain).
2. For every involved, buildable app: collect a build step (qualified image,
   Dockerfile, alias-rewritten working_directory, DEBUG/source_images/
   dependency build args, a cache-busting NOCACHE arg, a skip-when condition
   keyed off that image's already-exists/force-rebuild pipeline variables)
   and a matching publish step (skip-when a per-app publish-skip variable is
   set, tagged with DEPLOYMENT_PUBLISH_TAG and latest).
3. Every task of every involved app, and every base image in the project,
   gets the same build+publish step pair unconditionally (step 2's gating
   doesn't apply to them).
4. Unit test steps: one per buildable app with test.unit.commands, run
   inside that app's own freshly-tagged image.
5. API/E2E test steps: one scale entry per buildable app with test.api/
   test.e2e enabled and a subdomain (schemathesis/pytest commands or
   test/e2e volume mounts, a domain URL, and env for credentials/smoketest/
   console/request-error flags). The shared test-api/test-e2e runner image
   only gets a build step and its image wired in if at least one app
   contributed a scale entry; otherwise the whole container step is pruned.
6. Git-clone steps: one per app's declared git_dependencies, host-detected
   (github/gitlab/bitbucket) and working-directory-rewritten the same way
   build steps are.
7. Build steps are batched into dependency-ordered parallel groups - a step
   only joins a group once every build it depends on is already in an
   earlier group. A dependency cycle (which legacy recurses forever on) is
   dumped into one final group instead.
8. Deployment-adjacent wiring: wait_deployment gets a kubectl rollout-status
   command per auto-deployed app/gatekeeper; the deployment step's
   custom_values get one entry per secret/connect-string/registry-secret
   value that needs exporting from Codefresh's own pipeline variables;
   prepare_deployment's harness-deployment command gets its $ENV/$PARAMS/
   $PATHS placeholders substituted from the project's env list, include/
   exclude config and layered root paths.
9. Every step left falsy (an unfilled template placeholder) or an empty
   parallel container is pruned, matching legacy's own "remove useless
   steps" filter; surviving parallel containers get their inner steps
   key-sorted for a stable diff; if the template declares a `stages` list,
   the whole step dict is finally re-ordered to match it.
10. Every image reference emitted anywhere (build/publish/test/task args)
    uses the literal `${{REGISTRY}}` pipeline-variable placeholder
    (CHCodefresh.qualify), never a concretely resolved registry string - see
    the module-level rationale above.

write_env_file() is a separate, related entry point: it writes the
per-image TAG/EXISTS variables (consumed by step 2's skip-when condition and
step 8's $PATHS-adjacent exports) at *pipeline run time*, by checking what
already exists in the registry - never at generation time, since that's
exactly the kind of fact that can't be baked into the committed file.
"""

import re
from functools import lru_cache

from ch_cli_tools.secrets import is_cloudharness_managed, is_secret_config, secret_value
from ch_cli_tools.utils import check_image_exists_in_registry  # type: ignore

from .model import KEY_TASK_IMAGES, CHValues, register_file
from .utils import dict_merge, pipeline_relative_path  # type: ignore

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


def _to_codefresh_path(path, relative_to) -> str:
    return str(pipeline_relative_path(path, relative_to))


def _env_key(name: str) -> str:
    return name.replace("-", "_").upper()


def _tag_variable(name: str) -> str:
    return f"{_env_key(name)}_TAG"


def _tag_reference(name: str) -> str:
    return "${{%s}}" % _tag_variable(name)


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
        return "${{REGISTRY}}/%s" % image_name

    def _context_for(self, entity):
        return entity.dockerfile.resolve_context(self.path.parent).resolve_for_build(
            self.path.parent
        )

    def _working_directory_for(self, context) -> str:
        abs_context_path = (self.path.parent / context.path).resolve()
        return str(
            pipeline_relative_path(
                abs_context_path, self.path.parent, boundary=self.project.root
            )
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
            args[_env_key(dep.name)] = (
                f"{self.qualify(dep.image_name)}:{_tag_reference(dep.name)}"
            )
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
            "working_directory": self._working_directory_for(context),
            "dockerfile": str(context.dockerfile.path),
            "tag": _tag_reference(entity.name),
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
        return entity.name, step

    def _collect_git_clone_steps(self, project):
        steps = {}
        for app in project.involved_apps:
            if isinstance(app, str) or not project._is_buildable_app(app):
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
            "candidate": f"{self.qualify(entity.image_name)}:{_tag_reference(entity.name)}",
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
            if isinstance(app, str) or not project._is_buildable_app(app):
                continue
            commands = app.test.unit.commands
            if not commands:
                continue
            steps[f"{app.name}_ut"] = {
                "title": f"Unit tests for {app.name}",
                "commands": commands,
                "image": f"{self.qualify(app.image_name)}:{_tag_reference(app.name)}",
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
            if isinstance(app, str) or not project._is_buildable_app(app):
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
            if isinstance(app, str) or not project._is_buildable_app(app):
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
        steps[key]["image"] = (
            f"{self.qualify(test_image.image_name)}:{_tag_reference(test_image.name)}"
        )

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

    def _prune_useless_steps(self, steps: dict) -> dict:
        return {
            name: step
            for name, step in steps.items()
            if step and (step.get("type") != "parallel" or step.get("steps"))
        }

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

        publish_container = steps.setdefault(
            KEY_PUBLISH, {"type": "parallel", "steps": {}}
        )
        if publish_container is not None:
            publish_container.setdefault("steps", {}).update(publish_steps)

        unit_test_steps = self._collect_unit_test_steps(project)
        unit_test_container = steps.setdefault(
            KEY_UNIT_TESTS, {"type": "parallel", "steps": {}}
        )
        if unit_test_container is not None:
            unit_test_container.setdefault("steps", {}).update(unit_test_steps)

        clone_steps = self._collect_git_clone_steps(project)
        if clone_steps:
            clone_container = steps.setdefault(
                KEY_CLONE_DEPENDENCIES, {"type": "parallel", "steps": {}}
            )
            if clone_container is not None:
                clone_container.setdefault("steps", {}).update(clone_steps)

        for key, image_name, collect in (
            (KEY_API_TESTS, "test-api", self._collect_api_test_steps),
            (KEY_E2E_TESTS, "test-e2e", self._collect_e2e_test_steps),
        ):
            if steps.get(key):
                steps[key].setdefault("scale", {}).update(collect(project))
                self._wire_test_image(project, steps, key, image_name, build_steps)

        build_parallel_container = steps.setdefault(
            KEY_BUILD_PARALLEL, {"type": "parallel", "steps": {}}
        )
        if build_parallel_container is not None:
            for index, group in enumerate(self._batch_build_steps(build_steps)):
                group_step = dict(build_parallel_container)
                group_step["title"] = f"Build parallel step {index + 1}"
                group_step["steps"] = group
                steps[f"{KEY_BUILD_PARALLEL}_{index}"] = group_step

        if steps.get(KEY_WAIT_DEPLOYMENT):
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

        steps = self._prune_useless_steps(steps)
        steps = self._sort_parallel_steps(steps)
        stages = base.get("stages")
        if stages:
            steps = self._order_steps_by_stage(steps, stages)
        base["steps"] = steps

        if write_on_disk:
            self.write(base, output_path=output_path)

        return base
