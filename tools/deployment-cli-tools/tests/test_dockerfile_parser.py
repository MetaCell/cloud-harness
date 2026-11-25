"""The Dockerfile parser and the model it builds, without any project around them."""

from pathlib import Path

from ch_cli_tools.dockerfile import DockerfileParser


def _parse(tmp_path: Path, content: str):
    path = tmp_path / "Dockerfile"
    path.write_text(content)
    return DockerfileParser(path).parse()


def _fields(model):
    return [i.fields for i in model.instructions]


def test_missing_file_gives_an_empty_model(tmp_path):
    model = DockerfileParser(tmp_path / "Dockerfile").parse()

    assert model.instructions == []
    assert model.stages == []
    assert model.final_stage is None


def test_comments_blank_lines_and_continuations_are_handled(tmp_path):
    model = _parse(tmp_path, "# c\n\nFROM scratch\nRUN a \\\n  b\n")

    assert _fields(model) == [("FROM", "scratch"), ("RUN", "a", "b")]


def test_instruction_names_are_upper_cased(tmp_path):
    assert _fields(_parse(tmp_path, "from scratch\n")) == [("FROM", "scratch")]


def test_from_has_its_image_and_its_alias_without_flags(tmp_path):
    model = _parse(tmp_path, "FROM --platform=linux/amd64 python:3.14 AS build\n")

    assert _fields(model) == [("FROM", "python:3.14", "build")]


def test_variable_references_are_normalized_in_from(tmp_path):
    assert _fields(_parse(tmp_path, "FROM ${BASE}\n")) == [("FROM", "BASE")]


def test_arg_has_its_name_and_its_default(tmp_path):
    model = _parse(tmp_path, "ARG A\nARG B=python:3.14\n")

    assert _fields(model) == [("ARG", "A"), ("ARG", "B", "python:3.14")]
    assert model.arg_names == {"A", "B"}


def test_exec_form_arguments_are_the_items_and_shell_form_ones_are_split(tmp_path):
    model = _parse(tmp_path, 'CMD ["a", "b"]\nRUN echo "x y"\n')

    assert _fields(model) == [("CMD", "a", "b"), ("RUN", "echo", "x y")]


def test_instructions_before_the_first_from_belong_to_no_stage(tmp_path):
    model = _parse(tmp_path, "ARG A\nFROM scratch\nRUN x\n")

    assert len(model.stages) == 1
    assert [i.name for i in model.stages[0].instructions] == ["RUN"]


def test_stages_are_split_at_each_from(tmp_path):
    model = _parse(tmp_path, "FROM a\nRUN 1\nFROM b\nRUN 2\nRUN 3\n")

    assert [s.reference for s in model.stages] == ["a", "b"]
    assert [len(s.instructions) for s in model.stages] == [1, 2]
    assert model.final_stage.reference == "b"


def test_stage_built_from_an_earlier_one_has_it_as_parent_whatever_the_case(tmp_path):
    model = _parse(tmp_path, "FROM a AS Base\nFROM base\n")

    assert model.stages[1].parent is model.stages[0]
    assert model.stages[1].root_reference == "a"


def test_stage_built_from_an_image_has_no_parent(tmp_path):
    model = _parse(tmp_path, "FROM a AS base\nFROM python:3.14\n")

    assert model.stages[1].parent is None
    assert model.stages[1].root_reference == "python:3.14"


def test_arg_references_are_the_args_used_as_from_images(tmp_path):
    model = _parse(tmp_path, "ARG BASE\nARG OTHER\nFROM $BASE\nFROM python\n")

    assert model.arg_references == ["BASE"]


def test_exec_form_argv_is_used_as_written_and_shell_form_goes_through_the_shell(tmp_path):
    stage = _parse(tmp_path, 'FROM a\nENTRYPOINT ["e"]\nCMD run it\n').final_stage

    assert stage.entrypoint == ["e"]
    assert stage.cmd == ["/bin/sh", "-c", "run it"]


def test_shell_in_effect_wraps_shell_form_commands_and_is_inherited_by_child_stages(tmp_path):
    model = _parse(
        tmp_path,
        'FROM a AS base\nSHELL ["/bin/bash", "-c"]\nFROM base\nCMD hi\n',
    )

    assert model.final_stage.cmd == ["/bin/bash", "-c", "hi"]


def test_shell_applies_only_to_the_commands_after_it(tmp_path):
    stage = _parse(tmp_path, 'FROM a\nCMD one\nSHELL ["/bin/bash", "-c"]\nENTRYPOINT two\n').final_stage

    assert stage.cmd == ["/bin/sh", "-c", "one"]
    assert stage.entrypoint == ["/bin/bash", "-c", "two"]


