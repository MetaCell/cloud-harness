import json
import re
import shlex
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

# Instructions whose argument is either a JSON exec-form array (`CMD ["gunicorn", "app:app"]`)
# or a plain shell-form string (`CMD gunicorn app:app`).
_EXEC_FORM_INSTRUCTIONS = {"RUN", "CMD", "ENTRYPOINT", "SHELL", "HEALTHCHECK"}
_DEFAULT_SHELL = ["/bin/sh", "-c"]

_LINE_CONTINUATION = re.compile(r"\\\s*$")
_FROM_ALIAS = re.compile(r"\s+AS\s+", re.IGNORECASE)
_LEADING_FLAG = re.compile(r"^--[\w-]+(=\S*)?$")
_VAR_REFERENCE = re.compile(r"^\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?$")


@dataclass
class Instruction:
    """A line of a Dockerfile."""

    name: str
    arguments: tuple[str, ...] = ()
    raw: str = ""
    # The command ENTRYPOINT and CMD run, set once the shell in effect is known
    argv: list[str] | None = None

    @property
    def fields(self) -> tuple[str, ...]:
        return (self.name, *self.arguments)


@dataclass
class Stage:
    """The instructions that follow a FROM, up to the next one."""

    reference: str
    alias: str | None = None
    parent: "Stage | None" = None  # the earlier stage of the file this one is built FROM
    instructions: list[Instruction] = field(default_factory=list)
    shell: list[str] = field(default_factory=lambda: list(_DEFAULT_SHELL))

    @property
    def root_reference(self) -> str:
        """The image the chain of stages ultimately starts FROM."""
        return self.parent.root_reference if self.parent else self.reference

    @property
    def entrypoint(self) -> list[str] | None:
        """The ENTRYPOINT set by this stage or the stages it is built FROM."""
        own = self._last_argv("ENTRYPOINT")
        if own is not None or self.parent is None:
            return own
        return self.parent.entrypoint

    @property
    def cmd(self) -> list[str] | None:
        """The CMD set by this stage or the stages it is built FROM.

        Like Docker, an ENTRYPOINT clears the CMD of what the stage is built FROM,
        but not one set earlier in the same stage."""
        own = self._last_argv("CMD")
        if own is not None:
            return own
        if self._last_argv("ENTRYPOINT") is not None or self.parent is None:
            return None
        return self.parent.cmd

    @property
    def inherits_entrypoint(self) -> bool:
        """Whether no stage of the chain sets an ENTRYPOINT, leaving that of the base image."""
        return self._last_argv("ENTRYPOINT") is None and (
            self.parent is None or self.parent.inherits_entrypoint
        )

    @property
    def inherits_cmd(self) -> bool:
        """Whether no stage of the chain sets a CMD or an ENTRYPOINT, leaving the CMD of the base image."""
        return (
            self._last_argv("CMD") is None and
            self._last_argv("ENTRYPOINT") is None and
            (self.parent is None or self.parent.inherits_cmd)
        )

    def _last_argv(self, name: str) -> list[str] | None:
        argvs = [i.argv for i in self.instructions if i.name == name and i.argv is not None]
        return argvs[-1] if argvs else None


@dataclass
class ParsedDockerfile:
    """What the parser makes of a Dockerfile: its instructions, and the stages they build."""

    instructions: list[Instruction] = field(default_factory=list)
    stages: list[Stage] = field(default_factory=list)

    @cached_property
    def arg_names(self) -> set[str]:
        """The names declared by the ARG instructions."""
        return {i.arguments[0] for i in self.instructions if i.name == "ARG" and i.arguments}

    @property
    def final_stage(self) -> Stage | None:
        return self.stages[-1] if self.stages else None

    @property
    def arg_references(self) -> list[str]:
        """The ARG names used as the image of a FROM, in order."""
        return [s.reference for s in self.stages if s.reference in self.arg_names]

    @property
    def base_images(self) -> dict[str, str]:
        """The default of each ARG used as the image of a FROM, by the name of the ARG."""
        defaults = {
            i.arguments[0]: i.arguments[1]
            for i in self.instructions
            if i.name == "ARG" and len(i.arguments) > 1
        }
        return {ref: defaults[ref] for ref in self.arg_references if ref in defaults}

    def resolve_commands(self, inherited_shell: list[str] | None = None) -> None:
        """Set the argv of every ENTRYPOINT and CMD, shell form being run by the SHELL in effect.

        `inherited_shell` is the one the base image leaves in effect for the first stage."""
        for stage in self.stages:
            stage.shell = list(
                stage.parent.shell if stage.parent else inherited_shell or _DEFAULT_SHELL
            )
            for instruction in stage.instructions:
                if instruction.name == "SHELL" and instruction.raw:
                    stage.shell = DockerfileParser.parse_exec_form(instruction.raw) or stage.shell
                elif instruction.name in ("ENTRYPOINT", "CMD") and instruction.raw:
                    argv = DockerfileParser.parse_exec_form(instruction.raw)
                    instruction.argv = argv if argv is not None else [*stage.shell, instruction.raw]


