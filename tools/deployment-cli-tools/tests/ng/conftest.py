from pathlib import Path

from ch_cli_tools.ng import CHDeployConfig, CHProject

HERE = Path(__file__).parent
RESOURCES = HERE.parent / "resources"
CLOUDHARNESS_ROOT = HERE.parent.parent.parent.parent
WRONG_DEPENDENCIES = RESOURCES / "wrong-dependencies"


def chain(*roots, config=None):
    """Build a CHProject chain bottom-up from lowest to highest priority root -
    mirrors how ng.api.create_helm_chart builds one from root_paths. Returns
    the top of the chain.
    """
    project = None
    for root in roots:
        project = CHProject(root, base=project, config=config)
    return project


def minimal_project(tmp_path, **config_kwargs):
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    (app_dir / "tasks" / "mytask").mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "tasks" / "mytask" / "Dockerfile").write_text("FROM scratch\n")

    return chain(root, root, config=CHDeployConfig(**config_kwargs))
