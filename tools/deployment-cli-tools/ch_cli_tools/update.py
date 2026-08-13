"""Refresh dependency lock files and report known vulnerabilities.

`npm audit fix` only exists for npm-managed projects. Yarn ships no equivalent
auto-fix command, so yarn projects are re-resolved against the ranges already
declared in their package.json, which is what pulls in a patched in-range
version. Neither path edits package.json unless --upgrade is passed.

Python applications are locked to a PEP 751 pylock.toml next to their
requirements.txt. The lock is generated inside a throwaway container from the
application's own base image: the requirements are installed there first, so
resolution happens on top of what the image already provides, and the lock
records that environment rather than one resolved from scratch. The lock
toolchain never enters the deploy images, and only applications are locked -
the base images stay deliberately unlocked, so an application image keeps
inheriting their updates.

Every resolution applies the same 7 day release age cooldown, so an update
never pulls a version published inside the window.
"""

import logging
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Optional

from cloudharness_utils.constants import BASE_IMAGES_PATH, STATIC_IMAGES_PATH

from .utils import (app_name_from_path, confirm, find_dockerfiles_paths,
                    guess_build_dependencies_from_dockerfile, yaml)

MIN_YARN_MAJOR = 4

# Ignore package versions published in the last 7 days. Mirrors the
# --uploaded-prior-to=P7D carried by every pip install in the repository.
DEFAULT_COOLDOWN_DAYS = 7

REQUIREMENTS = "requirements.txt"
PYLOCK = "pylock.toml"

# Directories that never hold a project we own.
EXCLUDED_DIRS = frozenset({
    "node_modules", ".yarn", ".git", ".tox", ".venv", "dist", "build", "__pycache__",
})


class UpdateError(Exception):
    """A dependency update step could not be completed."""


class PackageManager(Enum):
    YARN = "yarn"
    NPM = "npm"
    PIP = "pip"

    @property
    def lock_file_name(self) -> str:
        return {
            PackageManager.YARN: "yarn.lock",
            PackageManager.NPM: "package-lock.json",
            PackageManager.PIP: PYLOCK,
        }[self]


JS_MANAGERS = (PackageManager.YARN, PackageManager.NPM)


@dataclass(frozen=True)
class Project:
    path: Path
    package_manager: PackageManager
    # For python projects, the image the lock is generated in: either the name
    # of a cloudharness base image or a literal reference from a FROM line.
    base_image: Optional[str] = None

    @property
    def lock_file(self) -> Path:
        return self.path / self.package_manager.lock_file_name

    def __str__(self) -> str:
        return f"{self.path} [{self.package_manager.value}]"


def find_js_projects(root: Path) -> list[Project]:
    """Every directory holding a package.json next to a lock file.

    Discovery keys off the lock file rather than the file name alone: a
    package-lock.json with no package.json beside it is a leftover, not a
    project. A directory carrying both lock files is returned once per manager,
    because both are really used - harness-test installs the end to end tests
    with npm while the docker image builds them with yarn.
    """
    projects: list[Project] = []
    for package_json in sorted(root.rglob("package.json")):
        if EXCLUDED_DIRS.intersection(package_json.parts):
            continue
        directory = package_json.parent
        for manager in JS_MANAGERS:
            if (directory / manager.lock_file_name).exists():
                projects.append(Project(directory, manager))
    return projects


def find_base_images(root: Path) -> set[str]:
    """The names of every base and common image the repository builds.

    Enumerated exactly the way the skaffold and codefresh generators enumerate
    what they build: find_dockerfiles_paths over the infrastructure folders. In
    a downstream deployment repository the cloud-harness images live in the
    cloud-harness checkout beside the applications, so that is scanned too, and
    images the downstream repository defines itself are covered the same way.
    """
    images: set[str] = set()
    for base in (root, root / "cloud-harness"):
        for images_path in (BASE_IMAGES_PATH, STATIC_IMAGES_PATH):
            for path in find_dockerfiles_paths(str(base / images_path)):
                images.add(app_name_from_path(path.split("/")[-1]))
    return images


