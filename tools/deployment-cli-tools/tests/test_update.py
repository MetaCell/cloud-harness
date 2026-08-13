import subprocess

import pytest

from ch_cli_tools import update
from ch_cli_tools.update import (
    Project,
    PackageManager,
    UpdateError,
    ensure_yarn_available,
    find_js_projects,
    find_python_projects,
)


def write_base_image(root, name, area="common-images"):
    directory = root / "infrastructure" / area / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "Dockerfile").write_text("FROM python:3.12\n")


def write_python_app(root, relative, *, dockerfile_body=None, installed_by_dockerfile=True,
                     dockerfile_in_parent=False):
    directory = root / "applications" / relative
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "requirements.txt").write_text("flask\n")
    where = directory.parent if dockerfile_in_parent else directory
    if dockerfile_body is None:
        dockerfile_body = ("FROM base\nRUN pip install -r requirements.txt\n"
                           if installed_by_dockerfile else "FROM base\nADD . /\n")
    (where / "Dockerfile").write_text(dockerfile_body)
    return directory


def write_project(directory, *lock_files, package_json=True):
    directory.mkdir(parents=True, exist_ok=True)
    if package_json:
        (directory / "package.json").write_text('{"name": "x"}')
    for lock_file in lock_files:
        (directory / lock_file).write_text("")
    return directory


def test_finds_yarn_and_npm_projects(tmp_path):
    write_project(tmp_path / "frontend", "yarn.lock")
    write_project(tmp_path / "e2e", "package-lock.json")

    assert find_js_projects(tmp_path) == [
        Project(tmp_path / "e2e", PackageManager.NPM),
        Project(tmp_path / "frontend", PackageManager.YARN),
    ]


def test_project_with_both_lock_files_is_returned_once_per_manager(tmp_path):
    # The end to end tests are installed with npm by harness-test and with yarn
    # by the docker build, so both lock files are live and both must be updated.
    write_project(tmp_path / "e2e", "yarn.lock", "package-lock.json")

    assert find_js_projects(tmp_path) == [
        Project(tmp_path / "e2e", PackageManager.YARN),
        Project(tmp_path / "e2e", PackageManager.NPM),
    ]


def test_lock_file_without_package_json_is_not_a_project(tmp_path):
    # applications/workflows carries a stub package-lock.json and no package.json.
    write_project(tmp_path / "stub", "package-lock.json", package_json=False)

    assert find_js_projects(tmp_path) == []


def test_package_json_without_lock_file_is_skipped(tmp_path):
    # Application templates ship a package.json but no lock file to update.
    write_project(tmp_path / "template")

    assert find_js_projects(tmp_path) == []


def test_vendored_dependencies_are_ignored(tmp_path):
    write_project(tmp_path / "frontend", "yarn.lock")
    write_project(tmp_path / "frontend" / "node_modules" / "dep", "yarn.lock")
    write_project(tmp_path / "frontend" / ".yarn" / "cache" / "dep", "package-lock.json")

    assert find_js_projects(tmp_path) == [Project(tmp_path / "frontend", PackageManager.YARN)]


def test_lock_file_path(tmp_path):
    assert Project(tmp_path, PackageManager.YARN).lock_file == tmp_path / "yarn.lock"
    assert Project(tmp_path, PackageManager.NPM).lock_file == tmp_path / "package-lock.json"
    assert Project(tmp_path, PackageManager.PIP).lock_file == tmp_path / "pylock.toml"


def test_finds_application_requirements(tmp_path):
    # A literal FROM is used verbatim as the lock generation image.
    backend = write_python_app(tmp_path, "myapp/backend")

    assert find_python_projects(tmp_path) == [Project(backend, PackageManager.PIP, "base")]


