"""Refresh dependency lock files and report known vulnerabilities.

`npm audit fix` only exists for npm-managed projects. Yarn ships no equivalent
auto-fix command, so yarn projects are re-resolved against the ranges already
declared in their package.json, which is what pulls in a patched in-range
version. Neither path edits package.json unless --upgrade is passed.

Both package managers apply the release-age cooldown configured in the root
.yarnrc.yml, so an update never pulls a version published inside the window.
"""

import logging
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable

from .utils import confirm

MIN_YARN_MAJOR = 4

# Directories that never hold a project we own.
EXCLUDED_DIRS = frozenset({
    "node_modules", ".yarn", ".git", ".tox", ".venv", "dist", "build", "__pycache__",
})


class UpdateError(Exception):
    """A dependency update step could not be completed."""


class PackageManager(Enum):
    YARN = "yarn"
    NPM = "npm"

    @property
    def lock_file_name(self) -> str:
        return "yarn.lock" if self is PackageManager.YARN else "package-lock.json"


@dataclass(frozen=True)
class JsProject:
    path: Path
    package_manager: PackageManager

    @property
    def lock_file(self) -> Path:
        return self.path / self.package_manager.lock_file_name

    def __str__(self) -> str:
        return f"{self.path} [{self.package_manager.value}]"


def find_js_projects(root: Path) -> list[JsProject]:
    """Every directory holding a package.json next to a lock file.

    Discovery keys off the lock file rather than the file name alone: a
    package-lock.json with no package.json beside it is a leftover, not a
    project. A directory carrying both lock files is returned once per manager,
    because both are really used - harness-test installs the end to end tests
    with npm while the docker image builds them with yarn.
    """
    projects: list[JsProject] = []
    for package_json in sorted(root.rglob("package.json")):
        if EXCLUDED_DIRS.intersection(package_json.parts):
            continue
        directory = package_json.parent
        for manager in PackageManager:
            if (directory / manager.lock_file_name).exists():
                projects.append(JsProject(directory, manager))
    return projects


