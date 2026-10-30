"""ch_cli_tools.github_actions: the pure helpers the generator is built from."""

import pytest
from ruamel.yaml.scalarstring import LiteralScalarString

from ch_cli_tools.github_actions import (
    apply_needs_guards,
    as_literal_blocks,
    combine_conditions,
    expand_steps,
    github_repository,
    github_secret_name,
    job_id,
    needs_guard,
    referenced_names,
    rewrite_needs,
    runner_expression,
    step_by_id,
    substitute_vars,
)


def test_job_id_is_valid_for_github():
    assert job_id("build-my.app/x") == "build-my-app-x"
    assert job_id("9lives") == "_9lives"
    assert job_id("build-cloudharness-base") == "build-cloudharness-base"


def test_substitute_vars_is_word_bounded_and_recursive():
    node = {
        "run": "harness-deployment $PATHS -e $ENV $PARAMS; echo $ENV_FILE $PATH",
        "list": ["$ENV", {"nested": "x-$ENV-y"}],
        "number": 3,
    }
    result = substitute_vars(node, {"ENV": "dev", "PATHS": "cloud-harness .", "PARAMS": "-i a"})
    assert result["run"] == "harness-deployment cloud-harness . -e dev -i a; echo $ENV_FILE $PATH"
    assert result["list"] == ["dev", {"nested": "x-dev-y"}]
    assert result["number"] == 3
    # the input is left untouched
    assert node["list"][0] == "$ENV"


def test_expand_steps_replaces_fragments_and_rejects_unknown_ones():
    fragment = [{"run": "a"}, {"run": "b"}]
    steps = expand_steps([{"uses": "x"}, "$F", {"run": "c"}], {"$F": fragment})
    assert steps == [{"uses": "x"}, {"run": "a"}, {"run": "b"}, {"run": "c"}]
    assert steps[1] is not fragment[0], "fragments are copied, never shared"
    assert expand_steps(None, {}) == []
    with pytest.raises(ValueError, match="Unknown step fragment"):
        expand_steps(["$NOPE"], {"$F": fragment})


def test_step_by_id():
    steps = [{"run": "a"}, {"id": "build", "uses": "x"}]
    assert step_by_id(steps, "build") == {"id": "build", "uses": "x"}
    assert step_by_id(steps, "missing") is None


def test_combine_conditions():
    assert combine_conditions() == ""
    assert combine_conditions(None, "") == ""
    assert combine_conditions("${{ a }}") == "${{ a }}"
    assert combine_conditions("a") == "${{ a }}"
    assert combine_conditions("${{ a }}", None, "b || c") == "${{ (a) && (b || c) }}"


def test_needs_guard_requires_success_of_non_skippable_jobs():
    guard = needs_guard(["prepare", "build-a"], skippable={"build-a"})
    assert "!cancelled()" in guard
    assert "!contains(needs.*.result, 'failure')" in guard
    assert "needs.prepare.result == 'success'" in guard
    assert "needs.build-a.result" not in guard


def test_rewrite_needs_expands_placeholders():
    jobs = {
        "prepare": {},
        "build-a": {"needs": "prepare"},
        "build-b": {"needs": ["prepare", "build-a"]},
        "deploy": {"needs": ["prepare", "build", "tests-unit"]},
        "publish": {"needs": ["tests-e2e"]},
    }
    rewrite_needs(jobs, {"build": ["build-a", "build-b"], "tests-unit": [], "tests-e2e": []})
    assert jobs["build-a"]["needs"] == ["prepare"]
    assert jobs["deploy"]["needs"] == ["prepare", "build-a", "build-b"]
    assert "needs" not in jobs["publish"]


def test_rewrite_needs_rejects_unknown_jobs():
    with pytest.raises(ValueError, match="unknown job 'approval'"):
        rewrite_needs({"a": {}, "b": {"needs": ["a", "approval"]}}, {})


