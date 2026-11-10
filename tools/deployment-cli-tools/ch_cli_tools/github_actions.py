"""Generates GitHub Actions workflows from a CHProject.

The GitHub Actions pipeline does what the Codefresh one does - build every image
the deployment needs, run the unit tests, deploy the helm chart, wait for the
rollout, run the API/E2E tests, publish (re-tag) the images - with the same
content-hash skip: the `prepare` job runs `harness-deployment --write-env` and
turns `deployment/.env` into job outputs, and every `build-<image>` job is only
scheduled when `<IMAGE>_TAG_EXISTS` is not set. Like codefresh.yaml, the
workflow is generated once and committed, so everything only known at run time
stays a `${{ ... }}` expression (vars, secrets, prepare outputs).

What differs from Codefresh, and shapes the template:
- GitHub only runs workflows found in .github/workflows/, so that is where the
  file goes: `.github/workflows/cloudharness-<env>.yaml` in the project root.
- Triggers (`on:`) are part of the file, hence of the per-environment template.
- Every job runs on a fresh runner: each one checks out what it needs, images
  travel between jobs through the registry, the helm chart and the merged
  `.overrides/` contexts travel as a workflow artifact.
- A job whose `needs` were skipped is skipped too unless its `if` says
  otherwise; since build jobs are skipped on purpose, every dependent job gets
  a guard (`apply_needs_guards`) that tolerates skipped builds but not failures.
  A job deciding for itself - an `if` using always()/cancelled()/failure() - is
  left alone. The template uses that for `publish`, which waits for the API/E2E
  tests and runs only if none failed.

Template mechanics (`github-template.yaml` + `github-template-<env>.yaml`, layered
across cloud-harness and the project exactly like the Codefresh templates):
- `jobs.build`, `jobs.build-test-images`, `jobs.tests-unit`, `jobs.tests-api`
  and `jobs.tests-e2e` are prototypes, expanded into one job per image/app at
  their position; a `null` or missing prototype means that kind of job is not
  generated. Inside a prototype `$CH_NAME`, `$CH_IMAGE` and `$CH_TAG` stand for
  the image being expanded.
- A string item in a `steps` list is a fragment the generator fills:
  `$GIT_CLONES`, `$PUBLISH_STEPS`, `$HELM_SECRETS_STEPS`, `$ROLLOUT_STEPS`,
  `$TEST_STEPS`, and `$KUBE_AUTH`, the steps giving kubectl/helm access to the
  cluster, taken from the template's own `cloudharness.kube_auth` list so a
  project changes the authentication method in one place. The top-level
  `cloudharness` section is for the generator only and never reaches GitHub.
- `$ENV`, `$PARAMS` and `$PATHS` are substituted everywhere, as in Codefresh.
- A template key matching an expanded job id (`jobs.build-myapp`) is merged over
  the generated job, so one image can get a bigger runner or extra steps; such a
  key is dropped when its image is not part of the deployment being generated.
- `runs-on` defaults to the `CH_GITHUB_RUNNER` repository/organization variable
  (build jobs: `CH_GITHUB_BUILD_RUNNER` first), read when the workflow runs,
  falling back to CHDeployConfig.ci_runner (`CH_GITHUB_RUNNER` in the generating
  shell, default ubuntu-latest). A template `runs-on` always wins.
"""

import copy
import json
import logging
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from ruamel.yaml.scalarstring import LiteralScalarString

from . import ci
from .model import CHValues, register_file
from .utils import GeneratedYAML, dict_merge, pipeline_relative_path  # type: ignore

WORKFLOW_FILE_NAME = "cloudharness.yaml"
DEFAULT_RUNNER = "ubuntu-latest"
RUNNER_VARIABLE = "CH_GITHUB_RUNNER"
BUILD_RUNNER_VARIABLE = "CH_GITHUB_BUILD_RUNNER"

