"""The content-hash tag must change when a pinned source image or a declared
build arg changes, even though the build context itself did not."""

from conftest import chain
from test_util import write_tree_from_yaml

from ch_cli_tools import CHDeployConfig

TREE = """
deployment-configuration:
  values-template.yaml: |
    name: testproj
    mainapp: myapp
    {source_images}
applications:
  myapp:
    Dockerfile: |
      ARG PYTHON=python:3.12
      FROM $PYTHON
    deploy:
      values.yaml: |
        harness:
          dockerfile:
            buildArgs:
              FLAVOUR: {flavour}
  other:
    Dockerfile: |
      ARG NODE=node:22
      FROM $NODE
"""


def _tag(tmp_path, source_images="", flavour="a"):
    root = tmp_path / f"{len(list(tmp_path.iterdir()))}"
    write_tree_from_yaml(root, TREE.format(source_images=source_images, flavour=flavour))
    project = chain(root, config=CHDeployConfig(registry="reg"))
    return project.qualify_image(project["myapp"]).rsplit(":", 1)[1]


def test_source_image_and_build_args_change_the_tag(tmp_path):
    baseline = _tag(tmp_path)
    assert _tag(tmp_path) == baseline, "the tag is stable"
    assert _tag(tmp_path, source_images='source_images: {PYTHON: "python:3.13"}') != baseline
    assert _tag(tmp_path, flavour="b") != baseline


def test_unrelated_source_image_keeps_the_tag(tmp_path):
    baseline = _tag(tmp_path)
    assert _tag(tmp_path, source_images='source_images: {NODE: "node:24"}') == baseline
