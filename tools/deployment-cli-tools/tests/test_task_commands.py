"""Task commands derived from the Dockerfiles, from parsing to the Argo task that uses them.

Argo's emissary executor reads an image's ENTRYPOINT/CMD from the registry when a container has
no command, which needs registry credentials. The commands are derived from the task Dockerfiles
at generation time and carried in the generated values instead.
"""

from pathlib import Path

from conftest import chain
from test_util import write_tree

from ch_cli_tools import CHDeployConfig
from ch_cli_tools.model import CHDockerfile
from ch_cli_tools.utils import parse_dockerfile
from cloudharness_model import HarnessMainConfig


# Schema


def _main_config(**extra):
    return HarnessMainConfig.from_dict(
        {
            "local": False,
            "secured_gatekeepers": False,
            "domain": "my.local",
            "namespace": "test",
            "mainapp": "myapp",
            "apps": {},
            **extra,
        }
    )


def test_main_config_model_carries_task_commands():
    config = _main_config(**{"task-commands": {"t": ["a", "b"]}})

    assert config.task_commands == {"t": ["a", "b"]}
    assert config.to_dict()["task-commands"] == {"t": ["a", "b"]}


def test_main_config_model_does_not_require_task_commands():
    config = _main_config()

    assert config.task_commands is None


# Dockerfile reading


def _dockerfile(tmp_path: Path, content: str) -> CHDockerfile:
    """The Dockerfile of a task, mytask, of a project with one app, myapp."""
    write_tree(
        tmp_path,
        {
            "deployment-configuration": {"values-template.yaml": "name: testproj\n"},
            "applications": {
                "myapp": {
                    "Dockerfile": "FROM scratch\n",
                    "tasks": {"mytask": {"Dockerfile": content}},
                }
            },
        },
    )
    project = chain(tmp_path, tmp_path, config=CHDeployConfig())
    return project.all_buildable_tasks()["myapp-mytask"].dockerfile


def test_parse_dockerfile_still_joins_continuations_and_skips_comments(tmp_path):
    path = tmp_path / "Dockerfile"
    path.write_text("# comment\nFROM scratch\nRUN a \\\n  b\n")

    assert parse_dockerfile(path) == [("FROM", "scratch"), ("RUN", "a", "b")]


def test_exec_form_cmd_is_used_as_written(tmp_path):
    dockerfile = _dockerfile(tmp_path, 'FROM scratch\nCMD ["./run.sh", "--fast"]\n')

    assert dockerfile.cmd == ["./run.sh", "--fast"]
    assert dockerfile.command == ["./run.sh", "--fast"]


def test_shell_form_cmd_is_wrapped_with_the_raw_string(tmp_path):
    dockerfile = _dockerfile(tmp_path, 'FROM scratch\nCMD python a.py "$X" --opt  b\n')

    assert dockerfile.command == ["/bin/sh", "-c", 'python a.py "$X" --opt  b']


def test_shell_form_cmd_with_line_continuation_is_joined(tmp_path):
    dockerfile = _dockerfile(tmp_path, "FROM scratch\nCMD python a.py \\\n    --opt b\n")

    assert dockerfile.command == ["/bin/sh", "-c", "python a.py --opt b"]


def test_invalid_json_cmd_is_shell_form(tmp_path):
    dockerfile = _dockerfile(tmp_path, "FROM scratch\nCMD [not json\n")

    assert dockerfile.command == ["/bin/sh", "-c", "[not json"]


def test_entrypoint_is_followed_by_cmd(tmp_path):
    dockerfile = _dockerfile(tmp_path, 'FROM scratch\nENTRYPOINT ["python"]\nCMD ["a.py"]\n')

    assert dockerfile.entrypoint == ["python"]
    assert dockerfile.cmd == ["a.py"]
    assert dockerfile.command == ["python", "a.py"]


def test_last_cmd_and_last_entrypoint_win(tmp_path):
    dockerfile = _dockerfile(
        tmp_path, 'FROM scratch\nENTRYPOINT ["a"]\nENTRYPOINT ["b"]\nCMD ["c"]\nCMD ["d"]\n'
    )

    assert dockerfile.command == ["b", "d"]


def test_dockerfile_without_command_has_an_empty_command(tmp_path):
    dockerfile = _dockerfile(tmp_path, "FROM scratch\nRUN true\n")

    assert dockerfile.entrypoint is None
    assert dockerfile.cmd is None
    assert dockerfile.command == []


def test_missing_dockerfile_has_an_empty_command(tmp_path):
    dockerfile = _dockerfile(tmp_path, "FROM scratch\n")
    (dockerfile.path).unlink()

    assert dockerfile.command == []


def test_only_the_final_stage_counts(tmp_path):
    dockerfile = _dockerfile(
        tmp_path,
        'FROM a AS build\nCMD ["build-cmd"]\nFROM scratch\nCOPY --from=build /x /x\n',
    )

    assert dockerfile.command == []


def test_stage_built_from_an_earlier_stage_keeps_its_command(tmp_path):
    dockerfile = _dockerfile(
        tmp_path,
        'FROM a AS base\nENTRYPOINT ["e"]\nCMD ["c"]\nFROM base AS final\nRUN true\n',
    )

    assert dockerfile.command == ["e", "c"]


def test_stage_built_from_an_earlier_stage_can_override_its_cmd(tmp_path):
    dockerfile = _dockerfile(
        tmp_path,
        'FROM a AS base\nENTRYPOINT ["e"]\nCMD ["c"]\nFROM base\nCMD ["own"]\n',
    )

    assert dockerfile.command == ["e", "own"]