JOB_PREPARE = "prepare"
JOB_BUILD = "build"
JOB_BUILD_TEST_IMAGES = "build-test-images"
JOB_UNIT_TESTS = "tests-unit"
JOB_API_TESTS = "tests-api"
JOB_E2E_TESTS = "tests-e2e"
JOB_DEPLOY = "deploy"
JOB_WAIT_DEPLOYMENT = "wait-deployment"
JOB_PUBLISH = "publish"
PROTOTYPE_JOBS = (JOB_BUILD, JOB_BUILD_TEST_IMAGES, JOB_UNIT_TESTS, JOB_API_TESTS, JOB_E2E_TESTS)

FRAGMENT_GIT_CLONES = "$GIT_CLONES"
FRAGMENT_PUBLISH_STEPS = "$PUBLISH_STEPS"
FRAGMENT_HELM_SECRETS = "$HELM_SECRETS_STEPS"
FRAGMENT_ROLLOUT = "$ROLLOUT_STEPS"
FRAGMENT_TEST = "$TEST_STEPS"
FRAGMENT_KUBE_AUTH = "$KUBE_AUTH"

SETTINGS_KEY = "cloudharness"  # generator-only template section, stripped from the workflow
SETTING_KUBE_AUTH = "kube_auth"

STEP_IMAGES = "images"  # prepare step appending deployment/.env to $GITHUB_OUTPUT
STEP_CHECK = "check"  # build step asking the registry whether the image exists
STEP_BUILD = "build"  # build step running docker/build-push-action

TEST_IMAGE_API = "test-api"
TEST_IMAGE_E2E = "test-e2e"
TEST_HOME = "/home/test"
DEFAULT_E2E_COMMANDS = ("npx puppeteer browsers install chrome", "yarn test")

_INVALID_JOB_ID_CHARS = re.compile(r"[^A-Za-z0-9_-]")
_INVALID_SECRET_CHARS = re.compile(r"[^A-Z0-9_]")
_EXPRESSION = re.compile(r"^\$\{\{(.*)\}\}$", re.DOTALL)
_STATUS_FUNCTION = re.compile(r"\b(always|cancelled|failure)\(\)")
_GITHUB_REPOSITORY = re.compile(
    r"^(?:https?://github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"([^/\s]+/[^/\s]+?)(?:\.git)?/?$"
)
_CONTEXT_REFERENCE = re.compile(r"(?<![\w.])(vars|secrets)\.([A-Za-z0-9_]+)")


# --- pure helpers ---------------------------------------------------------------


def job_id(name: str) -> str:
    """A valid GitHub job id: `[A-Za-z_][A-Za-z0-9_-]*`."""
    cleaned = _INVALID_JOB_ID_CHARS.sub("-", name)
    return cleaned if re.match(r"[A-Za-z_]", cleaned) else f"_{cleaned}"


def substitute_vars(node, mapping: dict[str, str]):
    """Replace word-bounded `$KEY` placeholders in every string of a nested structure."""
    if not mapping:
        return node
    pattern = re.compile(r"\$(" + "|".join(re.escape(key) for key in mapping) + r")\b")

    def visit(value):
        if isinstance(value, str):
            return pattern.sub(lambda match: mapping[match.group(1)], value)
        if isinstance(value, dict):
            return {key: visit(item) for key, item in value.items()}
        if isinstance(value, list):
            return [visit(item) for item in value]
        return value

    return visit(node)


def expand_steps(steps, fragments: dict[str, list]) -> list:
    """Replace string items of a steps list by the fragment steps they name."""
    expanded = []
    for step in steps or []:
        if isinstance(step, str):
            if step not in fragments:
                raise ValueError(
                    f"Unknown step fragment {step!r}; known fragments: {sorted(fragments)}"
                )
            expanded.extend(copy.deepcopy(fragments[step]))
        else:
            expanded.append(step)
    return expanded


def step_by_id(steps, step_id: str):
    return next(
        (step for step in steps if isinstance(step, dict) and step.get("id") == step_id),
        None,
    )


def strip_expression(value) -> str:
    value = str(value).strip()
    match = _EXPRESSION.match(value)
    return match.group(1).strip() if match else value


