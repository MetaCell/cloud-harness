import json
import re
import shlex
from pathlib import Path
from typing import TYPE_CHECKING

from cloudharness.utils import dict_merge  # type: ignore

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
    parts = _FROM_ALIAS.split(" ".join(tokens), maxsplit=1)
    return tuple(part.strip() for part in parts)


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
