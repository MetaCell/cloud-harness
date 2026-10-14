"""ch_cli_tools.ng.model application-instance support (CHAppInstance). Ported
from legacy's tests/test_helm.py (test_instance_*/test_collect_instances_*),
retargeted at ch_cli_tools.ng.api.create_helm_chart and the real
[CLOUDHARNESS_ROOT, RESOURCES] fixture chain, which already carries a real
instance each: samples/deploy/instances/instance1 (env=test only) and
myapp/deploy/instances/inst1 (unconditional, this repo's own test fixture).
"""

from types import SimpleNamespace

from conftest import CLOUDHARNESS_ROOT, RESOURCES, chain

from ch_cli_tools.ng.api import create_helm_chart
from ch_cli_tools.ng.model import CHAppInstance, ValuesValidationError, instance_app_key
from test_util_ng import write_tree_from_yaml


def _fake_instance(parent_name, instance_name):
    """A CHAppInstance bound only to a (parent_name, instance_name) pair, bypassing the
    filesystem-backed __init__, to exercise the pure values transform (_build_values) in
    isolation - the same way the other tests exercise it through a real chart."""
    instance = object.__new__(CHAppInstance)
    instance.parent_app = SimpleNamespace(name=parent_name)
    instance.instance_name = instance_name
    instance.name = instance_app_key(parent_name, instance_name)
    return instance


def _chart(tmp_path, **kwargs):
    kwargs.setdefault("domain", "my.local")
    kwargs.setdefault("namespace", "test")
    kwargs.setdefault("local", False)
    kwargs.setdefault("tag", "1")
    kwargs.setdefault("registry", "reg")
    return create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES], output_path=tmp_path, **kwargs
    ).to_dict()["apps"]


def test_instance_expands_into_an_application_inheriting_the_parent(tmp_path):
    apps = _chart(tmp_path, include=["samples"], env="test")
    instance, parent = apps["samples-instance1"], apps["samples"]

    # Its own host - the parent's subdomain/aliases are never inherited.
    assert instance["harness"]["subdomain"] == "samples1"
    assert not instance["harness"].get("aliases")
    assert parent["harness"]["subdomain"] == "www"

    # Its own resources.
    assert instance["harness"]["name"] == "samples-instance1"
    assert instance["harness"]["service"]["name"] == "samples-instance1"
    assert instance["harness"]["deployment"]["name"] == "samples-instance1"
    assert instance["harness"]["database"]["name"] == "samples-instance1-db"
    assert instance["harness"]["deployment"]["volume"]["name"] == "instance1-my-shared-volume"
    assert parent["harness"]["deployment"]["volume"]["name"] == "my-shared-volume"

    # The parent's image, built once.
    assert instance["build"] is False
    assert instance["image"] == parent["image"]
    assert instance["harness"]["deployment"]["image"] == parent["harness"]["deployment"]["image"]
    assert not instance["task-images"]


def test_instance_excluded_individually_leaves_its_parent_and_files_alone(tmp_path):
    apps = _chart(tmp_path, include=["samples"], exclude=["samples-instance1"], env="test")
    assert "samples-instance1" not in apps
    assert "samples" in apps
    assert not (tmp_path / "helm" / "resources" / "samples-instance1").exists()


def test_instance_included_alone_pulls_in_its_parent(tmp_path):
    apps = _chart(tmp_path, include=["samples-instance1"], env="test")
    assert "samples" in apps
    assert apps["samples-instance1"]["image"] == apps["samples"]["image"]


def test_instance_resources_are_overlaid_on_the_application(tmp_path):
    _chart(tmp_path, include=["samples"], env="test")
    instance_resources = tmp_path / "helm" / "resources" / "samples-instance1"
    assert (instance_resources / "example.yaml").exists()
    assert (instance_resources / "myConfig.json").exists(), (
        "a resource the instance does not override is inherited"
    )
    assert "an instance overridden" in (instance_resources / "example.yaml").read_text()


def test_instance_templates_are_overlaid_on_the_application(tmp_path):
    _chart(tmp_path, include=["myapp"], env="dev")
    helm_path = tmp_path / "helm"
    assert (helm_path / "templates" / "myapp-inst1" / "mytemplate.yaml").exists()
    assert (helm_path / "resources" / "myapp-inst1" / "instanceonly.txt").exists()
    assert (helm_path / "resources" / "myapp-inst1" / "aresource.txt").exists()