class DockerfileParser:
    """Reads a Dockerfile in phases, each one enriching the model: lines, instructions, stages, commands."""

    def __init__(self, path: Path):
        self.path = path

    def parse(self) -> ParsedDockerfile:
        model = ParsedDockerfile(
            instructions=[
                instruction for line in self._read_lines() for instruction in self._tokenize(line)
            ]
        )
        self._split_stages(model)
        model.resolve_commands()
        return model

    def _read_lines(self) -> list[str]:
        """The instructions, one per line: comments dropped, continuations joined. Empty when the file is missing."""
        if not self.path.exists():
            return []

        lines: list[str] = []
        pending = ""
        for raw_line in self.path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if pending:
                line = f"{pending} {line}".strip()
                pending = ""
            if _LINE_CONTINUATION.search(line):
                pending = _LINE_CONTINUATION.sub("", line).strip()
                continue
            lines.append(line)
        return lines

    @classmethod
    def _tokenize(cls, line: str) -> list[Instruction]:
        """The instructions of a line: one, except for an ARG declaring several names."""
        name, _, rest = line.partition(" ")
        name = name.upper()
        rest = rest.strip()
        if not rest:
            return [Instruction(name)]
        if name == "FROM":
            return [Instruction(name, cls._parse_from(rest), rest)]
        if name == "ARG":
            return [Instruction(name, cls._parse_arg(token), token) for token in cls._split_args(rest)]
        if name in _EXEC_FORM_INSTRUCTIONS and rest.startswith("["):
            items = cls.parse_exec_form(rest)
            return [Instruction(name, tuple(items) if items is not None else (rest,), rest)]
        return [Instruction(name, tuple(cls._split_args(rest)), rest)]

    @classmethod
    def _split_stages(cls, model: ParsedDockerfile) -> None:
        """Group the instructions after each FROM into a stage, linked to the earlier stage it is built FROM."""
        by_alias: dict[str, Stage] = {}
        for instruction in model.instructions:
            if instruction.name == "FROM" and instruction.arguments:
                reference, *alias = instruction.arguments
                is_variable = cls.variable_reference(cls._strip_leading_flags(instruction.raw.split())[0]) is not None
                parent = None if is_variable else by_alias.get(reference.lower())
                stage = Stage(reference, alias[0] if alias else None, parent)
                model.stages.append(stage)
                if stage.alias:
                    by_alias[stage.alias.lower()] = stage
            elif model.stages:
                model.stages[-1].instructions.append(instruction)

    @staticmethod
    def variable_reference(token: str) -> str | None:
        """The name in a `$NAME` or `${NAME}` token, None for anything else."""
        match = _VAR_REFERENCE.match(token)
        return match.group(1) if match else None

    @staticmethod
    def parse_exec_form(argument: str) -> list[str] | None:
        """The items of an exec-form (JSON array) argument, None when it is not one."""
        try:
            parsed = json.loads(argument)
        except ValueError:
            return None
        return [str(item) for item in parsed] if isinstance(parsed, list) else None

    @staticmethod
    def _strip_leading_flags(tokens: list[str]) -> list[str]:
        while tokens and _LEADING_FLAG.match(tokens[0]):
            tokens.pop(0)
        return tokens

    @classmethod
    def _split_args(cls, rest: str) -> list[str]:
        try:
            tokens = shlex.split(rest)
        except ValueError:
            tokens = rest.split()
        return cls._strip_leading_flags(tokens)

    @classmethod
    def _parse_from(cls, rest: str) -> tuple[str, ...]:
        # FROM [--platform=<platform>] <image> [AS <name>]
        tokens = cls._strip_leading_flags(rest.split())
        parts = [part.strip() for part in _FROM_ALIAS.split(" ".join(tokens), maxsplit=1)]
        reference = cls.variable_reference(parts[0])
        if reference is not None:
            parts[0] = reference
        return tuple(parts)

    @staticmethod
    def _parse_arg(token: str) -> tuple[str, ...]:
        # <name>[=<default>]
        name, has_default, default = token.partition("=")
        return (name, default) if has_default else (name,)
