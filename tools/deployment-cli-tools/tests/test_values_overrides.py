"""CHHelmChart.generate() wiring of ch_cli_tools.utils.write_values_overrides - a
purely reference values-overrides.yaml, listing every image the chart pulls but
does not build. write_values_overrides/find_chart_images themselves are legacy
code, imported as-is (debug-only, no behavioral impact - not worth porting into
ng); legacy's own tests/test_helm.py already covers them directly. These tests
only check that ng's own build_final_helm_values() output feeds it correctly.
"""

from conftest import CLOUDHARNESS_ROOT, RESOURCES
from test_helm import render_helm_chart, find_manifest
from test_util import write_tree, write_tree_from_yaml

from ch_cli_tools.api import create_helm_chart
from ch_cli_tools.utils import get_yaml_parser


def _chart(tmp_path, **kwargs):
    kwargs.setdefault("domain", "my.local")
    kwargs.setdefault("namespace", "test")
    kwargs.setdefault("local", False)
    kwargs.setdefault("tag", "1")
    kwargs.setdefault("registry", "reg")
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES], output_path=tmp_path, **kwargs
    ).to_dict()
    with (tmp_path / "helm" / "values-overrides.yaml").open() as f:
        overrides = get_yaml_parser().load(f)
    return values, overrides


def test_values_overrides_helm_native_structure(tmp_path):
    values, overrides = _chart(tmp_path, include=["chartimgapp"], env="dev")

    assert overrides["source_images"] == values["source_images"]

    # Keyed by the vendored sub-chart's own Chart.yaml name, not the app/dir name; the
    # empty tag resolves to the sub-chart's appVersion.
    assert overrides["vendored-thing"]["image"] == {
        "registry": "docker.io",
        "repository": "someorg/somerepo",
        "tag": "2.0.0",
    }
    assert "chartimgapp" not in overrides

    assert overrides["apps"]["chartimgapp"]["worker"]["image"] == "docker.io/baz/qux:9"
    assert overrides["apps"]["chartimgapp"]["sidecar"]["image"] == {
        "name": "quay.io/foo/bar",
        "tag": "1.2.3",
    }
    # The CloudHarness-built image is not an overridable image source
    assert "image" not in overrides["apps"]["chartimgapp"]
    assert "image" not in overrides["apps"]["chartimgapp"].get("harness", {}).get(
        "deployment", {}
    )
    # Configured once at source_images.GATEKEEPER, not repeated per application
    assert overrides["source_images"]["GATEKEEPER"].startswith("quay.io/gogatekeeper")
    assert "proxy" not in overrides["apps"]["chartimgapp"].get("harness", {})


def test_values_overrides_edit_overrides_subchart_image(tmp_path):
    """Editing the generated file is enough to change the deployed image: Helm applies it
    after values.yaml - a dict-shape assertion alone can't tell a well-formed override file
    from one that Helm would actually ignore."""
    out_path = tmp_path / "test_values_overrides_edit"
    create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_path,
        include=["chartimgapp"],
        domain="my.local",
        namespace="test",
        env="dev",
        local=False,
        tag="1",
        registry="reg",
    )
    helm_path = out_path / "helm"
    overrides_path = helm_path / "values-overrides.yaml"

    yaml = get_yaml_parser()
    with overrides_path.open() as f:
        overrides = yaml.load(f)
    overrides["vendored-thing"]["image"] = {
        "registry": "myregistry.io",
        "repository": "other/repo",
        "tag": "7",
    }
    with overrides_path.open("w") as f:
        yaml.dump(overrides, f)

    manifests = render_helm_chart(helm_path, values_files=[overrides_path])
    assert (
        find_manifest(manifests, "ConfigMap", "vendored-thing-image")["data"]["image"] ==
        "myregistry.io/other/repo:7"
    )


def test_values_overrides_from_values_template(tmp_path):
    values, overrides = _chart(tmp_path, include=["chartimgapp"], env="chartimages")

    assert overrides["vendored-thing"]["image"] == {
        "registry": "docker.io",
        "repository": "someorg/somerepo",
        "tag": "9.9.9",
    }
    # Helm-native: the override in values.yaml alone already reaches the sub-chart
    assert values["vendored-thing"]["image"]["tag"] == "9.9.9"