def test_requirements_installed_by_a_dockerfile_one_level_up_are_found(tmp_path):
    # applications/samples/backend/requirements.txt is installed by
    # applications/samples/Dockerfile, which sits one directory above it.
    backend = write_python_app(tmp_path, "samples/backend", dockerfile_in_parent=True)

    assert find_python_projects(tmp_path) == [Project(backend, PackageManager.PIP, "base")]


def test_base_image_is_resolved_from_the_build_arg(tmp_path):
    # The chain comes from the leading ARG block, the same way skaffold and
    # codefresh wire build dependencies. A repository can name its images
    # anything: the arg is the image name uppercased, dashes as underscores.
    backend = write_python_app(tmp_path, "myapp/backend", dockerfile_body=(
        "ARG MY_DJANGO\n"
        "FROM $MY_DJANGO\n"
        "COPY ./pylock.toml /usr/src/app/\n"
        "RUN pip3 install --no-cache-dir -r pylock.toml\n"
    ))

    # Also the regression for the pylock switch: this Dockerfile no longer
    # mentions requirements.txt at all, and must still be discovered.
    assert find_python_projects(tmp_path) == [
        Project(backend, PackageManager.PIP, "my-django")]


def test_base_images_are_scanned_like_the_generators_do(tmp_path):
    # Enumerated with the same helpers skaffold uses over the infrastructure
    # folders, including a cloud-harness checkout in a downstream repository
    # and images the downstream repository defines itself.
    write_base_image(tmp_path, "cloudharness-flask")
    write_base_image(tmp_path, "cloudharness-frontend-build", area="base-images")
    write_base_image(tmp_path / "cloud-harness", "cloudharness-base", area="base-images")
    write_base_image(tmp_path, "my-django")

    assert update.find_base_images(tmp_path) == {
        "cloudharness-flask", "cloudharness-frontend-build", "cloudharness-base", "my-django"}


def test_the_last_python_stage_wins_in_a_multistage_build(tmp_path):
    # samples builds its frontend first; the python base is the later stage,
    # even though the frontend build image is part of the dependency chain too.
    backend = write_python_app(tmp_path, "samples/backend", dockerfile_in_parent=True,
                               dockerfile_body=(
        "ARG CLOUDHARNESS_FRONTEND_BUILD\n"
        "ARG CLOUDHARNESS_FLASK\n"
        "FROM $CLOUDHARNESS_FRONTEND_BUILD as frontend\n"
        "RUN yarn build\n"
        "FROM $CLOUDHARNESS_FLASK\n"
        "RUN pip3 install -r pylock.toml\n"
    ))

    assert find_python_projects(tmp_path) == [
        Project(backend, PackageManager.PIP, "cloudharness-flask")]


def test_requirements_no_image_installs_are_skipped(tmp_path):
    # applications/workflows/tasks/send-result-event carries a requirements.txt
    # its Dockerfile never installs, naming a package that exists nowhere.
    write_python_app(tmp_path, "workflows/tasks/send-result-event", installed_by_dockerfile=False)

    assert find_python_projects(tmp_path) == []


def test_only_applications_are_locked(tmp_path):
    # Base images, libraries and tools install into the base images, which are
    # deliberately left unlocked.
    for area in ("infrastructure/base-images/cloudharness-base", "libraries/models", "tools/cli"):
        directory = tmp_path / area
        directory.mkdir(parents=True)
        (directory / "requirements.txt").write_text("flask\n")
        (directory / "Dockerfile").write_text("FROM x\nRUN pip install -r requirements.txt\n")

    assert find_python_projects(tmp_path) == []


def fake_run(monkeypatch, yarn_versions):
    """Stub out every subprocess call, handing back the given yarn versions in turn."""
    calls = []
    versions = list(yarn_versions)

    def _run(command, cwd, check=True, **kwargs):
        calls.append(command)
        stdout = versions.pop(0) if command[:2] == ["yarn", "--version"] else ""
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(update, "_run", _run)
    return calls


def answer(monkeypatch, *, interactive, reply=True):
    monkeypatch.setattr(update.sys.stdin, "isatty", lambda: interactive)
    monkeypatch.setattr(update, "confirm", lambda _question: reply)