def _installing_dockerfile(directory: Path) -> Optional[Path]:
    """The Dockerfile beside or above the requirements that installs them.

    Not every requirements.txt is live: applications/workflows/tasks/
    send-result-event carries one that its Dockerfile never installs, naming a
    package that exists nowhere. Locking that would only fail. The Dockerfiles
    install either the requirements or the lock generated from them.
    """
    for candidate in (directory, directory.parent):
        for dockerfile in sorted(candidate.glob("*Dockerfile*")):
            content = dockerfile.read_text(errors="ignore")
            if REQUIREMENTS in content or PYLOCK in content:
                return dockerfile
    return None


def _base_image_name(dockerfile: Path) -> Optional[str]:
    """The image of the last resolvable stage of a Dockerfile.

    The dependency chain comes from guess_build_dependencies_from_dockerfile,
    the same helper the skaffold and codefresh generators wire build
    dependencies with, so the lock is generated against what those generators
    consider the chain. The FROM lines then pick which dependency the final
    stage derives from - a frontend build stage before the python one does not
    shadow it. A literal `FROM image:tag` is taken verbatim, which covers
    applications that build directly from a public image.
    """
    chain = guess_build_dependencies_from_dockerfile(str(dockerfile))
    candidate = None
    for line in dockerfile.read_text(errors="ignore").splitlines():
        match = re.match(r"\s*FROM\s+(\S+)", line, re.IGNORECASE)
        if not match:
            continue
        reference = match.group(1)
        argument = re.fullmatch(r"\$\{?(\w+)\}?", reference)
        if argument:
            # The same arg -> name convention the generators use for aliases.
            name = argument.group(1).lower().replace("_", "-")
            if name in chain:
                candidate = name
        else:
            candidate = reference
    return candidate


def find_python_projects(root: Path) -> list[Project]:
    """Application requirements that an image actually installs.

    Restricted to ./applications on purpose. Libraries, tools and the base
    images are installed into the base images, which are left unlocked so that
    every application keeps picking their updates up.
    """
    applications = root / "applications"
    if not applications.is_dir():
        return []
    projects: list[Project] = []
    for requirements in sorted(applications.rglob(REQUIREMENTS)):
        if EXCLUDED_DIRS.intersection(requirements.parts):
            continue
        dockerfile = _installing_dockerfile(requirements.parent)
        if dockerfile is None:
            continue
        base_image = _base_image_name(dockerfile)
        if base_image is None:
            logging.warning("%s: cannot determine the base image from %s, skipping",
                            requirements.parent, dockerfile)
            continue
        projects.append(Project(requirements.parent, PackageManager.PIP, base_image))
    return projects


def find_projects(root: Path) -> list[Project]:
    return find_js_projects(root) + find_python_projects(root)


def _skaffold_images(root: Path) -> dict[str, str]:
    """Image name -> full reference from the generated skaffold.yaml.

    harness-deployment prefixes every image it builds with the deployment name
    (e.g. cloud-harness/cloudharness-flask), so what `skaffold build` produces
    is not the bare image name. When the build configuration has been
    generated, resolve through it so the locks use exactly the images skaffold
    built.
    """
    skaffold_file = root / "skaffold.yaml"
    if not skaffold_file.exists():
        return {}
    with open(skaffold_file) as f:
        config = yaml.load(f)
    artifacts = (config.get("build") or {}).get("artifacts") or []
    return {artifact["image"].split("/")[-1]: artifact["image"]
            for artifact in artifacts if artifact.get("image")}


def _image_reference(name: str, registry: str, tag: str, built_images: set[str],
                     skaffold_images: dict[str, str]) -> str:
    """The reference of the image a lock is generated in.

    An explicit --registry wins; without one, an image found in the generated
    skaffold.yaml is used under the name skaffold built it with. A literal
    reference from a FROM line already carries its own registry and tag.
    """
    if name not in built_images:
        return name
    if registry:
        return f"{registry.rstrip('/')}/{name}:{tag}"
    return f"{skaffold_images.get(name, name)}:{tag}"