def test_instance_declared_for_an_environment_only(tmp_path):
    apps = _chart(tmp_path, include=["samples"])
    assert "samples-instance1" not in apps
    assert not (tmp_path / "helm" / "resources" / "samples-instance1").exists()

    apps = _chart(tmp_path, include=["samples"], env="test")
    assert "samples-instance1" in apps


def test_instance_values_precedence_env_over_plain_over_application(tmp_path):
    apps = _chart(tmp_path, include=["myapp"], env="dev")
    instance, parent = apps["myapp-inst1"], apps["myapp"]
    assert instance["a"] == "instance-dev-b"
    assert instance["harness"]["deployment"]["replicas"] == 4
    assert instance["dev"] is True
    assert parent["a"] == "b"


def test_instance_without_env_still_layers_over_the_application(tmp_path):
    apps = _chart(tmp_path, include=["myapp"])
    instance = apps["myapp-inst1"]
    assert instance["a"] == "instance-b"
    assert instance["harness"]["deployment"]["replicas"] == 3
    assert "dev" not in instance


def test_instance_inherits_the_application_merged_across_roots(tmp_path):
    overriding_root = tmp_path / "overriding_root"
    write_tree_from_yaml(
        overriding_root,
        """
        applications:
          myapp:
            deploy:
              values.yaml: |
                harness:
                  secured: true
                  deployment:
                    port: 9999
                    replicas: 1
        """,
    )

    config_kwargs = dict(
        include=["myapp"], domain="my.local", namespace="test", env="dev", local=False,
        tag="1", registry="reg",
    )
    values = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES, overriding_root],
        output_path=tmp_path,
        **config_kwargs,
    ).to_dict()
    apps = values["apps"]

    assert apps["myapp"]["harness"]["deployment"]["port"] == 9999
    instance = apps["myapp-inst1"]["harness"]
    assert instance["deployment"]["port"] == 9999
    assert instance["secured"] is True
    # and what the instance sets for itself still wins over the later root's values.
    assert instance["subdomain"] == "myinstance"
    assert instance["deployment"]["replicas"] == 4
    assert apps["myapp"]["harness"]["deployment"]["replicas"] == 1


def test_auto_tag_reaches_instance_images(tmp_path):
    apps = _chart(
        tmp_path, include=["samples", "myapp"], exclude=["events"], env="test", tag=None
    )
    for app_name, instance_key in (("samples", "samples-instance1"), ("myapp", "myapp-inst1")):
        parent_image = apps[app_name]["harness"]["deployment"]["image"]
        instance = apps[instance_key]
        assert ":" in parent_image, f"{app_name} should be tagged with its content hash"
        assert instance["image"] == parent_image
        assert instance["harness"]["deployment"]["image"] == parent_image


def test_instance_of_a_dependency_is_included_and_can_still_be_excluded(tmp_path):
    dependent_root = tmp_path / "dependent_root"
    write_tree_from_yaml(
        dependent_root,
        """
        applications:
          needsmyapp:
            deploy:
              values.yaml: |
                harness:
                  subdomain: needsmyapp
                  dependencies:
                    soft: [myapp]
                  deployment:
                    auto: true
                    image: reg/needsmyapp:1
        """,
    )
    config_kwargs = dict(
        include=["needsmyapp"], domain="my.local", namespace="test", env="dev", local=False,
        tag="1", registry="reg",
    )
    apps = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES, dependent_root],
        output_path=tmp_path,
        **config_kwargs,
    ).to_dict()["apps"]
    assert "myapp" in apps, "the dependency itself is included"
    assert "myapp-inst1" in apps, "and so are its instances"
    assert apps["myapp-inst1"]["image"] == apps["myapp"]["image"]

    apps = create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES, dependent_root],
        output_path=tmp_path,
        exclude=["myapp-inst1"],
        **config_kwargs,
    ).to_dict()["apps"]
    assert "myapp" in apps
    assert "myapp-inst1" not in apps


def test_instance_colliding_with_an_application_is_rejected(tmp_path):
    first, second = tmp_path / "first", tmp_path / "second"
    write_tree_from_yaml(
        first,
        """
        applications:
          myapp:
            deploy:
              instances:
                other:
                  values.yaml: ""
        """,
    )
    write_tree_from_yaml(
        second,
        """
        applications:
          myapp-other:
            deploy: {}
        """,
    )

    project = chain(first, second)
    try:
        project.all_instances()
        raised = False
    except ValuesValidationError:
        raised = True
    assert raised, "myapp-other collides between an instance of myapp and a real application"


