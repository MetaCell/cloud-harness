import subprocess

import pytest

from ch_cli_tools import update
from ch_cli_tools.update import (
    JsProject,
    PackageManager,
    UpdateError,
    ensure_yarn_available,
    find_js_projects,
)


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
        JsProject(tmp_path / "e2e", PackageManager.NPM),
        JsProject(tmp_path / "frontend", PackageManager.YARN),
    ]


def test_project_with_both_lock_files_is_returned_once_per_manager(tmp_path):
    # The end to end tests are installed with npm by harness-test and with yarn
    # by the docker build, so both lock files are live and both must be updated.
    write_project(tmp_path / "e2e", "yarn.lock", "package-lock.json")

    assert find_js_projects(tmp_path) == [
        JsProject(tmp_path / "e2e", PackageManager.YARN),
        JsProject(tmp_path / "e2e", PackageManager.NPM),
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

    assert find_js_projects(tmp_path) == [JsProject(tmp_path / "frontend", PackageManager.YARN)]


def test_lock_file_path(tmp_path):
    assert JsProject(tmp_path, PackageManager.YARN).lock_file == tmp_path / "yarn.lock"
    assert JsProject(tmp_path, PackageManager.NPM).lock_file == tmp_path / "package-lock.json"


def fake_run(monkeypatch, yarn_versions):
    """Stub out every subprocess call, handing back the given yarn versions in turn."""
    calls = []
    versions = list(yarn_versions)

    def _run(command, cwd, check=True, capture=False):
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
    monkeypatch.setattr(update, "update_project", lambda project, upgrade=False: True)

    update.update_dependencies(tmp_path)

    assert probed == [tmp_path / "frontend"]


def test_yarn_is_not_probed_when_no_yarn_project_exists(tmp_path, monkeypatch):
    write_project(tmp_path / "e2e", "package-lock.json")
    probed = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: probed.append(cwd))
    monkeypatch.setattr(update, "update_project", lambda project, upgrade=False: True)

    update.update_dependencies(tmp_path)

    assert probed == []


def test_every_project_is_handled_by_default(tmp_path, monkeypatch):
    write_project(tmp_path / "frontend", "yarn.lock")
    write_project(tmp_path / "e2e", "package-lock.json")
    handled = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: None)
    monkeypatch.setattr(update, "update_project",
                        lambda project, upgrade=False: handled.append(project) or True)

    update.update_dependencies(tmp_path)

    assert len(handled) == 2


def test_declined_projects_are_skipped(tmp_path, monkeypatch):
    write_project(tmp_path / "frontend", "yarn.lock")
    write_project(tmp_path / "e2e", "package-lock.json")
    handled = []
    monkeypatch.setattr(update, "ensure_yarn_available", lambda cwd: None)
    monkeypatch.setattr(update, "update_project",
                        lambda project, upgrade=False: handled.append(project) or True)

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
