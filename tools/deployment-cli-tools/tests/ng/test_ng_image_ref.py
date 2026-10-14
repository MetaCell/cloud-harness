"""ch_cli_tools.ng.model harness.deployment.image_ref support. An application
declaring it runs an image of its own build (a base/common image from
harness.dependencies.build, or one of its own task images) instead of
building or declaring a prebuilt one. Ported from legacy's
test_deployment_image_ref_* in tests/test_helm.py.
"""

import pytest
from conftest import CLOUDHARNESS_ROOT, RESOURCES
from test_util_ng import write_tree

from ch_cli_tools.ng.api import create_helm_chart
from ch_cli_tools.ng.model import ValuesValidationError


def _image_ref_solution(tmp_path, image_ref="cloudharness-base", dockerfile=False, instance=False):
    """A solution with one application, refapp, running an image of the build through
    image_ref - mirrors legacy's own `image_ref_solution` fixture builder."""
    solution = tmp_path / "image_ref_solution"
    values = f"""harness:
  subdomain: refapp
  deployment:
    auto: true
    image_ref: {image_ref}
  dependencies:
    build:
      - cloudharness-base
"""
    deploy = {"values.yaml": values}
    if instance:
        deploy["instances"] = {"one": {"values.yaml": "harness:\n  subdomain: one\n"}}
    refapp = {"deploy": deploy}
    if dockerfile:
        refapp["Dockerfile"] = "FROM scratch\n"
    write_tree(solution, {"applications": {"refapp": refapp}})
    return solution


def _chart(tmp_path, solution, **kwargs):
    kwargs.setdefault("domain", "my.local")
    kwargs.setdefault("namespace", "test")
    kwargs.setdefault("local", False)
    kwargs.setdefault("tag", "1")
    kwargs.setdefault("registry", "reg")
    return create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES, solution], output_path=tmp_path, **kwargs
    ).to_dict()


def test_deployment_image_ref_runs_an_image_of_the_build(tmp_path):
    solution = _image_ref_solution(tmp_path)
    values = _chart(tmp_path, solution, include=["refapp"])

    base_image = values["task-images"]["cloudharness-base"]
    app = values["apps"]["refapp"]
    assert app["build"] is False
    assert app["image"] == base_image
    assert app["harness"]["deployment"]["image"] == base_image


def test_deployment_image_ref_without_include(tmp_path):
    solution = _image_ref_solution(tmp_path)
    values = _chart(tmp_path, solution)

    app = values["apps"]["refapp"]
    assert app["build"] is False
    assert app["harness"]["deployment"]["image"] == values["task-images"]["cloudharness-base"]


def test_deployment_image_ref_wins_over_a_dockerfile(tmp_path):
    solution = _image_ref_solution(tmp_path, dockerfile=True)
    values = _chart(tmp_path, solution, include=["refapp"])

    app = values["apps"]["refapp"]
    assert app["build"] is False
    assert app["harness"]["deployment"]["image"] == values["task-images"]["cloudharness-base"]


def test_deployment_image_ref_reaches_its_own_instance(tmp_path):
    solution = _image_ref_solution(tmp_path, instance=True)
    values = _chart(tmp_path, solution, include=["refapp"], env="test")

    base_image = values["task-images"]["cloudharness-base"]
    for app_key in ("refapp", "refapp-one"):
        app = values["apps"][app_key]
        assert app["image"] == base_image
        assert app["harness"]["deployment"]["image"] == base_image


def test_deployment_image_ref_to_an_image_not_built_fails(tmp_path):
    solution = _image_ref_solution(tmp_path, image_ref="not-built")
    with pytest.raises(ValuesValidationError, match="not-built"):
        _chart(tmp_path, solution, include=["refapp"])
