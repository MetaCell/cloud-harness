"""ch_cli_tools.codefresh generator tests, scoped to internal mechanics
that don't go through the public create_helm_chart/create_codefresh_deployment_scripts
facade - that end-to-end behavior belongs in test_codefresh_compat.py instead.
See test_ng.py (this folder) for the structural/model tests these build on.
"""

from conftest import minimal_project


def test_sort_parallel_steps_alphabetically(tmp_path):
    """Sub-steps inside parallel steps must be sorted alphabetically by name."""
    codefresh = minimal_project(tmp_path).codefresh

    steps = {
        "build_application_images_0": {
            "type": "parallel",
            "stage": "build",
            "steps": {
                "z-image": {"type": "build"},
                "a-image": {"type": "build"},
                "m-image": {"type": "build"},
                "b-image": {"type": "build"},
            },
        },
        "build_application_images_1": {
            "type": "parallel",
            "stage": "build",
            "steps": {
                "zz": {"type": "build"},
                "aa": {"type": "build"},
            },
        },
        "not_parallel": {
            "stage": "prepare",
            "title": "Not parallel",
        },
    }

    result = codefresh._sort_parallel_steps(steps)

    # Parallel sub-steps are sorted alphabetically.
    assert list(result["build_application_images_0"]["steps"].keys()) == [
        "a-image",
        "b-image",
        "m-image",
        "z-image",
    ]
    assert list(result["build_application_images_1"]["steps"].keys()) == ["aa", "zz"]
    # Non-parallel steps are unaffected.
    assert "not_parallel" in result


def test_order_steps_by_stage(tmp_path):
    """Steps must be sorted according to the stages list; relative order within each stage is preserved."""
    codefresh = minimal_project(tmp_path).codefresh
    stages = ["prepare", "build", "unittest", "deploy", "qa"]

    steps = {
        "build_step_1": {"stage": "build", "title": "Build 1"},
        "main_clone": {"stage": "prepare", "title": "Clone"},
        "prepare_deployment": {"stage": "prepare", "title": "Prepare"},
        "tests_unit": {"stage": "unittest", "title": "Unit tests"},
        "build_step_2": {"stage": "build", "title": "Build 2"},
        "deployment": {"stage": "deploy", "title": "Deploy"},
        "tests_e2e": {"stage": "qa", "title": "E2E tests"},
        "no_stage_step": {"title": "No stage"},
    }

    result = codefresh._order_steps_by_stage(steps, stages)
    step_names = list(result.keys())

    assert step_names.index("main_clone") < step_names.index("build_step_1"), (
        "prepare must precede build"
    )
    assert step_names.index("prepare_deployment") < step_names.index("build_step_1"), (
        "prepare must precede build"
    )
    assert step_names.index("build_step_1") < step_names.index("tests_unit"), (
        "build must precede unittest"
    )
    assert step_names.index("build_step_2") < step_names.index("tests_unit"), (
        "build must precede unittest"
    )
    assert step_names.index("tests_unit") < step_names.index("deployment"), (
        "unittest must precede deploy"
    )
    assert step_names.index("deployment") < step_names.index("tests_e2e"), (
        "deploy must precede qa"
    )

    # Relative order within each stage is preserved (stable sort).
    assert step_names.index("main_clone") < step_names.index("prepare_deployment"), (
        "relative order within prepare preserved"
    )
    assert step_names.index("build_step_1") < step_names.index("build_step_2"), (
        "relative order within build preserved"
    )

    # Steps without a stage come last.
    assert step_names.index("no_stage_step") == len(step_names) - 1, (
        "steps without a stage go to the end"
    )