def combine_conditions(*parts) -> str:
    """AND the given `if` expressions, with or without their `${{ }}` wrapper."""
    conditions = [strip_expression(part) for part in parts if part not in (None, "")]
    conditions = [condition for condition in conditions if condition]
    if not conditions:
        return ""
    if len(conditions) == 1:
        return "${{ %s }}" % conditions[0]
    return "${{ %s }}" % " && ".join(f"({condition})" for condition in conditions)


def normalize_needs(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)


def needs_guard(needs, skippable) -> str:
    """The condition letting a job run after skipped (but never failed) dependencies.

    Jobs without an `if` of their own are expected to succeed; the others
    (build jobs skipped when their image exists, tests skipped on request) may
    be skipped.
    """
    guard = [
        "!cancelled()",
        "!contains(needs.*.result, 'failure')",
        "!contains(needs.*.result, 'cancelled')",
    ]
    guard += [f"needs.{need}.result == 'success'" for need in needs if need not in skippable]
    return " && ".join(guard)


def rewrite_needs(jobs: dict, expansions: dict[str, list[str]]) -> None:
    """Replace prototype ids in every `needs` by the ids they expanded to; unknown ids raise."""
    for name, job in jobs.items():
        if "needs" not in job:
            continue
        needs = []
        for dependency in normalize_needs(job["needs"]):
            targets = [dependency] if dependency in jobs else expansions.get(dependency)
            if targets is None:
                raise ValueError(f"Job {name!r} needs unknown job {dependency!r}")
            for target in targets:
                if target != name and target not in needs:
                    needs.append(target)
        if needs:
            job["needs"] = needs
        else:
            del job["needs"]


def apply_needs_guards(jobs: dict) -> None:
    """Add the `needs_guard` to every job with dependencies, except those that
    already decide themselves with always()/cancelled()/failure()."""
    skippable = {name for name, job in jobs.items() if job.get("if")}
    for job in jobs.values():
        needs = normalize_needs(job.get("needs"))
        if not needs:
            continue
        own = job.get("if")
        if own and _STATUS_FUNCTION.search(str(own)):
            continue
        job["if"] = combine_conditions(own, needs_guard(needs, skippable))


def as_literal_blocks(node):
    """Multi-line strings as `|` blocks (trailing spaces stripped), tuples as lists."""
    if isinstance(node, dict):
        return {key: as_literal_blocks(value) for key, value in node.items()}
    if isinstance(node, (list, tuple)):
        return [as_literal_blocks(value) for value in node]
    if isinstance(node, str) and "\n" in node:
        text = "\n".join(line.rstrip() for line in node.splitlines())
        if node.endswith("\n"):
            text += "\n"
        return LiteralScalarString(text)
    return node


RESERVED_SECRET_PREFIX = "GITHUB_"
SECRET_PREFIX = "CH_"


def github_secret_name(variable: str) -> str:
    """The GitHub secret holding a pipeline variable: the Codefresh variable name
    with invalid characters replaced, prefixed with `CH_` when it starts with the
    `GITHUB_` prefix GitHub reserves (e.g. a `github_client_id` secret)."""
    name = _INVALID_SECRET_CHARS.sub("_", variable.upper())
    if name.startswith(RESERVED_SECRET_PREFIX):
        renamed = f"{SECRET_PREFIX}{name}"
        logging.warning(
            "Secret variable %s starts with the prefix GitHub reserves: the workflow reads it "
            "from the %s secret instead",
            name,
            renamed,
        )
        return renamed
    return name


def github_repository(url: str) -> str | None:
    """`owner/repo` of a github.com clone URL (https or ssh), None for any other host."""
    match = _GITHUB_REPOSITORY.match(url.strip())
    return match.group(1) if match else None


def referenced_names(workflow) -> dict[str, set[str]]:
    """The `vars.*` and `secrets.*` names a workflow references."""
    found: dict[str, set[str]] = {"vars": set(), "secrets": set()}

    def visit(value):
        if isinstance(value, str):
            for context, name in _CONTEXT_REFERENCE.findall(value):
                found[context].add(name)
        elif isinstance(value, dict):
            for item in value.values():
                visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)

    visit(workflow)
    return found