def test_values_overrides_no_include_lists_vendored_charts(tmp_path):
    values, overrides = _chart(tmp_path, env="dev")

    assert overrides["vendored-thing"]["image"]["repository"] == "someorg/somerepo"
    assert overrides["argo-workflows"]["controller"]["image"]["repository"] == (
        "argoproj/workflow-controller"
    )
    assert overrides["argo-workflows"]["controller"]["image"]["tag"]
    assert overrides["kafka-ui"]["image"]["repository"] == "provectuslabs/kafka-ui"
    assert overrides["apps"]["events"]["kafka"]["image"].startswith(
        "docker.io/apache/kafka"
    )
    assert (
        overrides["apps"]["jupyterhub"]["hub"]["image"]["name"] ==
        "quay.io/jupyterhub/k8s-hub"
    )

    assert overrides["apps"]["accounts"]["harness"]["database"]["postgres"][
        "image"
    ] == ("postgres:17")
    assert (
        overrides["apps"]["neo4j"]["harness"]["database"]["neo4j"]["image"] == "neo4j:5"
    )
    assert overrides["source_images"]["GATEKEEPER"].startswith("quay.io/gogatekeeper")
    assert "gatekeeper" not in overrides.get("proxy", {})

    repeated = {
        name
        for name, app in overrides["apps"].items()
        if "gatekeeper" in app.get("harness", {}).get("proxy", {})
    }
    explicit = {
        name
        for name, app in values["apps"].items()
        if (
            ((app.get("harness") or {}).get("proxy") or {}).get("gatekeeper") or {}
        ).get("image")
    }
    assert repeated == explicit
    assert len(repeated) < len(overrides["apps"])

    assert overrides["backup"]["image"] == "prodrigestivill/postgres-backup-local"
    assert overrides["volumeMigration"]["image"].startswith("alpine/k8s")
    assert overrides["volumeMigration"]["wait"]["image"].startswith("busybox")

    for app_name, app in overrides["apps"].items():
        if values["apps"].get(app_name, {}).get("build") is False:
            continue
        assert "image" not in app, (
            f"built image of {app_name} leaked into the overrides"
        )
        assert "image" not in app.get("harness", {}).get("deployment", {})


def test_values_overrides_omits_shadowed_gatekeeper_path(tmp_path):
    """proxy.gatekeeper.image no longer overrides anything, so it must not be advertised."""
    solution = tmp_path / "solution"
    write_tree_from_yaml(
        solution,
        """
        deployment-configuration:
          values-template.yaml: |
            proxy:
              gatekeeper:
                image: "legacyroot/gk:1"
        """,
    )
    create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES, solution],
        output_path=tmp_path / "out",
        include=["samples"],
        domain="my.local",
        namespace="test",
        local=False,
        tag="1",
        secured=True,
    )
    with (tmp_path / "out" / "helm" / "values-overrides.yaml").open() as f:
        overrides = get_yaml_parser().load(f)

    assert "gatekeeper" not in overrides.get("proxy", {})
    assert overrides["source_images"]["GATEKEEPER"].startswith("quay.io/gogatekeeper")


def test_values_overrides_omits_database_image_shadowed_by_image_ref(tmp_path):
    def overrides_for(app_values, name):
        solution = tmp_path / name
        write_tree(
            solution,
            {"applications": {"myapp": {"deploy": {"values.yaml": app_values}}}},
        )
        out_path = tmp_path / f"out-{name}"
        create_helm_chart(
            [CLOUDHARNESS_ROOT, RESOURCES, solution],
            output_path=out_path,
            include=["myapp"],
            exclude=["events"],
            domain="my.local",
            namespace="test",
            local=False,
            tag="1",
        )
        with (out_path / "helm" / "values-overrides.yaml").open() as f:
            loaded = get_yaml_parser().load(f)
        return loaded.get("apps", {}).get("myapp", {}).get("harness") or {}

    database = (
        "harness:\n  database:\n    auto: true\n    type: postgres\n"
        '    postgres:\n      image: "postgres:17"\n'
    )

    assert (
        overrides_for(database, "plain")["database"]["postgres"]["image"] ==
        "postgres:17"
    )

    with_ref = database.replace(
        "    type: postgres\n", "    type: postgres\n    image_ref: myapp-mytask\n"
    )
    assert "database" not in overrides_for(with_ref, "withref")


def test_values_overrides_includes_prebuilt_deployment_image(tmp_path):
    values = create_helm_chart(
        [RESOURCES],
        output_path=tmp_path,
        include=["myapp"],
        exclude=["events"],
        domain="my.local",
        namespace="test",
        env="nobuild",
        local=False,
        tag="1",
    ).to_dict()

    assert values["apps"]["myapp"]["build"] is False
    with (tmp_path / "helm" / "values-overrides.yaml").open() as f:
        overrides = get_yaml_parser().load(f)
    assert (
        overrides["apps"]["myapp"]["harness"]["deployment"]["image"] == "custom-image"
    )


def test_values_overrides_omits_deployment_image_ref(tmp_path):
    solution = tmp_path / "image_ref_solution"
    write_tree_from_yaml(
        solution,
        """
        applications:
          refapp:
            deploy:
              values.yaml: |
                harness:
                  subdomain: refapp
                  deployment:
                    auto: true
                    image_ref: cloudharness-base
                  dependencies:
                    build:
                      - cloudharness-base
        """,
    )
    create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES, solution],
        output_path=tmp_path / "out",
        include=["refapp"],
        domain="my.local",
        namespace="test",
        local=False,
        tag="1",
    )
    with (tmp_path / "out" / "helm" / "values-overrides.yaml").open() as f:
        overrides = get_yaml_parser().load(f)
    app_overrides = (overrides.get("apps") or {}).get("refapp") or {}
    assert "image" not in app_overrides
    assert "image" not in ((app_overrides.get("harness") or {}).get("deployment") or {})
