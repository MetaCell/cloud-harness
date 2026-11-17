"""Task commands derived from the Dockerfiles, from parsing to the Argo task that uses them.

Argo's emissary executor reads an image's ENTRYPOINT/CMD from the registry when a container has
no command, which needs registry credentials. The commands are derived from the task Dockerfiles
at generation time and carried in the generated values instead.
"""

import logging
from pathlib import Path

import pytest
from conftest import CLOUDHARNESS_ROOT, chain
from test_util import write_tree

from ch_cli_tools import CHDeployConfig
from ch_cli_tools.api import create_helm_chart
from ch_cli_tools.model import CHDockerfile
from ch_cli_tools.utils import parse_dockerfile
from cloudharness.utils.config import CloudharnessConfig
from cloudharness.workflows import operations, tasks
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


def _project(tmp_path: Path, tasks: dict[str, str], app_dockerfile: str = "FROM scratch\n"):
    """A project with one app, myapp, whose tasks have the given Dockerfile contents."""
    write_tree(
        tmp_path,
        {
            "deployment-configuration": {"values-template.yaml": "name: testproj\n"},
            "applications": {
                "myapp": {
                    "Dockerfile": app_dockerfile,
                    "tasks": {name: {"Dockerfile": content} for name, content in tasks.items()},
                }
            },
        },
    )
    return chain(tmp_path, tmp_path, config=CHDeployConfig())


def _dockerfile(tmp_path: Path, content: str) -> CHDockerfile:
    """The Dockerfile of a task, mytask, of a project with one app, myapp."""
    return _project(tmp_path, {"mytask": content}).all_buildable_tasks()["myapp-mytask"].dockerfile


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


# Chain following


def _task_dockerfile(project, name: str) -> CHDockerfile:
    return project.all_buildable_tasks()[f"myapp-{name}"].dockerfile


def test_command_is_inherited_from_a_project_task(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": 'FROM python:3.14\nENTRYPOINT ["python"]\nCMD ["-V"]\n',
            "child": "ARG MYAPP_BASE\nFROM $MYAPP_BASE\nRUN true\n",
        },
    )

    child = _task_dockerfile(project, "child")

    assert child.entrypoint == ["python"]
    assert child.cmd == ["-V"]
    assert child.command == ["python", "-V"]


def test_command_is_inherited_through_several_project_images(tmp_path):
    project = _project(
        tmp_path,
        {
            "root": 'FROM python:3.14\nENTRYPOINT ["e"]\nCMD ["c"]\n',
            "middle": "ARG MYAPP_ROOT\nFROM $MYAPP_ROOT\nRUN true\n",
            "leaf": "ARG MYAPP_MIDDLE\nFROM ${MYAPP_MIDDLE}\nRUN true\n",
        },
    )

    assert _task_dockerfile(project, "leaf").command == ["e", "c"]


def test_command_is_inherited_from_an_app_image(tmp_path):
    project = _project(
        tmp_path,
        {"child": "ARG MYAPP\nFROM $MYAPP\nRUN true\n"},
        app_dockerfile='FROM python:3.14\nCMD ["serve"]\n',
    )

    assert _task_dockerfile(project, "child").command == ["serve"]


def test_own_cmd_replaces_the_inherited_cmd_and_keeps_the_entrypoint(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": 'FROM python:3.14\nENTRYPOINT ["e"]\nCMD ["c"]\n',
            "child": 'ARG MYAPP_BASE\nFROM $MYAPP_BASE\nCMD ["own"]\n',
        },
    )

    assert _task_dockerfile(project, "child").command == ["e", "own"]


def test_own_entrypoint_clears_the_inherited_cmd(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": 'FROM python:3.14\nENTRYPOINT ["e"]\nCMD ["c"]\n',
            "child": 'ARG MYAPP_BASE\nFROM $MYAPP_BASE\nENTRYPOINT ["own"]\n',
        },
    )

    assert _task_dockerfile(project, "child").command == ["own"]


