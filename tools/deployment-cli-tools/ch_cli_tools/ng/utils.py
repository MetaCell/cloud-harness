import hashlib
import json
import re
import shlex
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import dirhash
import xxhash
from cloudharness.utils import dict_merge  # type: ignore
from ruamel.yaml import YAML

from ch_cli_tools.utils import get_git_commit_hash  # type: ignore

if TYPE_CHECKING:
    from .model import CHValues


def resolve_path(d, p, default=None):
    obj = d
    for frag in p.split("."):
        if obj is None:
            return default
        obj = obj.get(frag)
    return obj if obj is not None else default


def merge_with_layer(base: "CHValues", layer: "CHValues"):

    if base is layer or layer.env is None:
        return base.all_raw_values() if base.exists() else {}
    match base.exists(), layer.exists():
        case True, True:
            return dict_merge(base.all_raw_values(), layer.all_raw_values())
        case False, True:
            return layer.all_raw_values()
        case True, False:
            return base.all_raw_values()
        case False, False:
            return {}


# Commands whose argument can be either a JSON exec-form array
# (`CMD ["gunicorn", "app:app"]`) or a plain shell-form string
# (`CMD gunicorn app:app`).
_EXEC_FORM_COMMANDS = {"RUN", "CMD", "ENTRYPOINT", "SHELL", "HEALTHCHECK"}