def test_apply_needs_guards():
    jobs = {
        "prepare": {},
        "build-a": {"needs": ["prepare"], "if": "${{ needs.prepare.outputs.A_TAG_EXISTS != '1' }}"},
        "deploy": {"needs": ["prepare", "build-a"]},
        "tests": {"needs": ["deploy"], "if": "${{ vars.SKIP_TESTS != 'true' }}"},
        "cleanup": {"needs": ["deploy"], "if": "${{ always() }}"},
        "publish": {
            "needs": ["deploy", "tests"],
            "if": "${{ !cancelled() && needs.deploy.result == 'success' }}",
        },
        "checked": {"needs": ["prepare", "deploy"], "if": "${{ needs.deploy.result == 'success' }}"},
        "explicit": {"needs": ["prepare", "build-a"], "if": "${{ success() }}"},
    }
    apply_needs_guards(jobs)

    assert "if" not in jobs["prepare"]
    # build-a is skippable (own if), prepare is not
    assert jobs["deploy"]["if"] == (
        "${{ !cancelled() && !contains(needs.*.result, 'failure') && "
        "!contains(needs.*.result, 'cancelled') && needs.prepare.result == 'success' }}"
    )
    # the template's own condition is kept and the guard is ANDed to it
    assert jobs["tests"]["if"].startswith("${{ (vars.SKIP_TESTS != 'true') && (!cancelled()")
    assert "needs.deploy.result == 'success'" in jobs["tests"]["if"]
    # build-a keeps its exists check plus the guard on prepare
    assert "A_TAG_EXISTS != '1'" in jobs["build-a"]["if"]
    assert "needs.prepare.result == 'success'" in jobs["build-a"]["if"]
    # a job deciding with always()/cancelled() is left alone
    assert jobs["cleanup"]["if"] == "${{ always() }}"
    assert jobs["publish"]["if"] == "${{ !cancelled() && needs.deploy.result == 'success' }}"
    # success() and needs.<job>.result checks do not tolerate skipped dependencies: still guarded
    assert "needs.prepare.result == 'success'" in jobs["checked"]["if"]
    assert "success()" in jobs["explicit"]["if"] and "!cancelled()" in jobs["explicit"]["if"]


def test_as_literal_blocks():
    result = as_literal_blocks({"a": "one\nline two   \n", "b": "single", "c": ("x", "y")})
    assert isinstance(result["a"], LiteralScalarString)
    assert result["a"] == "one\nline two\n"
    assert not isinstance(result["b"], LiteralScalarString)
    assert result["c"] == ["x", "y"]


def test_github_secret_name():
    assert github_secret_name("DB__PASSWORD") == "DB__PASSWORD"
    assert github_secret_name("google__bucket__credentials.json") == "GOOGLE__BUCKET__CREDENTIALS_JSON"
    # GitHub reserves the GITHUB_ prefix for its own secrets
    assert github_secret_name("GITHUB__CLIENTID") == "CH_GITHUB__CLIENTID"


def test_github_repository():
    assert github_repository("https://github.com/MetaCell/cloud-harness.git") == "MetaCell/cloud-harness"
    assert github_repository("https://github.com/MetaCell/cloud-harness") == "MetaCell/cloud-harness"
    assert github_repository("git@github.com:MetaCell/cloud-harness.git") == "MetaCell/cloud-harness"
    assert github_repository("https://gitlab.com/group/project.git") is None


def test_referenced_names():
    names = referenced_names(
        {
            "a": "${{ vars.REGISTRY }}/x:${{ secrets.TOKEN }}",
            "b": [{"c": "${{ secrets.GH_PAT || github.token }}"}],
            "d": "--set-file apps.myapp.harness.secrets.asecret=/tmp/0",
        }
    )
    assert names == {"vars": {"REGISTRY"}, "secrets": {"TOKEN", "GH_PAT"}}


def test_runner_expression_falls_back_through_the_variables():
    assert runner_expression(["A", "B"], "ubuntu-latest") == "${{ vars.A || vars.B || 'ubuntu-latest' }}"
    assert runner_expression([], "it's") == "${{ 'it''s' }}"
    assert runner_expression(["A"], ["self-hosted", "linux"]) == (
        """${{ vars.A || fromJSON('["self-hosted", "linux"]') }}"""
    )
