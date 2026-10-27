from pathlib import Path

from ch_cli_tools import CHDeployConfig, CHProject
from test_util import write_tree_from_yaml

HERE = Path(__file__).parent
RESOURCES = HERE / "resources"
CLOUDHARNESS_ROOT = HERE.parent.parent.parent
WRONG_DEPENDENCIES = RESOURCES / "wrong-dependencies"


def chain(*roots, config=None):
    return CHProject.init(roots, config=config)


def minimal_project(tmp_path, **config_kwargs):
    write_tree_from_yaml(tmp_path, """
        deployment-configuration:
          values-template.yaml: |
            name: testproj
        applications:
          myapp:
            Dockerfile: |
              FROM scratch
            tasks:
              mytask:
                Dockerfile: |
                  FROM scratch
    """)
    return chain(tmp_path, tmp_path, config=CHDeployConfig(**config_kwargs))