def _run(command: list[str], cwd: Path, check: bool = True, capture: bool = False,
         capture_stdout: bool = False, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    logging.info("%s $ %s", cwd, " ".join(command))
    kwargs = {"capture_output": True} if capture else (
        {"stdout": subprocess.PIPE} if capture_stdout else {})
    if env is not None:
        kwargs["env"] = env
    try:
        return subprocess.run(command, cwd=cwd, check=check, text=True, **kwargs)
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


def ensure_docker_available(cwd: Path) -> None:
    """Fail early when the docker daemon is not reachable."""
    try:
        _run(["docker", "info"], cwd, capture=True)
    except UpdateError as e:
        raise UpdateError(
            "Docker is needed to generate the python locks inside the base images, but it is "
            "not available: install it or start the docker daemon."
        ) from e


def _ensure_image_available(image: str, cwd: Path) -> None:
    """Checked per project rather than up front, so an interactive run can
    update the projects whose base image exists and skip the rest."""
    if _run(["docker", "image", "inspect", image], cwd, check=False, capture=True).returncode != 0:
        raise UpdateError(
            f"Base image {image} was not found locally. Locks are generated inside the "
            f"application's base image: run `harness-deployment` to generate the build "
            f"configuration, then `skaffold build` to build the images. Alternatively, "
            f"point at existing images with --registry and --tag."
        )


def audit(project: Project) -> bool:
    """Report known vulnerabilities. Returns True when the audit came back clean.

    A failing audit is a finding, not an error: the caller decides what to do
    about it, so the non-zero exit code is not raised.
    """
    if project.package_manager is PackageManager.PIP:
        # pip has no audit command, and shelling out to a third party scanner is
        # a bigger decision than this tool should be making on its own.
        logging.info("%s: pip has no audit command, only refreshing the lock file", project)
        return True
    if project.package_manager is PackageManager.YARN:
        command = ["yarn", "npm", "audit", "--all", "--recursive"]
    else:
        command = ["npm", "audit"]
    return _run(command, project.path, check=False).returncode == 0


def fix_vulnerabilities(project: Project) -> None:
    """Apply the in-range fixes a vulnerability report suggests.

    Only npm can do this on its own. For yarn the equivalent effect comes from
    re-resolving the lock file, which update_lock_file() does next anyway.
    """
    if project.package_manager is PackageManager.NPM:
        _run(["npm", "audit", "fix", "--package-lock-only"], project.path, check=False)


def _generate_python_lock(project: Project, image: str, cooldown_days: Optional[int]) -> None:
    """Run pip lock in a throwaway container from the application's base image.

    The requirements are installed first, so the resolution happens on top of
    the packages the base image already provides instead of from an empty
    environment, and the freeze of that environment constrains the lock to the
    versions that will really be present. The lock is written inside the
    container and only cat'ed to stdout at the end - pip logs its resolution
    progress to stdout too, so streaming the lock directly would corrupt it.
    Writing it back host-side keeps the mount read-only and no root-owned file
    appears in the working tree.
    """
    _ensure_image_available(image, project.path)
    cooldown = f"P{DEFAULT_COOLDOWN_DAYS if cooldown_days is None else cooldown_days}D"
    script = " && ".join([
        "python -m pip install --upgrade pip 1>&2",
        f"pip install --uploaded-prior-to={cooldown} -r {REQUIREMENTS} --prefer-binary 1>&2",
        "pip freeze --exclude-editable > /tmp/constraints.txt",
        f"pip lock --uploaded-prior-to={cooldown} -r {REQUIREMENTS} -c /tmp/constraints.txt"
        f" -o /tmp/{PYLOCK} 1>&2",
        f"cat /tmp/{PYLOCK}",
    ])
    command = ["docker", "run", "--rm",
               "-v", f"{project.path.absolute()}:/lock:ro", "-w", "/lock",
               image, "sh", "-c", script]
    lock = _run(command, project.path, capture_stdout=True).stdout
    if not lock.strip():
        raise UpdateError(f"pip lock produced no output for {project}")
    project.lock_file.write_text(lock)


def update_lock_file(project: Project, upgrade: bool = False, image: Optional[str] = None,
                     cooldown_days: Optional[int] = None) -> None:
    """Move the lock file to the newest versions the declared ranges allow.

    With upgrade=True the declared ranges themselves are raised, which can cross
    major versions and rewrites package.json. requirements.txt is never rewritten:
    pip has no equivalent, so upgrade is not meaningful there.

    cooldown_days overrides the release age window. Without it, yarn follows the
    npmMinimalAgeGate configured in .yarnrc.yml and pip uses the default, so the
    repository configuration stays authoritative unless explicitly overridden.
    """
    # Yarn reads the same setting from .yarnrc.yml; only override when asked to.
    env = None
    if cooldown_days is not None:
        env = {**os.environ, "YARN_NPM_MINIMAL_AGE_GATE": f"{cooldown_days}d"}

    if project.package_manager is PackageManager.PIP:
        if upgrade:
            logging.info("%s: pip cannot raise the ranges in %s, edit it by hand to do that",
                         project, REQUIREMENTS)
        _generate_python_lock(project, image, cooldown_days)
    elif project.package_manager is PackageManager.YARN:
        if upgrade:
            _run(["yarn", "up", "*"], project.path, env=env)
            return
        # Yarn keeps any resolution that still satisfies its range, even when a
        # newer one is available, so the lock file has to be re-resolved from
        # scratch to actually move. package.json is left alone either way.
        # A failed or interrupted resolution can leave a partial lock file
        # behind, which breaks every later yarn command in the project - hold
        # on to the old lock and put it back when the new one does not land.
        backup = project.lock_file.read_text() if project.lock_file.exists() else None
        project.lock_file.unlink(missing_ok=True)
        try:
            _run(["yarn", "install", "--mode=update-lockfile"], project.path, env=env)
        except BaseException:
            if backup is None:
                project.lock_file.unlink(missing_ok=True)
            else:
                project.lock_file.write_text(backup)
            raise
    else:
        command = ["npm", "update", "--package-lock-only"]
        if upgrade:
            command.append("--save")
        _run(command, project.path)


def update_project(project: Project, upgrade: bool = False, image: Optional[str] = None,
                   cooldown_days: Optional[int] = None) -> bool:
    """Audit and refresh a single project.

    Returns True when nothing vulnerable is left once the update has run, so a
    finding that the refresh resolved on its own is not reported to the caller.

    npm audits before fixing, because `npm audit fix` works from the report.
    Yarn audits after the update instead: its audit resolves from the lock file
    alone, so a stale or partial lock crashes it outright, and the refresh is
    what fixes anything fixable anyway.
    """
    if project.package_manager is PackageManager.NPM:
        was_clean = audit(project)
        if not was_clean:
            logging.warning("%s reported vulnerabilities, attempting to resolve them", project)
            fix_vulnerabilities(project)
        update_lock_file(project, upgrade=upgrade, image=image, cooldown_days=cooldown_days)
        return was_clean or audit(project)

    update_lock_file(project, upgrade=upgrade, image=image, cooldown_days=cooldown_days)
    if project.package_manager is PackageManager.YARN:
        return audit(project)
    return True


def _check_toolchain(projects: list[Project], audit_only: bool) -> None:
    """Check the machine once, before any project is touched.

    Yarn has to be probed from inside a project: corepack resolves the version
    from the packageManager field, and reports its own default - still yarn
    1.x - anywhere that field does not apply, such as the root.

    Docker is only needed to generate python locks, which an audit-only run
    never does.
    """
    yarn_project = next((p for p in projects if p.package_manager is PackageManager.YARN), None)
    if yarn_project:
        ensure_yarn_available(yarn_project.path)

    python_project = next((p for p in projects if p.package_manager is PackageManager.PIP), None)
    if python_project and not audit_only:
        ensure_docker_available(python_project.path)


def update_dependencies(root: Path, upgrade: bool = False, audit_only: bool = False,
                        should_update: Callable[[str], bool] = lambda _: True,
                        registry: str = "", tag: str = "latest",
                        cooldown_days: Optional[int] = None) -> list[Project]:
    """Audit and refresh every project below root.

    should_update is asked about each project before it is touched, so a caller
    can run interactively. Skipped projects are not reported back.

    Returns the projects whose audit reported vulnerabilities, so the caller can
    exit non-zero when something still needs a human.
    """
    projects = find_projects(root)
    if not projects:
        logging.warning("No project with a lock file found under %s", root)
        return []

    logging.info("Updating %d project(s):\n  %s", len(projects), "\n  ".join(str(p) for p in projects))

    _check_toolchain(projects, audit_only)

    built_images = find_base_images(root)
    skaffold_images = _skaffold_images(root)

    unresolved: list[Project] = []
    for project in projects:
        if not should_update(str(project)):
            logging.info("Skipping %s", project)
            continue
        logging.info("--- %s", project)
        if audit_only:
            if not audit(project):
                unresolved.append(project)
            continue
        image = None
        if project.package_manager is PackageManager.PIP:
            image = _image_reference(project.base_image, registry, tag, built_images, skaffold_images)
        if not update_project(project, upgrade=upgrade, image=image, cooldown_days=cooldown_days):
            unresolved.append(project)
    return unresolved