def test_current_yarn_is_left_alone(tmp_path, monkeypatch):
    calls = fake_run(monkeypatch, ["4.18.0"])
    answer(monkeypatch, interactive=True)

    ensure_yarn_available(tmp_path)

    assert calls == [["yarn", "--version"]]


def test_old_yarn_is_not_touched_without_a_terminal(tmp_path, monkeypatch):
    # A CI run must never be left hanging on a prompt it cannot answer.
    calls = fake_run(monkeypatch, ["1.22.22"])
    answer(monkeypatch, interactive=False)

    with pytest.raises(UpdateError, match="corepack enable"):
        ensure_yarn_available(tmp_path)

    assert ["corepack", "enable"] not in calls


def test_old_yarn_is_not_touched_when_declined(tmp_path, monkeypatch):
    calls = fake_run(monkeypatch, ["1.22.22"])
    answer(monkeypatch, interactive=True, reply=False)

    with pytest.raises(UpdateError, match="corepack enable"):
        ensure_yarn_available(tmp_path)

    assert ["corepack", "enable"] not in calls


def test_old_yarn_is_upgraded_when_accepted(tmp_path, monkeypatch):
    calls = fake_run(monkeypatch, ["1.22.22", "4.18.0", "4.18.0"])
    answer(monkeypatch, interactive=True, reply=True)

    ensure_yarn_available(tmp_path)

    assert ["corepack", "enable"] in calls


def test_yarn_is_probed_inside_a_project_not_at_the_root(tmp_path, monkeypatch):
    # corepack reads the version from the packageManager field, and falls back to
    # its own default - still yarn 1.x - anywhere that field does not apply. Probing
    # the root would therefore report an ancient yarn on a correctly set up machine.
    write_project(tmp_path / "frontend", "yarn.lock")
    probed = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: probed.append(cwd))
    monkeypatch.setattr(update, "update_project", lambda project, **kwargs: True)

    update.update_dependencies(tmp_path)

    assert probed == [tmp_path / "frontend"]


def test_yarn_is_not_probed_when_no_yarn_project_exists(tmp_path, monkeypatch):
    write_project(tmp_path / "e2e", "package-lock.json")
    probed = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: probed.append(cwd))
    monkeypatch.setattr(update, "update_project", lambda project, **kwargs: True)

    update.update_dependencies(tmp_path)

    assert probed == []


def test_every_project_is_handled_by_default(tmp_path, monkeypatch):
    write_project(tmp_path / "frontend", "yarn.lock")
    write_project(tmp_path / "e2e", "package-lock.json")
    handled = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: None)
    monkeypatch.setattr(update, "update_project",
                        lambda project, **kwargs: handled.append(project) or True)

    update.update_dependencies(tmp_path)

    assert len(handled) == 2


def test_declined_projects_are_skipped(tmp_path, monkeypatch):
    write_project(tmp_path / "frontend", "yarn.lock")
    write_project(tmp_path / "e2e", "package-lock.json")
    handled = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: None)
    monkeypatch.setattr(update, "update_project",
                        lambda project, **kwargs: handled.append(project) or True)

    update.update_dependencies(tmp_path, should_update=lambda project: "frontend" in project)

    assert [p.path.name for p in handled] == ["frontend"]


def test_declined_projects_are_skipped_when_auditing(tmp_path, monkeypatch):
    write_project(tmp_path / "frontend", "yarn.lock")
    audited = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: None)
    monkeypatch.setattr(update, "audit", lambda project: audited.append(project) or True)

    update.update_dependencies(tmp_path, audit_only=True, should_update=lambda _: False)

    assert audited == []