def test_collect_instances_skips_hidden_directories_and_ones_without_values(tmp_path):
    write_tree_from_yaml(
        tmp_path,
        """
        applications:
          myapp:
            deploy:
              instances:
                .hidden:
                  values.yaml: ""
                novalues:
                  resources:
                    a.txt: content
                real:
                  values.yaml: |
                    harness:
                      subdomain: real
        """,
    )
    project = chain(tmp_path)
    assert project["myapp"].instance_names == {"real"}


def test_instance_values_replace_parent_lists_but_merge_mappings():
    parent_app = {
        "harness": {
            "uri_role_mapping": [{"uri": "/", "white-listed": True}],
            "env": [{"name": "WORKERS", "value": "3"}],
            "envmap": {"A": "parent", "B": "kept"},
        }
    }
    instance = _fake_instance("myapp", "i1")._build_values(
        parent_app,
        {
            "harness": {
                "subdomain": "myapp1",
                "uri_role_mapping": [{"uri": "/*", "roles": ["administrator"]}],
                "envmap": {"A": "instance"},
            }
        },
    )["harness"]

    assert instance["uri_role_mapping"] == [{"uri": "/*", "roles": ["administrator"]}]
    assert instance["env"] == [{"name": "WORKERS", "value": "3"}]
    assert instance["envmap"] == {"A": "instance", "B": "kept"}
    # the parent is never mutated by deriving an instance from it
    assert parent_app["harness"]["envmap"] == {"A": "parent", "B": "kept"}


def test_instance_subdomain_defaults_to_its_directory_name():
    parent = {"harness": {"subdomain": "www", "aliases": ["samples"]}}

    def subdomain_of(instance_values):
        return _fake_instance("samples", "instance1")._build_values(parent, instance_values)[
            "harness"
        ].get("subdomain", "<absent>")

    assert subdomain_of({}) == "instance1"
    assert subdomain_of({"harness": {"deployment": {"replicas": 2}}}) == "instance1"
    assert subdomain_of({"harness": {"subdomain": "samples1"}}) == "samples1"
    assert subdomain_of({"harness": {"subdomain": None}}) is None


def test_instance_gets_its_own_automatic_volume_named_after_it():
    def volume_of(parent_volume, instance_values=None):
        parent = {"harness": {"deployment": {"volume": parent_volume}}}
        return _fake_instance("samples", "instance1")._build_values(
            parent, instance_values or {}
        )["harness"]["deployment"]["volume"]

    assert volume_of({"name": "shared", "auto": True})["name"] == "instance1-shared"
    assert volume_of({"name": "shared"})["name"] == "instance1-shared"
    assert volume_of({"name": "existing-claim", "auto": False})["name"] == "existing-claim"
    assert (
        volume_of(
            {"name": "shared", "auto": True},
            {"harness": {"deployment": {"volume": {"name": "mine"}}}},
        )["name"]
        == "mine"
    )


def test_instance_sharing_the_parent_database_server_gets_its_own_initial_database():
    parent = {
        "harness": {
            "database": {
                "type": "postgres",
                "auto": True,
                "postgres": {"initialdb": "cloudharness"},
            }
        }
    }

    def database_of(instance_database):
        return _fake_instance("samples", "instance1")._build_values(
            parent, {"harness": {"database": instance_database}}
        )["harness"]["database"]

    own_server = database_of({})
    assert "name" not in own_server

    shared_server = database_of({"name": "samples-db"})
    assert shared_server["postgres"]["initialdb"] == "samples_instance1"
    assert parent["harness"]["database"]["postgres"]["initialdb"] == "cloudharness"

    assert database_of({"name": "other-db"})["postgres"]["initialdb"] == "cloudharness"


def test_instance_does_not_inherit_the_parent_connect_string():
    parent = {
        "harness": {"database": {"type": "postgres", "connect_string": "parent connection"}}
    }
    instance = _fake_instance("myapp", "i1")._build_values(
        parent, {"harness": {"subdomain": "myapp1"}}
    )
    assert instance["harness"]["database"]["connect_string"] == ""
    assert parent["harness"]["database"]["connect_string"] == "parent connection"


def test_dockerfile_dropped_inside_an_instance_is_never_the_parents_own(tmp_path):
    """A Dockerfile under deploy/instances/<name>/ must not be picked up as the
    application's own buildable Dockerfile - instances never build."""
    write_tree_from_yaml(
        tmp_path,
        """
        applications:
          myapp:
            deploy:
              instances:
                foo:
                  Dockerfile: |
                    FROM scratch
        """,
    )
    project = chain(tmp_path)
    assert not project["myapp"].dockerfile.exists()