def _run(command: list[str], cwd: Path, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    logging.info("%s $ %s", cwd, " ".join(command))
    try:
        return subprocess.run(command, cwd=cwd, check=check, capture_output=capture, text=True)
    except FileNotFoundError as e:
        raise UpdateError(f"{command[0]} is not installed but is needed to update {cwd}") from e
    except subprocess.CalledProcessError as e:
        raise UpdateError(f"`{' '.join(command)}` failed in {cwd}") from e


def _yarn_major(cwd: Path) -> int:
    version = _run(["yarn", "--version"], cwd, capture=True).stdout.strip()
    try:
        return int(version.split(".")[0])
    except ValueError as e:
        raise UpdateError(f"Could not read the yarn version, got '{version}'") from e


def _enable_corepack(cwd: Path) -> None:
    """Install the yarn version pinned in package.json through corepack."""
    try:
        _run(["corepack", "enable"], cwd)
    except UpdateError as e:
        raise UpdateError(
            "`corepack enable` failed. It writes to the directory holding the node binary, "
            "which may not be writable: retry with sudo, or point it somewhere on your PATH "
            "with `corepack enable --install-directory <dir>`."
        ) from e


def ensure_yarn_available(cwd: Path) -> None:
    """Make sure the yarn on PATH can read a berry lock file, offering to install it.

    The yarn shipped with node is still 1.x and cannot read the lock files, so
    rather than only reporting that, offer the one command that fixes it.
    """
    if _yarn_major(cwd) >= MIN_YARN_MAJOR:
        return

    logging.warning(
        "The yarn on PATH is too old to read the lock files in this repository, "
        "which need yarn %d. Corepack can install the version pinned in package.json.",
        MIN_YARN_MAJOR,
    )
    if not (sys.stdin.isatty() and confirm("Run `corepack enable` now?")):
        raise UpdateError(
            "Run `corepack enable` once to pick up the yarn version pinned in package.json."
        )

    _enable_corepack(cwd)

    if _yarn_major(cwd) < MIN_YARN_MAJOR:
        raise UpdateError(
            f"corepack ran, but yarn in {cwd} is still older than yarn {MIN_YARN_MAJOR} "
            f"(resolved to {shutil.which('yarn')}). Either another yarn earlier in PATH is "
            f"shadowing the corepack shim, or that directory has no packageManager field for "
            f"corepack to honour, leaving it on its built-in default."
        )
    logging.info("corepack enabled, yarn is now %s", _run(["yarn", "--version"], cwd, capture=True).stdout.strip())


def audit(project: JsProject) -> bool:
    """Report known vulnerabilities. Returns True when the audit came back clean.

    A failing audit is a finding, not an error: the caller decides what to do
    about it, so the non-zero exit code is not raised.
    """
    if project.package_manager is PackageManager.YARN:
        command = ["yarn", "npm", "audit", "--all", "--recursive"]
    else:
        command = ["npm", "audit"]
    return _run(command, project.path, check=False).returncode == 0


def fix_vulnerabilities(project: JsProject) -> None:
    """Apply the in-range fixes a vulnerability report suggests.

    Only npm can do this on its own. For yarn the equivalent effect comes from
    re-resolving the lock file, which update_lock_file() does next anyway.
    """
    if project.package_manager is PackageManager.NPM:
        _run(["npm", "audit", "fix", "--package-lock-only"], project.path, check=False)


def update_lock_file(project: JsProject, upgrade: bool = False) -> None:
    """Move the lock file to the newest versions the package.json ranges allow.

    With upgrade=True the declared ranges themselves are raised, which can cross
    major versions and rewrites package.json.
    """
    if project.package_manager is PackageManager.YARN:
        if upgrade:
            _run(["yarn", "up", "*"], project.path)
            return
        # Yarn keeps any resolution that still satisfies its range, even when a
        # newer one is available, so the lock file has to be re-resolved from
        # scratch to actually move. package.json is left alone either way.
        project.lock_file.unlink(missing_ok=True)
        _run(["yarn", "install", "--mode=update-lockfile"], project.path)
    else:
        command = ["npm", "update", "--package-lock-only"]
        if upgrade:
            command.append("--save")
        _run(command, project.path)


def update_project(project: JsProject, upgrade: bool = False) -> bool:
    """Audit and refresh a single project.

    Returns True when nothing vulnerable is left once the update has run, so a
    finding that the refresh resolved on its own is not reported to the caller.
    """
    was_clean = audit(project)
    if not was_clean:
        logging.warning("%s reported vulnerabilities, attempting to resolve them", project)
        fix_vulnerabilities(project)

    update_lock_file(project, upgrade=upgrade)

    # Nothing was wrong to begin with, so there is nothing to confirm.
    if was_clean:
        return True
    return audit(project)


def update_dependencies(root: Path, upgrade: bool = False, audit_only: bool = False,
                        should_update: Callable[[str], bool] = lambda _: True) -> list[JsProject]:
    """Audit and refresh every JavaScript project below root.

    should_update is asked about each project before it is touched, so a caller
    can run interactively. Skipped projects are not reported back.

    Returns the projects whose audit reported vulnerabilities, so the caller can
    exit non-zero when something still needs a human.
    """
    projects = find_js_projects(root)
    if not projects:
        logging.warning("No JavaScript project with a lock file found under %s", root)
        return []

    logging.info("Updating %d project(s):\n  %s", len(projects), "\n  ".join(str(p) for p in projects))

    # Whether yarn is current is a property of the machine, not of a project, so
    # check it once up front rather than prompting for each yarn project found.
    # It has to be probed from inside a project though: corepack resolves the
    # version from the packageManager field, and reports its own default - which
    # is still yarn 1.x - anywhere that field does not apply, such as the root.
    yarn_project = next((p for p in projects if p.package_manager is PackageManager.YARN), None)
    if yarn_project:
        ensure_yarn_available(yarn_project.path)

    unresolved: list[JsProject] = []
    for project in projects:
        if not should_update(str(project)):
            logging.info("Skipping %s", project)
            continue
        logging.info("--- %s", project)
        if audit_only:
            if not audit(project):
                unresolved.append(project)
            continue
        if not update_project(project, upgrade=upgrade):
            unresolved.append(project)
    return unresolved