_LINE_CONTINUATION = re.compile(r"\\\s*$")
_FROM_ALIAS = re.compile(r"\s+AS\s+", re.IGNORECASE)
_LEADING_FLAG = re.compile(r"^--[\w-]+(=\S*)?$")
_VAR_REFERENCE = re.compile(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?$")


def dockerfile_variable_reference(token: str) -> str | None:
    match = _VAR_REFERENCE.match(token)
    return match.group(1) if match else None


def parse_dockerfile(path: Path) -> list[tuple[str, ...]]:
    if not path.exists():
        return []

    instructions: list[tuple[str, ...]] = []
    pending = ""
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if pending:
            line = f"{pending} {line}".strip()
            pending = ""
        if not line or line.startswith("#"):
            continue
        if _LINE_CONTINUATION.search(line):
            pending = _LINE_CONTINUATION.sub("", line).strip()
            continue

        command, _, rest = line.partition(" ")
        command = command.upper()
        rest = rest.strip()
        if not rest:
            instructions.append((command,))
            continue

        if command == "FROM":
            instructions.append((command, *_parse_from(rest)))
        elif command == "ARG":
            instructions.append((command, *_parse_arg(rest)))
        elif command in _EXEC_FORM_COMMANDS and rest.startswith("["):
            instructions.append((command, *_parse_exec_form(rest)))
        else:
            instructions.append((command, *_split_args(rest)))

    return instructions


def _strip_leading_flags(tokens: list[str]) -> list[str]:
    while tokens and _LEADING_FLAG.match(tokens[0]):
        tokens.pop(0)
    return tokens


def _split_args(rest: str) -> list[str]:
    try:
        tokens = shlex.split(rest)
    except ValueError:
        tokens = rest.split()
    return _strip_leading_flags(tokens)


def _parse_from(rest: str) -> tuple[str, ...]:
    # FROM [--platform=<platform>] <image> [AS <name>]
    tokens = _strip_leading_flags(rest.split())
    parts = [part.strip() for part in _FROM_ALIAS.split(" ".join(tokens), maxsplit=1)]
    reference = dockerfile_variable_reference(parts[0])
    if reference is not None:
        parts[0] = reference
    return tuple(parts)


def _parse_arg(rest: str) -> tuple[str, ...]:
    # ARG <name>[=<default>]
    name, has_default, default = rest.partition("=")
    if has_default:
        return (name.strip(), default.strip())
    return (name.strip(),)


def _parse_exec_form(rest: str) -> tuple[str, ...]:
    try:
        parsed = json.loads(rest)
    except ValueError:
        return (rest,)
    if isinstance(parsed, list):
        return tuple(str(item) for item in parsed)
    return (rest,)


CLOUD_HARNESS_DIR_NAME = "cloud-harness"


def pipeline_relative_path(
    path: Path,
    relative_to: Path,
    boundary: Path | None = None,
    cloudharness_root: Path | None = None,
) -> Path:
    rel_parts = path.resolve().relative_to(relative_to.resolve(), walk_up=True).parts
    if rel_parts and rel_parts[0] == "..":
        if boundary is not None:
            try:
                path.resolve().relative_to(boundary.resolve())
            except ValueError:
                pass
            else:
                return Path(*rel_parts)
        if cloudharness_root is not None:
            try:
                suffix = path.resolve().relative_to(cloudharness_root.resolve())
            except ValueError:
                pass
            else:
                return Path(CLOUD_HARNESS_DIR_NAME, *suffix.parts)
    return Path(*rel_parts) if rel_parts else Path(".")


MERGE_DIRNAME = ".overrides"
_MERGE_COPY_IGNORE = shutil.ignore_patterns(
    MERGE_DIRNAME, ".git", "node_modules", ".tox"
)


def _merge_base_chain(entity, source_of, destination: Path) -> None:
    if entity.base is not None:
        _merge_base_chain(entity.base, source_of, destination)
    source = source_of(entity)
    if source.exists():
        shutil.copytree(
            source, destination, dirs_exist_ok=True, ignore=_MERGE_COPY_IGNORE
        )


yaml = YAML(typ="safe")


def get_yaml_parser():
    return yaml


_MERGEABLE_SUFFIXES = {".yaml": yaml, ".yml": yaml, ".json": json}


def env_suffixed_path(path: Path, suffix: str) -> Path:
    """The env-specific sibling of path (values.yaml, dev -> values-dev.yaml)
    - the one naming convention CHValues.path_for_env and
    collect_and_merge_env_specific_files both need."""
    return path.with_name(f"{path.stem}-{suffix}{path.suffix}")


def collect_and_merge_env_specific_files(directory: Path, envs: list[str]) -> None:
    if not envs or not directory.exists():
        return
    for path in directory.rglob("*"):
        codec = _MERGEABLE_SUFFIXES.get(path.suffix.lower())
        if not path.is_file() or codec is None:
            continue
        if any(path.stem.endswith(f"-{env}") for env in envs):
            continue
        for env in envs:
            env_path = env_suffixed_path(path, env)
            if not env_path.exists():
                continue
            with path.open("r", encoding="utf-8") as f:
                base = codec.load(f) or {}
            with env_path.open("r", encoding="utf-8") as f:
                override = codec.load(f) or {}
            with path.open("w", encoding="utf-8") as f:
                codec.dump(dict_merge(base, override), f)


_DEFAULT_IGNORE = (
    "/tasks",
    ".dockerignore",
    ".hypothesis",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".coverage",
)


def _cloned_dependency_repos(directory: Path):
    for child in directory.iterdir():
        if not child.is_dir():
            continue
        if (child / ".git").is_dir():
            yield child
        else:
            yield from _cloned_dependency_repos(child)


class _PruningFilter(dirhash.Filter):
    def include(self, recursion_path):
        if recursion_path.is_dir():
            if recursion_path.is_symlink() and not self.linked_dirs:
                return False
            return self.match_file(recursion_path.relative)
        return super().include(recursion_path)


def content_hash(path: Path) -> str:
    ignore = set(_DEFAULT_IGNORE)
    dockerignore = path / ".dockerignore"
    if dockerignore.exists():
        ignore |= {
            line.strip()
            for line in dockerignore.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        }

    git_hashes = []
    dependencies_path = path / "dependencies"
    if dependencies_path.is_dir():
        ignore.add("/dependencies")
        git_hashes = [
            commit_hash
            for repo in _cloned_dependency_repos(dependencies_path)
            if (commit_hash := get_git_commit_hash(repo))
        ]

    match_patterns = dirhash.get_match_patterns(ignore=ignore)
    filter_ = _PruningFilter(match_patterns=match_patterns)
    protocol = dirhash.Protocol(allow_cyclic_links=True)
    digest = dirhash.dirhash_impl(
        str(path), xxhash.xxh3_64, filter_=filter_, protocol=protocol
    )
    if git_hashes:
        digest = hashlib.sha1(
            (digest + "".join(git_hashes)).encode("utf-8")
        ).hexdigest()
    return digest


_EXCLUDED_WALK_SEGMENTS = {
    "tasks",
    "dependencies",
    "subapps",
    "instances",
    "node_modules",
    ".git",
}


def find_files(path: Path, filename: str) -> list[Path]:
    candidates = []
    for root, dirs, files in path.walk():
        dirs[:] = [d for d in dirs if d not in _EXCLUDED_WALK_SEGMENTS]
        if filename in files:
            candidates.append(root / filename)
    return candidates


def own_dockerfile_path(path: Path) -> Path:
    candidates = find_files(path, "Dockerfile")
    if not candidates:
        return path / "Dockerfile"
    return min(candidates, key=lambda p: (len(p.parts), str(p)))
