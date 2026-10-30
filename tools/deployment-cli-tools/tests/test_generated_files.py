"""The YAML files harness-deployment writes: each one starts with a comment naming the command
that generated it, and keeps the key order its generator built - Codefresh runs a pipeline's
steps in file order, so a dump sorting keys alphabetically would reorder the pipeline."""
import io
import shutil

import pytest

from conftest import CLOUDHARNESS_ROOT, RESOURCES, chain

from ch_cli_tools import CHDeployConfig
from ch_cli_tools.model import CHValues
from ch_cli_tools.utils import GeneratedYAML, generation_argv, get_yaml_parser

COMMAND = "harness-deployment . -i samples -e dev"
HEADER = f"# Generated with: {COMMAND}\n"


@pytest.fixture
def generation_command():
    """Generation started from the command line, as harness-deployment does; reset afterwards."""
    token = generation_argv.set(["/opt/bin/harness-deployment", ".", "-i", "samples", "-e", "dev"])
    yield
    generation_argv.reset(token)


def _config(tmp_path, **kwargs):
    return CHDeployConfig(
        env="dev",
        includes=["samples"],
        excludes=["events"],
        registry="reg",
        tag="1",
        namespace="test",
        domain="my.local",
        output_path=str(tmp_path / "deployment"),
        **kwargs,
    )


def _assert_header_once(path):
    text = path.read_text()
    assert text.startswith(HEADER), path
    assert text.count("Generated with:") == 1, path


def _dumped(data, handler=None):
    stream = io.StringIO()
    (handler or get_yaml_parser()).dump(data, stream)
    return stream.getvalue()


def test_header_names_the_command_as_typed_in_a_shell():
    token = generation_argv.set(["/opt/bin/harness-deployment", ".", "--cache-url", "${{IMAGE_CACHE_URL}}"])
    try:
        assert _dumped({"a": 1}) == (
            "# Generated with: harness-deployment . --cache-url '${{IMAGE_CACHE_URL}}'\na: 1\n"
        )
    finally:
        generation_argv.reset(token)


def test_no_header_without_generation_command():
    assert _dumped({"a": 1}) == "a: 1\n"


def test_round_trip_handler_writes_the_header_too(generation_command):
    assert _dumped({"a": 1}, GeneratedYAML()) == f"{HEADER}a: 1\n"


def test_write_on_disk_keeps_key_order(tmp_path, generation_command):
    data = {
        "version": "1.0",
        "steps": {
            "main_clone": {"title": "Clone", "stage": "prepare"},
            "approval": {"type": "pending-approval", "stage": "qa"},
        },
    }
    CHValues.write_on_disk(tmp_path / "out.yaml", data)

    _assert_header_once(tmp_path / "out.yaml")
    loaded = get_yaml_parser().load((tmp_path / "out.yaml").read_text())
    assert loaded == data
    assert list(loaded) == ["version", "steps"]
    assert list(loaded["steps"]) == ["main_clone", "approval"]
    assert list(loaded["steps"]["main_clone"]) == ["title", "stage"]


def test_written_codefresh_pipeline_keeps_generated_order(tmp_path):
    project = chain(CLOUDHARNESS_ROOT, RESOURCES, config=_config(tmp_path))
    cf = project.codefresh.generate(output_path=tmp_path)

    loaded = get_yaml_parser().load((tmp_path / "codefresh-dev.yaml").read_text())
    assert list(loaded) == list(cf)
    assert list(loaded["steps"]) == list(cf["steps"])


def test_every_generated_yaml_file_starts_with_the_command(tmp_path, generation_command):
    # A chart version makes Chart.yaml generated rather than copied as-is
    project = chain(CLOUDHARNESS_ROOT, RESOURCES, config=_config(tmp_path, chart_version="1.2.3"))
    project.helm_chart.generate()
    project.build_final_helm_values()
    project.codefresh.generate(output_path=tmp_path / "deployment")
    project.skaffold.generate(output_path=tmp_path)

    for path in (
        "deployment/helm/values.yaml",
        "deployment/helm/Chart.yaml",
        "deployment/helm/values-overrides.yaml",
        "deployment/codefresh-dev.yaml",
        "skaffold.yaml",
    ):
        _assert_header_once(tmp_path / path)


@pytest.mark.skipif(shutil.which("helm") is None, reason="helm is not installed")
def test_every_generated_compose_file_starts_with_the_command(tmp_path, generation_command):
    config = _config(tmp_path)
    config.backend = "compose"
    project = chain(CLOUDHARNESS_ROOT, RESOURCES, config=config)
    project.docker_compose.generate()

    for path in (
        "deployment/compose/values.yaml",
        "deployment/compose/allvalues.yaml",
        "docker-compose.yaml",
    ):
        _assert_header_once(tmp_path / path)