def test_own_entrypoint_and_cmd_replace_both_inherited_ones(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": 'FROM python:3.14\nENTRYPOINT ["e"]\nCMD ["c"]\n',
            "child": 'ARG MYAPP_BASE\nFROM $MYAPP_BASE\nENTRYPOINT ["own"]\nCMD ["arg"]\n',
        },
    )

    assert _task_dockerfile(project, "child").command == ["own", "arg"]


def test_base_dockerfile_is_the_project_image_the_dockerfile_is_built_from(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": "FROM python:3.14\n",
            "child": "ARG MYAPP_BASE\nFROM $MYAPP_BASE\n",
        },
    )

    assert _task_dockerfile(project, "child").base_dockerfile.path == _task_dockerfile(project, "base").path


def test_base_dockerfile_is_found_through_a_stage_of_the_same_file(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": 'FROM python:3.14\nCMD ["c"]\n',
            "child": "ARG MYAPP_BASE\nFROM $MYAPP_BASE AS build\nFROM build\nRUN true\n",
        },
    )

    child = _task_dockerfile(project, "child")

    assert child.base_dockerfile.path == _task_dockerfile(project, "base").path
    assert child.command == ["c"]


def test_external_base_through_an_arg_has_no_base_dockerfile(tmp_path):
    dockerfile = _dockerfile(tmp_path, 'ARG PYTHON=python:3.14\nFROM $PYTHON\nCMD ["a"]\n')

    assert dockerfile.base_dockerfile is None
    assert dockerfile.command == ["a"]


def test_literal_from_is_external_even_when_named_like_a_project_image(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": 'FROM python:3.14\nCMD ["c"]\n',
            "child": "FROM myapp-base\nRUN true\n",
        },
    )

    child = _task_dockerfile(project, "child")

    assert child.base_dockerfile is None
    assert child.command == []


def test_base_dependencies_still_lists_the_project_images_referenced_via_arg(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": "FROM python:3.14\n",
            "child": "ARG MYAPP_BASE\nARG OTHER\nFROM $MYAPP_BASE\nFROM $OTHER\n",
        },
    )

    dependencies = _task_dockerfile(project, "child").base_dependencies

    assert dependencies[0].path == _task_dockerfile(project, "base").path
    assert dependencies[1] == "other"


def test_project_finds_an_app_or_a_task_by_name(tmp_path):
    project = _project(tmp_path, {"mytask": "FROM scratch\n"})

    assert project.find_entity("myapp").name == "myapp"
    assert project.find_entity("myapp-mytask").name == "myapp-mytask"
    assert project.find_entity("unknown") is None


# Generation


def test_task_commands_are_derived_for_every_task_image(tmp_path):
    project = _project(
        tmp_path,
        {
            "exec": 'FROM python:3.14\nCMD ["./run.sh"]\n',
            "shell": "FROM python:3.14\nCMD python job.py\n",
            "base": 'FROM python:3.14\nENTRYPOINT ["python"]\n',
            "child": 'ARG MYAPP_BASE\nFROM $MYAPP_BASE\nCMD ["job.py"]\n',
        },
    )

    assert project.all_task_commands() == {
        "myapp-exec": ["./run.sh"],
        "myapp-shell": ["/bin/sh", "-c", "python job.py"],
        "myapp-base": ["python"],
        "myapp-child": ["python", "job.py"],
    }


def test_task_commands_are_named_like_the_task_images(tmp_path):
    project = _project(tmp_path, {"job": 'FROM python:3.14\nCMD ["x"]\n'})

    assert set(project.all_task_commands()) <= set(project.all_task_images())


def test_task_without_any_command_is_left_out_with_a_warning(tmp_path, caplog):
    project = _project(tmp_path, {"silent": "FROM scratch\nRUN true\n"})

    with caplog.at_level(logging.WARNING):
        commands = project.all_task_commands()

    assert "myapp-silent" not in commands
    assert "Task myapp-silent sets no ENTRYPOINT or CMD" in caplog.text