def test_a_shadowed_corepack_shim_is_reported(tmp_path, monkeypatch):
    # corepack writes next to the node binary; another yarn earlier in PATH wins.
    fake_run(monkeypatch, ["1.22.22", "1.22.22"])
    answer(monkeypatch, interactive=True, reply=True)

    with pytest.raises(UpdateError, match="shadowing"):
        ensure_yarn_available(tmp_path)


def test_python_lock_is_generated_in_the_base_image(tmp_path, monkeypatch):
    write_base_image(tmp_path, "cloudharness-flask")
    backend = write_python_app(tmp_path, "myapp/backend", dockerfile_body=(
        "ARG CLOUDHARNESS_FLASK\nFROM $CLOUDHARNESS_FLASK\nRUN pip3 install -r pylock.toml\n"))
    commands = []

    def _run(command, cwd, check=True, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='lock-version = "1.0"\n', stderr="")

    monkeypatch.setattr(update, "_run", _run)

    update.update_dependencies(tmp_path, registry="reg", tag="v1")

    docker_run = next(c for c in commands if c[:2] == ["docker", "run"])
    assert "reg/cloudharness-flask:v1" in docker_run
    assert f"{backend}:/lock:ro" in docker_run
    script = docker_run[-1]
    assert "pip install --uploaded-prior-to=P7D -r requirements.txt" in script
    assert "pip lock --uploaded-prior-to=P7D -r requirements.txt -c /tmp/constraints.txt -o /tmp/pylock.toml" in script
    # The lock must reach stdout only through the final cat: pip logs resolution
    # progress to stdout, which corrupted the lock when it was streamed directly.
    assert script.endswith("cat /tmp/pylock.toml")
    assert (backend / "pylock.toml").read_text() == 'lock-version = "1.0"\n'


def test_the_skaffold_image_name_is_used_when_the_build_config_exists(tmp_path, monkeypatch):
    # harness-deployment prefixes built images with the deployment name; the
    # lock must be generated in the image `skaffold build` actually produced.
    write_base_image(tmp_path, "cloudharness-flask")
    (tmp_path / "skaffold.yaml").write_text(
        "build:\n  artifacts:\n  - image: cloud-harness/cloudharness-flask\n")
    write_python_app(tmp_path, "myapp/backend", dockerfile_body=(
        "ARG CLOUDHARNESS_FLASK\nFROM $CLOUDHARNESS_FLASK\nRUN pip3 install -r pylock.toml\n"))
    commands = []

    def _run(command, cwd, check=True, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='lock-version = "1.0"\n', stderr="")

    monkeypatch.setattr(update, "_run", _run)

    update.update_dependencies(tmp_path)

    docker_run = next(c for c in commands if c[:2] == ["docker", "run"])
    assert "cloud-harness/cloudharness-flask:latest" in docker_run


def test_an_explicit_registry_wins_over_the_skaffold_name(tmp_path, monkeypatch):
    write_base_image(tmp_path, "cloudharness-flask")
    (tmp_path / "skaffold.yaml").write_text(
        "build:\n  artifacts:\n  - image: cloud-harness/cloudharness-flask\n")
    write_python_app(tmp_path, "myapp/backend", dockerfile_body=(
        "ARG CLOUDHARNESS_FLASK\nFROM $CLOUDHARNESS_FLASK\nRUN pip3 install -r pylock.toml\n"))
    commands = []

    def _run(command, cwd, check=True, **kwargs):
        commands.append(command)
        return subprocess.CompletedProcess(command, 0, stdout='lock-version = "1.0"\n', stderr="")

    monkeypatch.setattr(update, "_run", _run)

    update.update_dependencies(tmp_path, registry="reg", tag="v1")

    docker_run = next(c for c in commands if c[:2] == ["docker", "run"])
    assert "reg/cloudharness-flask:v1" in docker_run