def runner_expression(variables, default) -> str:
    """A `runs-on` taking the runner from the first of the given GitHub variables
    that is set when the workflow runs, `default` (one label or a list) otherwise."""
    if isinstance(default, str):
        fallback = "'%s'" % default.replace("'", "''")
    else:
        fallback = "fromJSON('%s')" % json.dumps(list(default)).replace("'", "''")
    return "${{ %s }}" % " || ".join([*(f"vars.{name}" for name in variables), fallback])


def prepare_output(key: str) -> str:
    return "${{ needs.%s.outputs.%s }}" % (JOB_PREPARE, key)


def tag_output(name: str) -> str:
    return prepare_output(ci.tag_variable(name))


@dataclass(frozen=True)
class BuildContext:
    path: str  # docker build context, relative to the workflow's checkout root
    dockerfile: str  # Dockerfile, relative to the context


# --- generator ------------------------------------------------------------------


@register_file(
    "github_template",
    lambda root: root / "deployment-configuration" / "github-template.yaml",
)
class CHGithubActionsTemplate(CHValues):
    @lru_cache
    def all_values(self):
        layer = self.containing_project
        own = self.merge_with_envs(self.project.config.envs)
        if layer.base is None:
            return own
        return dict_merge(layer.base.github_template.all_values(), own)