def test_base_image_without_a_command_is_left_out_silently(tmp_path, caplog):
    write_tree(
        tmp_path,
        {
            "infrastructure": {"base-images": {"mybase": {"Dockerfile": "FROM python:3.14\n"}}},
        },
    )
    project = _project(
        tmp_path,
        {"job": 'FROM python:3.14\nCMD ["x"]\n'},
        app_dockerfile="ARG MYBASE\nFROM $MYBASE\n",
    )

    with caplog.at_level(logging.WARNING):
        commands = project.all_task_commands()

    assert "mybase" in project.all_task_images()
    assert "mybase" not in commands
    assert "mybase sets no" not in caplog.text


def test_external_bases_the_commands_rely_on_are_reported_in_one_warning(tmp_path, caplog):
    project = _project(
        tmp_path,
        {
            "a": 'FROM python:3.14\nCMD ["a"]\n',
            "b": 'ARG NODE=node:22\nFROM $NODE\nCMD ["b"]\n',
            "own": 'FROM alpine:3\nENTRYPOINT ["own"]\n',
        },
    )

    with caplog.at_level(logging.WARNING):
        project.all_task_commands()

    warnings = [r.message for r in caplog.records if "external base images" in r.message]
    assert len(warnings) == 1
    assert "node:22" in warnings[0] and "python:3.14" in warnings[0]
    assert "alpine:3" not in warnings[0]


def test_external_base_is_where_the_chain_of_froms_ends(tmp_path):
    project = _project(
        tmp_path,
        {
            "base": "FROM python:3.14\n",
            "child": "ARG MYAPP_BASE\nFROM $MYAPP_BASE\n",
            "arg": "ARG PYTHON=python:3.12\nFROM $PYTHON\n",
        },
    )

    assert _task_dockerfile(project, "child").external_base == "python:3.14"
    assert _task_dockerfile(project, "arg").external_base == "python:3.12"


def test_generated_values_carry_task_commands_beside_task_images(tmp_path):
    solution = tmp_path / "solution"
    write_tree(
        solution,
        {
            "deployment-configuration": {"values-template.yaml": "name: testproj\n"},
            "applications": {
                "myapp": {
                    "Dockerfile": "FROM scratch\n",
                    "deploy": {"values.yaml": "harness:\n  subdomain: myapp\n"},
                    "tasks": {
                        "job": {"Dockerfile": "FROM python:3.14\nCMD python job.py\n"},
                        "plain": {"Dockerfile": 'FROM scratch\nCMD ["x"]\n'},
                    },
                }
            },
        },
    )

    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, solution],
        output_path=tmp_path / "out",
        domain="my.local",
        namespace="test",
        local=False,
        tag="1",
        registry="reg",
        include=["myapp"],
    ).to_dict()

    assert values["task-commands"]["myapp-job"] == ["/bin/sh", "-c", "python job.py"]
    assert values["task-commands"]["myapp-plain"] == ["x"]
    assert set(values["task-commands"]) <= set(values["task-images"])


# Runtime


@pytest.fixture
def ch_config(monkeypatch):
    """Installs a Cloud Harness configuration for the test, with a registry and the given values."""

    def install(**values):
        allvalues = {
            "registry": {"name": "reg"},
            "apps": {},
            "task-images": {"job": "reg/job:1", "workflows-notify-queue": "reg/notify:1"},
            **values,
        }
        monkeypatch.setattr(CloudharnessConfig, "allvalues", allvalues)
        return allvalues

    return install


def test_get_task_command_returns_the_derived_command(ch_config):
    ch_config(**{"task-commands": {"job": ["./run.sh"]}})

    assert CloudharnessConfig.get_task_command("job") == ["./run.sh"]