def test_cooldown_days_reaches_both_package_managers(tmp_path, monkeypatch):
    write_python_app(tmp_path, "myapp/backend")
    write_project(tmp_path / "frontend", "yarn.lock")
    calls = []

    def _run(command, cwd, check=True, env=None, **kwargs):
        calls.append((command, env))
        return subprocess.CompletedProcess(command, 0, stdout='lock-version = "1.0"\n', stderr="")

    monkeypatch.setattr(update, "_run", _run)
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: None)

    update.update_dependencies(tmp_path, cooldown_days=10)

    docker_run, _ = next(c for c in calls if c[0][:2] == ["docker", "run"])
    assert "--uploaded-prior-to=P10D" in docker_run[-1]
    _, yarn_env = next(c for c in calls if c[0][:2] == ["yarn", "install"])
    assert yarn_env["YARN_NPM_MINIMAL_AGE_GATE"] == "10d"


def test_without_the_flag_the_repository_cooldown_configuration_rules(tmp_path, monkeypatch):
    # No env override: yarn keeps following the npmMinimalAgeGate in .yarnrc.yml,
    # so a repository with its own window is not silently overridden.
    write_python_app(tmp_path, "myapp/backend")
    write_project(tmp_path / "frontend", "yarn.lock")
    calls = []

    def _run(command, cwd, check=True, env=None, **kwargs):
        calls.append((command, env))
        return subprocess.CompletedProcess(command, 0, stdout='lock-version = "1.0"\n', stderr="")

    monkeypatch.setattr(update, "_run", _run)
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: None)

    update.update_dependencies(tmp_path)

    docker_run, _ = next(c for c in calls if c[0][:2] == ["docker", "run"])
    assert "--uploaded-prior-to=P7D" in docker_run[-1]
    _, yarn_env = next(c for c in calls if c[0][:2] == ["yarn", "install"])
    assert yarn_env is None


def test_a_missing_base_image_is_reported_with_the_fix(tmp_path, monkeypatch):
    write_python_app(tmp_path, "myapp/backend")

    def _run(command, cwd, check=True, **kwargs):
        returncode = 1 if command[:3] == ["docker", "image", "inspect"] else 0
        return subprocess.CompletedProcess(command, returncode, stdout="", stderr="")

    monkeypatch.setattr(update, "_run", _run)

    with pytest.raises(UpdateError, match="not found locally"):
        update.update_dependencies(tmp_path)


def test_a_failed_yarn_refresh_puts_the_old_lock_back(tmp_path, monkeypatch):
    # A failed or interrupted resolution (e.g. every candidate of a pin
    # quarantined by the cooldown) must not leave a partial lock behind:
    # every later yarn command in the project crashes on it.
    project = Project(write_project(tmp_path, "yarn.lock"), PackageManager.YARN)
    project.lock_file.write_text("the good lock")

    def _run(command, cwd, check=True, **kwargs):
        if command[:2] == ["yarn", "install"]:
            project.lock_file.write_text("partial garbage")
            raise UpdateError("resolution failed")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(update, "_run", _run)

    with pytest.raises(UpdateError):
        update.update_lock_file(project)

    assert project.lock_file.read_text() == "the good lock"


def test_yarn_audits_after_the_refresh_not_before(tmp_path, monkeypatch):
    # Auditing resolves from the lock file alone, so a stale or partial lock
    # crashes the audit outright; the refresh has to come first.
    project = Project(write_project(tmp_path, "yarn.lock"), PackageManager.YARN)
    order = []
    monkeypatch.setattr(update, "update_lock_file",
                        lambda p, **kwargs: order.append("update"))
    monkeypatch.setattr(update, "audit", lambda p: order.append("audit") or True)

    assert update.update_project(project)

    assert order == ["update", "audit"]


def test_audit_only_needs_no_docker(tmp_path, monkeypatch):
    write_python_app(tmp_path, "myapp/backend")

    def _run(command, cwd, check=True, **kwargs):
        raise AssertionError(f"audit-only ran a command: {command}")

    monkeypatch.setattr(update, "_run", _run)

    assert update.update_dependencies(tmp_path, audit_only=True) == []