@register_file(
    "github_actions",
    lambda root: root / ".github" / "workflows" / WORKFLOW_FILE_NAME,
    only_env=True,
)
class CHGithubActions(CHValues):
    def qualify(self, image_name: str) -> str:
        return "${{ vars.REGISTRY }}/%s" % image_name

    def _runner(self, *variables) -> str:
        default = self.project.config.ci_runner or DEFAULT_RUNNER
        if "," in default:
            default = [label.strip() for label in default.split(",") if label.strip()]
        return runner_expression([*variables, RUNNER_VARIABLE], default)

    def _pipeline_path(self, path) -> str:
        """A path as the workflow sees it: relative to the project checkout, with
        cloud-harness under ./cloud-harness."""
        project = self.project
        return str(
            pipeline_relative_path(
                Path(path),
                project.root,
                boundary=project.root,
                cloudharness_root=project.all_layers()[-1].root,
            )
        )

    def _context_for(self, entity) -> BuildContext:
        root = self.project.root
        context = entity.dockerfile.resolve_context(root).resolve_for_build(root)
        return BuildContext(
            self._pipeline_path(root / context.path), str(context.dockerfile.path)
        )

    def _dependencies(self, entity) -> list:
        dependencies = []
        for dependency in self.project._combined_dependencies(entity):
            if isinstance(dependency, str):
                continue
            if dependency.name not in {d.name for d in dependencies}:
                dependencies.append(dependency)
        return dependencies

    def _buildable_apps(self) -> list:
        return [
            app
            for app in self.project.involved_apps
            if not isinstance(app, str) and app.is_buildable
        ]

    def _entities(self) -> dict:
        """Every image to build: buildable involved apps, their tasks and the
        build dependencies the deployment needs - the same set helm's
        `task-images` and `write_env_file` cover."""
        project = self.project
        entities = {}
        for app in project.involved_apps:
            if isinstance(app, str):
                continue
            if app.is_buildable:
                entities[app.name] = app
            for task in app.buildable_tasks:
                entities[task.name] = task
        app_names = {app.name for app in project.involved_apps if not isinstance(app, str)}
        for name, dependency in project.all_build_dependencies(app_names).items():
            entities.setdefault(name, dependency)
        return entities

    # --- generated fragments ---

    def _git_clone_steps(self, entities) -> list[dict]:
        steps = []
        for entity in entities:
            for dependency in getattr(entity, "git_dependencies", None) or []:
                url = dependency["url"]
                ref = dependency.get("branch_tag")
                repo_name = Path(url).name.split(".")[0]
                destination = Path(self._pipeline_path(entity.path)) / "dependencies"
                if dependency.get("path"):
                    destination = destination / dependency["path"]
                destination = destination / repo_name
                repository = github_repository(url)
                if repository:
                    with_ = {
                        "repository": repository,
                        "path": str(destination),
                        "token": "${{ secrets.GH_PAT || github.token }}",
                    }
                    if ref:
                        with_["ref"] = ref
                    steps.append(
                        {
                            "name": f"Clone {repo_name}",
                            "uses": "actions/checkout@v4",
                            "with": with_,
                        }
                    )
                else:
                    branch = f' --branch "{ref}"' if ref else ""
                    steps.append(
                        {
                            "name": f"Clone {repo_name}",
                            "run": f'git clone --depth 1{branch} "{url}" "{destination}"',
                        }
                    )
        return steps

    def _publish_steps(self, entities: dict) -> list[dict]:
        steps = []
        for name, entity in entities.items():
            steps.append(
                {
                    "name": f"Publish {name}",
                    "if": "${{ vars.%s_PUBLISH_SKIP == '' }}" % ci.env_key(name),
                    "env": {
                        "SOURCE": f"{self.qualify(entity.image_name)}:{tag_output(name)}",
                        "TARGET": "${{ vars.REGISTRY_PUBLISH_URL || vars.REGISTRY }}/%s"
                        % entity.image_name,
                        "PUBLISH_TAG": prepare_output("publish_tag"),
                    },
                    "run": 'docker buildx imagetools create -t "$TARGET:$PUBLISH_TAG" '
                    '-t "$TARGET:latest" "$SOURCE"',
                }
            )
        return steps

    def _helm_secrets_steps(self) -> list[dict]:
        """One step writing every pipeline-supplied secret to a file and exporting the
        matching `--set-file` arguments as HELM_SET_ARGS: no quoting or escaping of the
        values is needed, and no secret ever appears on a command line."""
        values = ci.deployment_secret_values(self.project)
        if not values:
            return []
        env: dict[str, str] = {}
        lines = [
            "set -e",
            'secrets_dir="$RUNNER_TEMP/ch-secrets"',
            'mkdir -p "$secrets_dir"',
            'args=""',
        ]
        for index, value in enumerate(values):
            secret = github_secret_name(value.variable)
            env[secret] = "${{ secrets.%s }}" % secret
            key = ".".join(segment.replace(".", "\\.") for segment in value.path)
            lines.append(f"printf '%s' \"${secret}\" > \"$secrets_dir/{index}\"")
            lines.append(f'args="$args --set-file {key}=$secrets_dir/{index}"')
        lines.append('echo "HELM_SET_ARGS=$args" >> "$GITHUB_ENV"')
        return [{"name": "Collect secret values", "env": env, "run": "\n".join(lines) + "\n"}]

    def _rollout_steps(self) -> list[dict]:
        commands = ci.rollout_wait_commands(self.project)
        if not commands:
            return []
        return [{"name": "Wait for the rollouts", "run": "\n".join(commands) + "\n"}]

    def _docker_run_step(self, name, image, commands, env=None, volumes=(), workdir=None):
        env = dict(env or {})
        parts = ["docker run --rm"]
        parts += [f"-e {key}" for key in env]
        parts += [f'-v "{volume}"' for volume in volumes]
        if workdir:
            parts.append(f"-w {workdir}")
        parts.append('"$CH_TEST_IMAGE" sh -c "$CH_TEST_COMMANDS"')
        env["CH_TEST_IMAGE"] = image
        env["CH_TEST_COMMANDS"] = "\n".join(["set -e", *commands]) + "\n"
        return {"name": name, "env": env, "run": " \\\n  ".join(parts)}

    # --- expanded jobs ---

    def _prototype(self, prototype, name, image_name):
        job = copy.deepcopy(prototype)
        job.pop("commands", None)
        return substitute_vars(
            job,
            {
                "CH_NAME": name,
                "CH_IMAGE": self.qualify(image_name),
                "CH_TAG": tag_output(name),
            },
        )

    def _specific_needs(self, prototype, replacements: dict[str, list]) -> list[str]:
        needs = []
        for need in normalize_needs(prototype.get("needs")):
            for target in replacements.get(need, [need]):
                if target and target not in needs:
                    needs.append(target)
        return needs

    def _build_args(self, entity) -> list[str]:
        project = self.project
        args = {"NOCACHE": "${{ github.run_id }}"}
        if project.config.local or project.config.debug:
            args["DEBUG"] = "true"
        for dependency in self._dependencies(entity):
            args[ci.env_key(dependency.name)] = (
                f"{self.qualify(dependency.image_name)}:{tag_output(dependency.name)}"
            )
        args.update(project.all_source_images())
        args.update(getattr(entity, "build_args", None) or {})
        return [f"{key}={value}" for key, value in args.items()]

    def _build_job(self, prototype, entity, build_ids, fragments, extra_tags=()):
        name = entity.name
        image = self.qualify(entity.image_name)
        tag_var = ci.tag_variable(name)
        job = self._prototype(prototype, name, entity.image_name)
        job["name"] = f"Build {name}"
        job.setdefault("runs-on", self._runner(BUILD_RUNNER_VARIABLE))
        job["needs"] = self._specific_needs(
            prototype,
            {
                JOB_BUILD: [],
                JOB_BUILD_TEST_IMAGES: [],
                JOB_PREPARE: [JOB_PREPARE],
            },
        ) or [JOB_PREPARE]
        if JOB_PREPARE not in job["needs"]:
            job["needs"].insert(0, JOB_PREPARE)
        for dependency in self._dependencies(entity):
            dependency_job = build_ids.get(dependency.name)
            if dependency_job and dependency_job not in job["needs"]:
                job["needs"].append(dependency_job)
        job["if"] = combine_conditions(
            prototype.get("if"), f"needs.{JOB_PREPARE}.outputs.{tag_var}_EXISTS != '1'"
        )
        steps = expand_steps(
            job.get("steps"),
            {**fragments, FRAGMENT_GIT_CLONES: self._git_clone_steps([entity])},
        )
        build = step_by_id(steps, STEP_BUILD)
        if build is not None:
            context = self._context_for(entity)
            with_ = build.setdefault("with", {})
            with_["context"] = f"./{context.path}"
            with_["file"] = f"./{context.path}/{context.dockerfile}"
            with_["build-args"] = "\n".join(self._build_args(entity))
            tags = [
                f"{image}:{tag_output(name)}",
                f"{image}:{prepare_output('branch_tag')}",
                *(f"{image}:{tag}" for tag in extra_tags),
            ]
            with_["tags"] = "\n".join(tags)
            forced = (
                f"needs.{JOB_PREPARE}.outputs.force_build == 'all' || "
                f"contains(format(',{{0}},', needs.{JOB_PREPARE}.outputs.force_build), ',{name},')"
            )
            build["if"] = combine_conditions(
                build.get("if"), f"steps.{STEP_CHECK}.outputs.exists != 'true' || {forced}"
            )
        job["steps"] = steps
        return job

    def _unit_test_job(self, prototype, app, build_ids, fragments):
        job = self._prototype(prototype, app.name, app.image_name)
        job["name"] = f"Unit tests {app.name}"
        job["needs"] = self._specific_needs(prototype, {JOB_BUILD: [build_ids.get(app.name)]})
        test_step = self._docker_run_step(
            f"Run {app.name} unit tests",
            f"{self.qualify(app.image_name)}:{tag_output(app.name)}",
            app.test.unit.commands,
        )
        job["steps"] = expand_steps(job.get("steps"), {**fragments, FRAGMENT_TEST: [test_step]})
        return job

    def _test_image_reference(self, name) -> str | None:
        test_image = self.project.test_images.get(name)
        if test_image is None or not test_image.dockerfile.exists():
            return None
        return f"{self.qualify(test_image.image_name)}:{tag_output(name)}"

    def _api_test_job(self, prototype, app, build_ids, fragments):
        url = ci.api_test_url(app, "${{ vars.DOMAIN }}")
        image = self._test_image_reference(TEST_IMAGE_API)
        if url is None or image is None:
            return None
        job = self._prototype(prototype, app.name, app.image_name)
        job["name"] = f"API tests {app.name}"
        job["needs"] = self._specific_needs(
            prototype, {JOB_BUILD_TEST_IMAGES: [build_ids.get(TEST_IMAGE_API)]}
        )
        app_path = self._pipeline_path(app.path)
        test_step = self._docker_run_step(
            f"Run {app.name} API tests",
            image,
            ci.api_test_commands(app, url),
            env=ci.test_environment(app, url),
            volumes=[
                f"$GITHUB_WORKSPACE/{app_path}:{TEST_HOME}",
                "$GITHUB_WORKSPACE/deployment/helm/values.yaml:/opt/cloudharness/resources/allvalues.yaml",
            ],
            workdir=TEST_HOME,
        )
        job["steps"] = expand_steps(job.get("steps"), {**fragments, FRAGMENT_TEST: [test_step]})
        return job

    def _e2e_test_job(self, prototype, app, build_ids, fragments):
        image = self._test_image_reference(TEST_IMAGE_E2E)
        if image is None:
            return None
        url = ci.app_domain(app, "${{ vars.DOMAIN }}")
        job = self._prototype(prototype, app.name, app.image_name)
        job["name"] = f"E2E tests {app.name}"
        job["needs"] = self._specific_needs(
            prototype, {JOB_BUILD_TEST_IMAGES: [build_ids.get(TEST_IMAGE_E2E)]}
        )
        app_path = self._pipeline_path(app.path)
        test_step = self._docker_run_step(
            f"Run {app.name} E2E tests",
            image,
            list(prototype.get("commands") or DEFAULT_E2E_COMMANDS),
            env=ci.test_environment(app, url),
            volumes=[f"$GITHUB_WORKSPACE/{app_path}/test/e2e:{TEST_HOME}/__tests__/{app.name}"],
            workdir=TEST_HOME,
        )
        job["steps"] = expand_steps(job.get("steps"), {**fragments, FRAGMENT_TEST: [test_step]})
        return job

    def _prepare_outputs(self) -> dict[str, str]:
        outputs = {}
        for name in ci.image_tag_names(self.project):
            variable = ci.tag_variable(name)
            for key in (variable, f"{variable}_EXISTS"):
                outputs[key] = "${{ steps.%s.outputs.%s }}" % (STEP_IMAGES, key)
        return outputs

    def _expand_jobs(self, jobs: dict, settings: dict | None = None) -> dict:
        project = self.project
        settings = settings or {}
        removed = [key for key, job in jobs.items() if job is None]
        jobs = {key: job for key, job in jobs.items() if job is not None}

        entities = self._entities()
        apps = self._buildable_apps()
        unit_apps = [app for app in apps if app.test.unit.commands]
        api_apps = (
            [app for app in apps if ci.has_api_tests(app) and app.openapi.server_urls]
            if JOB_API_TESTS in jobs
            else []
        )
        e2e_apps = [app for app in apps if ci.has_e2e_tests(app)] if JOB_E2E_TESTS in jobs else []
        test_entities = {}
        if JOB_BUILD_TEST_IMAGES in jobs and JOB_BUILD in jobs:
            for name, users in ((TEST_IMAGE_API, api_apps), (TEST_IMAGE_E2E, e2e_apps)):
                image = project.test_images.get(name)
                if users and image is not None and image.dockerfile.exists():
                    test_entities[name] = image

        build_ids = {name: job_id(f"{JOB_BUILD}-{name}") for name in [*entities, *test_entities]}
        unit_ids = {app.name: job_id(f"{JOB_UNIT_TESTS}-{app.name}") for app in unit_apps}
        api_ids = {app.name: job_id(f"{JOB_API_TESTS}-{app.name}") for app in api_apps}
        e2e_ids = {app.name: job_id(f"{JOB_E2E_TESTS}-{app.name}") for app in e2e_apps}
        generated_ids = {*build_ids.values(), *unit_ids.values(), *api_ids.values(), *e2e_ids.values()}

        fragments = {
            FRAGMENT_GIT_CLONES: self._git_clone_steps(apps),
            FRAGMENT_PUBLISH_STEPS: self._publish_steps({**entities, **test_entities}),
            FRAGMENT_HELM_SECRETS: self._helm_secrets_steps(),
            FRAGMENT_ROLLOUT: self._rollout_steps(),
            FRAGMENT_TEST: [],
            FRAGMENT_KUBE_AUTH: list(settings.get(SETTING_KUBE_AUTH) or []),
        }

        overlays = {key: job for key, job in jobs.items() if key in generated_ids}
        overlay_prefixes = tuple(f"{prototype}-" for prototype in PROTOTYPE_JOBS)
        # a prototype left out or removed with null expands to nothing: the jobs
        # needing it simply drop the dependency
        expansions: dict[str, list[str]] = {key: [] for key in [*PROTOTYPE_JOBS, *removed]}
        result: dict[str, dict] = {}

        def expand(key, items, make):
            ids = []
            for item in items:
                expanded_id, job = make(item)
                if job is None:
                    continue
                result[expanded_id] = job
                ids.append(expanded_id)
            expansions[key] = ids

        for key, job in jobs.items():
            if key in overlays:
                continue
            if key == JOB_BUILD:
                expand(
                    key,
                    entities.items(),
                    lambda item: (
                        build_ids[item[0]],
                        self._build_job(job, item[1], build_ids, fragments),
                    ),
                )
            elif key == JOB_BUILD_TEST_IMAGES:
                prototype = dict_merge(jobs[JOB_BUILD], job) if JOB_BUILD in jobs else None
                expand(
                    key,
                    test_entities.items() if prototype else [],
                    lambda item: (
                        build_ids[item[0]],
                        self._build_job(
                            prototype, item[1], build_ids, fragments, extra_tags=("latest",)
                        ),
                    ),
                )
            elif key == JOB_UNIT_TESTS:
                expand(
                    key,
                    unit_apps,
                    lambda app: (
                        unit_ids[app.name],
                        self._unit_test_job(job, app, build_ids, fragments),
                    ),
                )
            elif key == JOB_API_TESTS:
                expand(
                    key,
                    api_apps,
                    lambda app: (
                        api_ids[app.name],
                        self._api_test_job(job, app, build_ids, fragments),
                    ),
                )
            elif key == JOB_E2E_TESTS:
                expand(
                    key,
                    e2e_apps,
                    lambda app: (
                        e2e_ids[app.name],
                        self._e2e_test_job(job, app, build_ids, fragments),
                    ),
                )
            elif key.startswith(overlay_prefixes):
                # an overlay for an image/app that is not part of this deployment
                continue
            else:
                job = copy.deepcopy(job)
                if key == JOB_PREPARE:
                    outputs = dict(job.get("outputs") or {})
                    for output, value in self._prepare_outputs().items():
                        outputs.setdefault(output, value)
                    job["outputs"] = outputs
                job["steps"] = expand_steps(job.get("steps"), fragments)
                result[key] = job

        for key, overlay in overlays.items():
            if key in result:
                result[key] = dict_merge(result[key], overlay)

        rewrite_needs(result, expansions)
        apply_needs_guards(result)
        return result

    def generate(self, write_on_disk=True, output_path=None):
        project = self.project

        base = copy.deepcopy(project.github_template.all_values())
        if not base:
            logging.warning(
                "No GitHub Actions template found for environments %s: workflow not generated",
                project.config.envs,
            )
            return {}

        base = substitute_vars(base, ci.placeholder_values(project, self._pipeline_path))
        settings = base.pop(SETTINGS_KEY, None) or {}
        base["jobs"] = self._expand_jobs(base.get("jobs") or {}, settings)
        # the env template contributes name/on after the base keys: put them first
        base = {key: base[key] for key in ("name", "on") if key in base} | {
            key: value for key, value in base.items() if key not in ("name", "on")
        }

        runner = self._runner()
        for job in base["jobs"].values():
            job.setdefault("runs-on", runner)

        references = referenced_names(base)
        logging.info(
            "GitHub Actions workflow %s expects repository variables %s and secrets %s",
            self.path.name,
            ", ".join(sorted(references["vars"])) or "-",
            ", ".join(sorted(references["secrets"])) or "-",
        )

        if write_on_disk:
            self.write(base, output_path=output_path)

        return base

    @classmethod
    def write_on_disk(cls, path, data) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        yaml = GeneratedYAML()
        yaml.width = 4096
        yaml.indent(mapping=2, sequence=4, offset=2)
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(as_literal_blocks(data), f)