@pytest.mark.parametrize("values", [{"task-commands": {"other": ["x"]}}, {"task-commands": None}, {}])
def test_get_task_command_is_none_when_there_is_none_for_the_image(ch_config, values):
    ch_config(**values)

    assert CloudharnessConfig.get_task_command("job") is None


def test_get_task_command_is_none_without_any_configuration(monkeypatch):
    monkeypatch.setattr(CloudharnessConfig, "allvalues", {})
    monkeypatch.setattr("cloudharness.utils.config.ALLVALUES_PATH", "/nonexistent/allvalues.yaml")

    assert CloudharnessConfig.get_task_command("job") is None


def test_custom_task_uses_the_derived_command_by_default(ch_config):
    ch_config(**{"task-commands": {"job": ["./run.sh"]}})

    spec = tasks.CustomTask("t", "job").spec()

    assert spec["container"]["command"] == ["./run.sh"]


def test_custom_task_explicit_command_wins(ch_config):
    ch_config(**{"task-commands": {"job": ["./run.sh"]}})

    spec = tasks.CustomTask("t", "job", command=["explicit"]).spec()

    assert spec["container"]["command"] == ["explicit"]


def test_custom_task_without_a_derived_command_sets_none(ch_config):
    ch_config()

    spec = tasks.CustomTask("t", "job").spec()

    assert "command" not in spec["container"]


def _exit_template(workflow):
    return next(t for t in workflow["spec"]["templates"] if t["name"] == "exit-handler")


def test_exit_handler_uses_the_derived_command_by_default(ch_config):
    ch_config(**{"task-commands": {"workflows-notify-queue": ["notify"]}})

    operation = operations.PipelineOperation(
        "wf", [tasks.CustomTask("t", "job")], on_exit_notify={"queue": "q"}
    )

    assert _exit_template(operation.to_workflow())["container"]["command"] == ["notify"]


def test_exit_handler_explicit_command_wins(ch_config):
    ch_config(**{"task-commands": {"workflows-notify-queue": ["notify"]}})

    operation = operations.PipelineOperation(
        "wf", [tasks.CustomTask("t", "job")], on_exit_notify={"queue": "q", "command": ["explicit"]}
    )

    assert _exit_template(operation.to_workflow())["container"]["command"] == ["explicit"]


# End to end


def _generate_values(tmp_path: Path, tasks: dict[str, str]) -> dict:
    """The values harness-deployment generates for a project with one app, myapp, and the given tasks."""
    solution = tmp_path / "solution"
    write_tree(
        solution,
        {
            "deployment-configuration": {"values-template.yaml": "name: testproj\n"},
            "applications": {
                "myapp": {
                    "Dockerfile": "FROM scratch\n",
                    "deploy": {"values.yaml": "harness:\n  subdomain: myapp\n"},
                    "tasks": {name: {"Dockerfile": content} for name, content in tasks.items()},
                }
            },
        },
    )
    return create_helm_chart(
        [CLOUDHARNESS_ROOT, solution],
        output_path=tmp_path / "out",
        domain="my.local",
        namespace="test",
        local=False,
        tag="1",
        registry="reg",
        include=["myapp"],
    ).to_dict()


def test_generated_command_reaches_the_argo_workflow(tmp_path, monkeypatch):
    values = _generate_values(
        tmp_path,
        {
            "base": 'FROM python:3.14\nENTRYPOINT ["python"]\n',
            "child": 'ARG MYAPP_BASE\nFROM $MYAPP_BASE\nCMD ["job.py"]\n',
        },
    )
    monkeypatch.setattr(CloudharnessConfig, "allvalues", values)

    workflow = operations.PipelineOperation("wf", [tasks.CustomTask("run", "myapp-child")]).to_workflow()

    template = next(t for t in workflow["spec"]["templates"] if t["name"] == "run")
    assert template["container"]["command"] == ["python", "job.py"]
    assert template["container"]["image"] == values["task-images"]["myapp-child"]