def test_last_entrypoint_and_cmd_win(tmp_path):
    stage = _parse(tmp_path, 'FROM a\nCMD ["1"]\nCMD ["2"]\nENTRYPOINT ["x"]\nENTRYPOINT ["y"]\n').final_stage

    assert stage.cmd == ["2"]
    assert stage.entrypoint == ["y"]


def test_empty_exec_form_entrypoint_is_set_not_missing(tmp_path):
    stage = _parse(tmp_path, "FROM a\nENTRYPOINT []\n").final_stage

    assert stage.entrypoint == []
    assert stage.inherits_entrypoint is False


def test_stage_inherits_what_it_does_not_set_from_its_parent(tmp_path):
    stage = _parse(tmp_path, 'FROM a AS base\nENTRYPOINT ["e"]\nCMD ["c"]\nFROM base\nRUN x\n').final_stage

    assert stage.entrypoint == ["e"]
    assert stage.cmd == ["c"]
    assert stage.inherits_entrypoint is False
    assert stage.inherits_cmd is False


def test_entrypoint_clears_the_cmd_of_the_parent_stage(tmp_path):
    stage = _parse(tmp_path, 'FROM a AS base\nCMD ["a"]\nFROM base\nENTRYPOINT ["b"]\n').final_stage

    assert stage.entrypoint == ["b"]
    assert stage.cmd is None
    assert stage.inherits_cmd is False


def test_entrypoint_after_a_cmd_of_the_same_stage_keeps_it(tmp_path):
    stage = _parse(tmp_path, 'FROM a\nCMD ["c"]\nENTRYPOINT ["e"]\n').final_stage

    assert stage.cmd == ["c"]


def test_stage_setting_nothing_inherits_the_command_of_its_base_image(tmp_path):
    stage = _parse(tmp_path, "FROM a\nRUN x\n").final_stage

    assert stage.inherits_entrypoint is True
    assert stage.inherits_cmd is True
    assert stage.entrypoint is None
    assert stage.cmd is None


def test_entrypoint_alone_stops_the_stage_inheriting_the_cmd_but_not_the_entrypoint_of_a_parent(tmp_path):
    stage = _parse(tmp_path, 'FROM a\nENTRYPOINT ["e"]\n').final_stage

    assert stage.inherits_entrypoint is False
    assert stage.inherits_cmd is False


def test_variable_reference_is_the_name_in_a_dollar_token():
    assert DockerfileParser.variable_reference("$NAME") == "NAME"
    assert DockerfileParser.variable_reference("${NAME}") == "NAME"
    assert DockerfileParser.variable_reference("python:3.12") is None


def test_parse_exec_form_is_none_when_the_argument_is_not_a_json_array():
    assert DockerfileParser.parse_exec_form('["a", 1]') == ["a", "1"]
    assert DockerfileParser.parse_exec_form("a b") is None
    assert DockerfileParser.parse_exec_form('{"a": 1}') is None


def test_comments_and_blank_lines_inside_a_continued_instruction_are_dropped(tmp_path):
    model = _parse(tmp_path, 'FROM a\nCMD ["a", \\\n# comment\n\n  "b"]\nRUN x\n')

    assert _fields(model) == [("FROM", "a"), ("CMD", "a", "b"), ("RUN", "x")]


def test_arg_declaring_several_names_is_one_instruction_per_name(tmp_path):
    model = _parse(tmp_path, 'ARG A=1 B C="x y"\nFROM $B\n')

    assert _fields(model)[:3] == [("ARG", "A", "1"), ("ARG", "B"), ("ARG", "C", "x y")]
    assert model.arg_names == {"A", "B", "C"}
    assert model.arg_references == ["B"]


def test_variable_named_like_an_earlier_stage_is_an_image_not_that_stage(tmp_path):
    model = _parse(tmp_path, "ARG BASE\nFROM x AS base\nFROM $BASE\n")

    assert model.final_stage.parent is None
    assert model.final_stage.root_reference == "BASE"


def test_resolving_commands_again_uses_the_shell_the_base_image_leaves_in_effect(tmp_path):
    model = _parse(tmp_path, "FROM a\nCMD hi\n")

    model.resolve_commands(["/bin/bash", "-c"])

    assert model.final_stage.cmd == ["/bin/bash", "-c", "hi"]


def test_base_images_are_the_defaults_of_the_args_used_as_from_images(tmp_path):
    model = _parse(
        tmp_path,
        'ARG BASE="python:3.14"\nARG OTHER=x\nARG NODEFAULT\nFROM --platform=$BUILDPLATFORM ${BASE}\nFROM $NODEFAULT\n',
    )

    assert model.base_images == {"BASE": "python:3.14"}
