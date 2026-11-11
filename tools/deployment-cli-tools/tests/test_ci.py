"""ch_cli_tools.ci: the pieces shared by the Codefresh and GitHub Actions generators."""

from unittest.mock import patch

import pytest
from conftest import deployable_project

from ch_cli_tools.ci import (
    ImageReference,
    env_key,
    image_tag_env,
    is_forced,
    parse_force_build,
    tag_variable,
)


def test_env_key_and_tag_variable():
    assert env_key("my-app") == "MY_APP"
    assert tag_variable("cloudharness-base") == "CLOUDHARNESS_BASE_TAG"


@pytest.mark.parametrize(
    "image, expected",
    [
        ("reg.io/proj/myapp:abc", ("reg.io", "proj/myapp", "abc")),
        ("localhost:5000/proj/myapp:abc", ("localhost:5000", "proj/myapp", "abc")),
        ("proj/myapp:abc", ("docker.io", "proj/myapp", "abc")),
        ("proj/myapp", ("docker.io", "proj/myapp", "latest")),
        ("reg.io/proj/myapp", ("reg.io", "proj/myapp", "latest")),
    ],
)
def test_image_reference_parse(image, expected):
    reference = ImageReference.parse(image)
    assert (reference.registry, reference.repository, reference.tag) == expected


def test_parse_force_build():
    assert parse_force_build(None) == ()
    assert parse_force_build("") == ()
    assert parse_force_build("myapp, other,,") == ("myapp", "other")
    assert is_forced("myapp", ("myapp",))
    assert is_forced("anything", ("all",))
    assert not is_forced("myapp", ())


def test_image_tag_env_marks_existing_and_new_images(tmp_path):
    project = deployable_project(tmp_path, registry="reg.io/proj", tag="1")

    with patch(
        "ch_cli_tools.ci.check_image_exists_in_registry", side_effect=[True, False]
    ) as check:
        env = image_tag_env(project, image_cache_endpoint_url="https://cache")

    assert env["MYAPP_TAG"] == "1"
    assert env["MYAPP_TAG_EXISTS"] == "1"
    assert env["MYAPP_MYTASK_TAG"] == "1"
    assert env["MYAPP_MYTASK_TAG_NEW"] == "1"
    registry, repository, tag = check.call_args_list[0].args
    assert (registry, repository, tag) == ("reg.io", "proj/testproj/myapp", "1")
    assert check.call_args_list[0].kwargs == {"endpoint_url": "https://cache"}


def test_image_tag_env_forced_images_skip_the_registry_check(tmp_path):
    project = deployable_project(tmp_path, registry="reg.io/proj", tag="1")

    with patch(
        "ch_cli_tools.ci.check_image_exists_in_registry", return_value=True
    ) as check:
        env = image_tag_env(project, force_build=("myapp",))

    assert env["MYAPP_TAG_NEW"] == "1"
    assert "MYAPP_TAG_EXISTS" not in env
    assert env["MYAPP_MYTASK_TAG_EXISTS"] == "1"
    assert check.call_count == 1

    with patch("ch_cli_tools.ci.check_image_exists_in_registry") as check:
        env = image_tag_env(project, force_build=("all",))
    assert check.call_count == 0
    assert env["MYAPP_TAG_NEW"] == "1"
    assert env["MYAPP_MYTASK_TAG_NEW"] == "1"


def test_codefresh_write_env_file_accepts_force_build(tmp_path):
    project = deployable_project(tmp_path, registry="reg.io/proj", tag="1")
    env_file = tmp_path / "build.env"

    with patch("ch_cli_tools.ci.check_image_exists_in_registry", return_value=True):
        project.codefresh.write_env_file(env_file, force_build=("all",))

    lines = env_file.read_text().splitlines()
    assert "MYAPP_TAG=1" in lines
    assert "MYAPP_TAG_NEW=1" in lines
