"""ch_cli_tools.ng.skaffold generator tests. Ports of tests/test_skaffold.py,
scoped to the slice of behavior the ng model currently supports. See test_ng.py
(this folder) for the structural/model tests these build on.
"""

from ch_cli_tools.ng import CHDeployConfig, CHProject, skaffold
from ch_cli_tools.ng.utils import dockerfile_variable_reference, parse_dockerfile
from conftest import CLOUDHARNESS_ROOT, RESOURCES, minimal_project


def test_build_dependency_on_app_produces_requires_entry():
    # Ports test_app_depends_on_app: dependantapp declares
    # dependencies.build: [myapp, myapp-mytask] - a real app and a task owned by
    # that app. Both resolve, each to its own requires entry.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["dependantapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    dependantapp_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/dependantapp"
    )
    assert dependantapp_artifact["requires"] == [
        {"image": "testprojectname/myapp", "alias": "MYAPP"},
        {"image": "testprojectname/myapp-mytask", "alias": "MYAPP_MYTASK"},
    ]

    # myapp-mytask must have its own build artifact even though myapp itself is
    # only a build dependency here, not deployed.
    assert any(a["image"] == "testprojectname/myapp-mytask" for a in artifacts)


def test_build_only_dependency_is_not_deployed():
    # Ports the other half of test_app_depends_on_app: myapp is a build
    # dependency of dependantapp (dependencies.build), not a soft/hard one, so it
    # must not end up deployed - no artifactOverrides entry, even though its
    # image still gets built (see test_build_dependency_on_app_produces_requires_
    # entry for the build side of the same fixture).
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["dependantapp"]),
    )
    generated = project.skaffold.generate(write_on_disk=False)
    overrides = generated["deploy"]["helm"]["releases"][0]["artifactOverrides"]["apps"]

    assert "dependantapp" in overrides
    assert "myapp" not in overrides


def test_build_dependency_on_base_image_gets_its_own_artifact():
    # Slice of test_create_skaffold_configuration's cloudharness_flask assertions:
    # a build dependency resolving to infrastructure/common-images/ gets its own
    # artifact, with a context under that directory, and the requiring app's
    # artifact references it via requires.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["taskdep"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    taskdep_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/taskdep"
    )
    assert taskdep_artifact["requires"] == [
        {"image": "testprojectname/cloudharness-flask", "alias": "CLOUDHARNESS_FLASK"},
        {"image": "testprojectname/myapp-mytask", "alias": "MYAPP_MYTASK"},
    ]

    flask_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/cloudharness-flask"
    )
    context = (RESOURCES / flask_artifact["context"]).resolve()
    expected = (
        CLOUDHARNESS_ROOT / "infrastructure" / "common-images" / "cloudharness-flask"
    )
    assert context == expected.resolve()


def test_build_dependency_on_task_owned_by_an_undeployed_app_resolves():
    # Ports test_skaffold_builds_cross_app_task_image: taskdep declares
    # dependencies.build: [cloudharness-flask, myapp-mytask]. myapp-mytask is a
    # task owned by myapp, an app that isn't otherwise deployed here (not an
    # entrypoint, not a soft/hard dep of anything included) - it must still
    # resolve and get its own build artifact. CHAppDefault.build_dependencies()
    # falls back to CHProject.all_buildable_tasks(), which is scoped to every
    # scanned app, not just involved_apps, precisely to cover this case.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["taskdep"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    assert any(a["image"] == "testprojectname/myapp-mytask" for a in artifacts)


def test_excluded_task_drops_out_unless_still_a_build_dependency():
    # Ports test_exclude_single_task. excludes applies to a task in its own
    # right - myapp's own myapp-mytask disappears when excluded and nothing else
    # needs it - but a build dependency is never optional (see
    # test_build_dependency_on_task_owned_by_an_undeployed_app_resolves), so the
    # same exclude has no effect when dependantapp still requires it to build.
    own_project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"], excludes=["myapp-mytask"]),
    )
    own_artifacts = own_project.skaffold.generate(write_on_disk=False)["build"][
        "artifacts"
    ]
    assert not any(a["image"].endswith("myapp-mytask") for a in own_artifacts)

    required_project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["dependantapp"], excludes=["myapp-mytask"]),
    )
    required_artifacts = required_project.skaffold.generate(write_on_disk=False)[
        "build"
    ]["artifacts"]
    assert any(a["image"] == "testprojectname/myapp-mytask" for a in required_artifacts)


def test_namespace_sets_helm_release_name_and_namespace(tmp_path):
    project = minimal_project(tmp_path, namespace="my-ns")
    release = project.skaffold.generate(write_on_disk=False)["deploy"]["helm"][
        "releases"
    ][0]

    assert release["name"] == "my-ns"
    assert release["namespace"] == "my-ns"


def test_no_namespace_leaves_helm_release_name_unset(tmp_path):
    project = minimal_project(tmp_path)
    release = project.skaffold.generate(write_on_disk=False)["deploy"]["helm"][
        "releases"
    ][0]

    assert "name" not in release
    assert "namespace" not in release


def test_tag_policy_is_sha256_by_default(tmp_path):
    project = minimal_project(tmp_path)
    build = project.skaffold.generate(write_on_disk=False)["build"]
    assert build["tagPolicy"] == {"sha256": {}}


def test_tag_policy_is_env_template_when_external_tag_and_not_local(tmp_path):
    # An external tag (e.g. from CI) means skaffold should trust the tag it's
    # handed rather than compute its own content hash.
    project = minimal_project(tmp_path, tag="v1", local=False)
    build = project.skaffold.generate(write_on_disk=False)["build"]
    assert build["tagPolicy"] == {"envTemplate": {"template": '"{{.TAG}}"'}}


def test_tag_policy_is_sha256_when_tag_set_but_local(tmp_path):
    # A local dev build still wants content-hash tagging even if an external tag
    # was also passed - `local` wins over `tag`.
    project = minimal_project(tmp_path, tag="v1", local=True)
    build = project.skaffold.generate(write_on_disk=False)["build"]
    assert build["tagPolicy"] == {"sha256": {}}


def test_compose_backend_builds_docker_compose_deploy_block(tmp_path):
    # Also covers the tagPolicy branch: compose always wants envTemplate, even
    # without an explicit tag - see test_tag_policy_is_env_template_when_
    # external_tag_and_not_local for the non-compose case.
    project = minimal_project(tmp_path, backend="compose")
    generated = project.skaffold.generate(write_on_disk=False)

    assert generated["build"]["tagPolicy"] == {
        "envTemplate": {"template": '"{{.TAG}}"'}
    }
    assert generated["deploy"] == {
        "docker": {
            "useCompose": True,
            "images": ["testproj/myapp", "testproj/myapp-mytask"],
        }
    }


def test_env_dockerfile_used_when_it_exists():
    # Ports test_env_dockerfile: myapp has a dev.Dockerfile, so it's preferred
    # over the plain Dockerfile once env="dev" is active.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"], env="dev"),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    myapp_artifact = next(a for a in artifacts if a["image"] == "testprojectname/myapp")
    assert myapp_artifact["docker"]["dockerfile"].endswith("dev.Dockerfile")


def test_env_dockerfile_falls_back_to_plain_dockerfile():
    # Ports test_env_dockerfile's samples half and test_env_dockerfile_fallback:
    # samples has no dev.Dockerfile, so it keeps using the plain Dockerfile even
    # with env="dev" active; myapp-mytask (a task, not the app itself) has no
    # dev.Dockerfile of its own either.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"], env="dev"),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    mytask_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/myapp-mytask"
    )
    dockerfile = mytask_artifact["docker"]["dockerfile"]
    assert dockerfile.endswith("Dockerfile")
    assert not dockerfile.endswith("dev.Dockerfile")


def test_no_env_never_uses_env_dockerfile():
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    myapp_artifact = next(a for a in artifacts if a["image"] == "testprojectname/myapp")
    assert myapp_artifact["docker"]["dockerfile"] == "Dockerfile"


def _multi_env_project(tmp_path, env):
    # Deliberately deterministic, not RESOURCES: a, b, c let us tell apart
    # "later env wins" from "earlier env's untouched keys survive" from
    # "base's own untouched keys survive both env layers".
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    app_dir.mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "dev.Dockerfile").write_text("FROM dev-image\n")
    (app_dir / "test.Dockerfile").write_text("FROM test-image\n")
    (app_dir / "deploy").mkdir()
    (app_dir / "deploy" / "values.yaml").write_text("a: base\nb: base\nc: base\n")
    (app_dir / "deploy" / "values-dev.yaml").write_text("a: dev\nb: dev\n")
    (app_dir / "deploy" / "values-test.yaml").write_text("a: test\n")

    return CHProject(root, cloudharness_path=root, config=CHDeployConfig(env=env))


def test_multi_env_layers_in_order_later_env_wins(tmp_path):
    project = _multi_env_project(tmp_path, env=["dev", "test"])
    values = project["myapp"].all_values()

    assert values["a"] == "test"  # both dev and test touch it - test is later
    assert values["b"] == "dev"  # only dev touches it - survives test's layer
    assert values["c"] == "base"  # neither env touches it - stays at base


def test_multi_env_order_matters(tmp_path):
    # Same two envs, reversed order - "dev" now wins on "a" since it's last.
    project = _multi_env_project(tmp_path, env=["test", "dev"])
    values = project["myapp"].all_values()

    assert values["a"] == "dev"
    assert values["b"] == "dev"


def test_multi_env_dockerfile_selection_tries_each_env_in_order(tmp_path):
    project = _multi_env_project(tmp_path / "both", env=["dev", "test"])
    assert project["myapp"].dockerfile.path.name == "dev.Dockerfile"

    project_test_only = _multi_env_project(tmp_path / "test-only", env=["test"])
    assert project_test_only["myapp"].dockerfile.path.name == "test.Dockerfile"


def test_multi_env_output_path_is_dash_joined(tmp_path):
    # Ports the real -e dev-test convention: the *output* artifact name joins
    # the envs with a dash, unlike the per-env *input* files it reads from.
    project = _multi_env_project(tmp_path / "both", env=["dev", "test"])
    assert project.codefresh.path.name == "codefresh-dev-test.yaml"

    project_none = _multi_env_project(tmp_path / "none", env=None)
    assert project_none.codefresh.path.name == "codefresh.yaml"


def test_own_build_args_apply_only_to_the_apps_own_artifact():
    # Ports part of test_skaffold_imgarg: samples declares harness.dockerfile.
    # buildArgs.TEST_ARGUMENT, which must reach samples' own artifact but not its
    # tasks'.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["samples"], excludes=["events"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    app_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/sampleapp"
    )
    assert app_artifact["docker"]["buildArgs"]["TEST_ARGUMENT"] == "example value"

    task_artifacts = [
        a for a in artifacts if a["image"].startswith("testprojectname/sampleapp-")
    ]
    assert task_artifacts
    assert all(
        "TEST_ARGUMENT" not in a["docker"].get("buildArgs", {}) for a in task_artifacts
    )


def test_source_images_apply_to_every_artifact_project_wide():
    # Ports test_skaffold_imgarg/test_skaffold_imgarg_retrieval's source_images
    # aggregation. cloudharness_path=CLOUDHARNESS_ROOT (not RESOURCES) so myapp's
    # explicit dependencies.build: [cloudharness-flask] actually resolves - myapp's
    # Dockerfile doesn't reference mybase/mybase2 itself, but still gets them as
    # buildArgs, since source_images is a project-wide aggregation applied to
    # every artifact, not just the app that owns the ARG.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["newapp1", "myapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    myapp_artifact = next(a for a in artifacts if a["image"] == "testprojectname/myapp")
    assert myapp_artifact["docker"]["buildArgs"]["mybase"] == "foo:bar"
    assert myapp_artifact["docker"]["buildArgs"]["mybase2"] == "spam:egg"


def test_ssh_default_set_on_every_artifact(tmp_path):
    project = minimal_project(tmp_path)
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]

    assert artifacts
    assert all(a["docker"]["ssh"] == "default" for a in artifacts)


def _entrypoint_app_project(
    tmp_path, dockerfile_text="", requirements_text=None, main_dirs=()
):
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    app_dir.mkdir(parents=True)
    (app_dir / "Dockerfile").write_text(dockerfile_text or "FROM scratch\n")
    if requirements_text is not None:
        (app_dir / "requirements.txt").write_text(requirements_text)
    for main_dir in main_dirs:
        (app_dir / main_dir).mkdir(parents=True)
        (app_dir / main_dir / "__main__.py").write_text("")

    return CHProject(root, cloudharness_path=root, config=CHDeployConfig())


def test_entrypoint_prefers_shortest_path_over_decoys(tmp_path):
    # Ports test_create_skaffold_configuration_with_conflicting_dependencies:
    # a venv/vendored __main__.py (e.g. matplotlib's) must lose to the app's
    # own, shallower one.
    project = _entrypoint_app_project(
        tmp_path,
        dockerfile_text="ARG CLOUDHARNESS_FLASK\nFROM $CLOUDHARNESS_FLASK\n",
        main_dirs=["myapp_code", "myapp_code/venv/matplotlib"],
    )
    entrypoint = project["myapp"].app_entrypoint
    assert entrypoint.name == "myapp_code"


def test_entrypoint_falls_back_to_requirements_txt(tmp_path):
    # Ports test_create_skaffold_configuration_with_conflicting_dependencies_
    # requirements_file: a Dockerfile with no gunicorn/Flask/Django mention
    # still triggers the override via a sibling requirements.txt.
    project = _entrypoint_app_project(
        tmp_path,
        dockerfile_text="FROM python:3.12\n",
        requirements_text="gunicorn==21.2.0\n",
        main_dirs=["myapp_code"],
    )
    entrypoint = project["myapp"].app_entrypoint
    assert entrypoint.name == "myapp_code"


def test_entrypoint_none_without_a_match(tmp_path):
    project = _entrypoint_app_project(
        tmp_path,
        dockerfile_text="FROM python:3.12\n",
        main_dirs=["myapp_code"],
    )
    assert project["myapp"].app_entrypoint is None


def test_entrypoint_none_without_main(tmp_path):
    project = _entrypoint_app_project(
        tmp_path, dockerfile_text="ARG CLOUDHARNESS_FLASK\nFROM $CLOUDHARNESS_FLASK\n"
    )
    assert project["myapp"].app_entrypoint is None


def test_unit_test_commands_requires_the_enabled_flag(tmp_path):
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    (app_dir / "deploy").mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "deploy" / "values.yaml").write_text(
        "harness:\n  test:\n    unit:\n      enabled: false\n"
        "      commands: ['pytest tests/']\n"
    )
    project = CHProject(root, cloudharness_path=root, config=CHDeployConfig())
    assert project["myapp"].unit_test_commands == []


def test_app_entrypoint_override_and_unit_tests_reach_skaffold_output():
    # Ports test_create_skaffold_configuration's command/args and test[]
    # assertions, against the real samples app (applications/samples/backend/
    # samples/__main__.py, a real Flask-based entrypoint in this monorepo).
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["samples"], excludes=["events"]),
    )
    generated = project.skaffold.generate(write_on_disk=False)
    release = generated["deploy"]["helm"]["releases"][0]

    override = release["overrides"]["apps"]["samples"]["harness"]["deployment"]
    assert override["command"] == ["python"]
    assert override["args"] == ["/usr/src/app/samples/__main__.py"]

    test_entries = generated["test"]
    assert len(test_entries) == 1
    assert test_entries[0]["image"] == "testprojectname/sampleapp"
    assert "samples/test" in test_entries[0]["custom"][0]["command"]


def test_parse_dockerfile_missing_file_returns_empty_list(tmp_path):
    assert parse_dockerfile(tmp_path / "Dockerfile") == []


def test_parse_dockerfile_skips_comments_and_blank_lines(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("# a comment\n\nFROM scratch\n\n# another\n")
    assert parse_dockerfile(dockerfile) == [("FROM", "scratch")]


def test_parse_dockerfile_from_with_and_without_alias(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text(
        "FROM python:3.12 AS builder\nFROM --platform=linux/amd64 scratch\n"
    )
    assert parse_dockerfile(dockerfile) == [
        ("FROM", "python:3.12", "builder"),
        ("FROM", "scratch"),
    ]


def test_parse_dockerfile_from_normalizes_variable_references(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM $BASE AS one\nFROM ${BASE}\nFROM python:3.12\n")
    assert parse_dockerfile(dockerfile) == [
        ("FROM", "BASE", "one"),
        ("FROM", "BASE"),
        ("FROM", "python:3.12"),  # a literal image is left untouched
    ]


def test_parse_dockerfile_arg_with_and_without_default(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("ARG NO_DEFAULT\nARG WITH_DEFAULT=value\n")
    assert parse_dockerfile(dockerfile) == [
        ("ARG", "NO_DEFAULT"),
        ("ARG", "WITH_DEFAULT", "value"),
    ]


def test_parse_dockerfile_exec_form_vs_shell_form(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text('CMD ["gunicorn", "app:app"]\nRUN pip install gunicorn\n')
    assert parse_dockerfile(dockerfile) == [
        ("CMD", "gunicorn", "app:app"),
        ("RUN", "pip", "install", "gunicorn"),
    ]


def test_parse_dockerfile_line_continuation(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("RUN apt-get update && \\\n    apt-get install -y curl\n")
    assert parse_dockerfile(dockerfile) == [
        ("RUN", "apt-get", "update", "&&", "apt-get", "install", "-y", "curl")
    ]


def test_parse_dockerfile_copy_strips_leading_flags_only(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("COPY --from=builder /app/dist /app/dist\n")
    assert parse_dockerfile(dockerfile) == [("COPY", "/app/dist", "/app/dist")]


def test_parse_dockerfile_command_is_case_insensitive():
    # Real fixture Dockerfile, already all-uppercase - locks in that we don't
    # accidentally rely on case for the common path while testing case
    # insensitivity synthetically below.
    instructions = parse_dockerfile(RESOURCES / "applications" / "myapp" / "Dockerfile")
    assert instructions == [
        ("ARG", "CLOUDHARNESS_FLASK"),
        # $NAME is normalized to the bare NAME at parse time - see
        # test_parse_dockerfile_from_normalizes_variable_references below.
        ("FROM", "CLOUDHARNESS_FLASK"),
    ]


def test_parse_dockerfile_lowercase_instructions_are_normalized(tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("from scratch\n")
    assert parse_dockerfile(dockerfile) == [("FROM", "scratch")]


def test_dockerfile_variable_reference_dollar_and_braces_are_equivalent():
    assert dockerfile_variable_reference("$NAME") == "NAME"
    assert dockerfile_variable_reference("${NAME}") == "NAME"


def test_dockerfile_variable_reference_none_for_a_literal():
    assert dockerfile_variable_reference("python:3.12") is None
    assert dockerfile_variable_reference("scratch") is None


def test_git_dependencies_exposes_raw_config():
    # myapp/deploy/values.yaml declares two: one without a path, one with.
    project = CHProject(
        RESOURCES, cloudharness_path=CLOUDHARNESS_ROOT, config=CHDeployConfig()
    )
    deps = project["myapp"].git_dependencies
    assert deps == [
        {"url": "https://github.com/a/b.git", "branch_tag": "master"},
        {
            "url": "https://github.com/c/d.git",
            "branch_tag": "v1.0.0",
            "path": "myrepo",
        },
    ]


def test_git_dependencies_empty_for_an_app_without_any():
    project = CHProject(
        RESOURCES, cloudharness_path=CLOUDHARNESS_ROOT, config=CHDeployConfig()
    )
    assert project["events"].git_dependencies == []


def test_git_clone_hooks_reach_the_skaffold_artifact():
    # Ports the intent of the legacy git_clone_hook(): one build.artifacts[].
    # hooks.before entry per git dependency, each shelling out to clone.sh
    # with (branch_tag, url, clone_path) - clone_path under context/
    # dependencies/[path/]repo_name.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    myapp_artifact = next(a for a in artifacts if a["image"] == "testprojectname/myapp")

    hooks = myapp_artifact["hooks"]["before"]
    assert len(hooks) == 2

    no_path_command = hooks[0]["command"]
    assert no_path_command[0:2] == ["sh", str(skaffold._CLONE_SH)]
    assert no_path_command[2:] == [
        "master",
        "https://github.com/a/b.git",
        "applications/myapp/dependencies/b",
    ]

    with_path_command = hooks[1]["command"]
    assert with_path_command[2:] == [
        "v1.0.0",
        "https://github.com/c/d.git",
        "applications/myapp/dependencies/myrepo/d",
    ]


def test_git_clone_hooks_absent_when_no_git_dependencies():
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["accounts"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    accounts_artifact = next(
        a for a in artifacts if a["image"] == "testprojectname/accounts"
    )
    assert "hooks" not in accounts_artifact


def test_skaffold_template_flags_pass_through_to_output():
    # deployment-configuration/skaffold-template.yaml's own deploy.helm.flags
    # (install --timeout=10m, upgrade --install) - static passthrough via
    # skaffold_template.all_values(), not something generate() computes, but
    # never actually asserted anywhere.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["accounts"]),
    )
    generated = project.skaffold.generate(write_on_disk=False)
    flags = generated["deploy"]["helm"]["flags"]
    assert flags["install"] == ["--timeout=10m"]
    assert flags["upgrade"] == ["--install"]


def test_multiple_apps_unit_tests_all_aggregate_into_test_array(tmp_path):
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    for name, command in [
        ("appone", "pytest appone/test"),
        ("apptwo", "pytest apptwo/test"),
    ]:
        app_dir = root / "applications" / name
        (app_dir / "deploy").mkdir(parents=True)
        (app_dir / "Dockerfile").write_text("FROM scratch\n")
        (app_dir / "deploy" / "values.yaml").write_text(
            "harness:\n"
            "  test:\n"
            "    unit:\n"
            "      enabled: true\n"
            f"      commands: ['{command}']\n"
        )

    project = CHProject(root, cloudharness_path=root, config=CHDeployConfig())
    test_entries = project.skaffold.generate(write_on_disk=False)["test"]

    assert len(test_entries) == 2
    images = {entry["image"] for entry in test_entries}
    assert images == {"testproj/appone", "testproj/apptwo"}


def test_build_dependency_artifact_respects_env_dockerfile(tmp_path):
    # _collect_build_dependency_artifact goes through the same env-aware
    # .dockerfile property as an app's own artifact - never exercised with an
    # env active until now.
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )

    helper_dir = root / "applications" / "helper"
    helper_dir.mkdir(parents=True)
    (helper_dir / "Dockerfile").write_text("FROM scratch\n")
    (helper_dir / "dev.Dockerfile").write_text("FROM dev-base\n")

    consumer_dir = root / "applications" / "consumer"
    (consumer_dir / "deploy").mkdir(parents=True)
    (consumer_dir / "Dockerfile").write_text("FROM scratch\n")
    (consumer_dir / "deploy" / "values.yaml").write_text(
        "harness:\n  dependencies:\n    build: ['helper']\n"
    )

    project = CHProject(
        root,
        cloudharness_path=root,
        config=CHDeployConfig(includes=["consumer"], env="dev"),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    helper_artifact = next(a for a in artifacts if a["image"] == "testproj/helper")
    assert helper_artifact["docker"]["dockerfile"] == "dev.Dockerfile"


def test_base_dependencies_resolves_real_chain():
    # cloudharness-flask's own Dockerfile: ARG CLOUDHARNESS_BASE (no default) /
    # FROM $CLOUDHARNESS_BASE - a real, currently-unresolved-by-base_images
    # chain (base_images only picks up ARGs *with* a default).
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["taskdep"]),
    )
    flask = project.base_images["cloudharness-flask"]
    [flask_dep] = flask.dockerfile.base_dependencies
    assert flask_dep.path == project.base_images["cloudharness-base"].dockerfile.path

    myapp = project["myapp"]
    [myapp_dep] = myapp.dockerfile.base_dependencies
    assert myapp_dep.path == flask.dockerfile.path


def test_base_dependencies_unresolved_names_stay_plain_strings():
    # newapp1/Dockerfile: ARG mybase=foo:bar / FROM ${mybase} - a real ARG,
    # used in a real FROM, but "mybase" isn't any scanned app/base-image/task
    # name in this project, so it can't resolve to a CHDockerfile.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["newapp1"]),
    )
    deps = project["newapp1"].dockerfile.base_dependencies
    assert deps == ["mybase", "mybase2"]


def test_base_dependencies_survives_a_leading_comment(tmp_path):
    # The old guess_build_dependencies_from_dockerfile() would find nothing
    # here at all: a leading comment breaks its "leading run of ARG lines"
    # scan before it ever reaches the ARG below.
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    base_dir = root / "applications" / "base"
    base_dir.mkdir(parents=True)
    (base_dir / "Dockerfile").write_text("FROM scratch\n")

    app_dir = root / "applications" / "consumer"
    app_dir.mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("# license header\nARG BASE\nFROM $BASE\n")

    project = CHProject(root, cloudharness_path=root, config=CHDeployConfig())
    [dep] = project["consumer"].dockerfile.base_dependencies
    assert dep.path == project["base"].dockerfile.path


def test_base_dependencies_finds_an_arg_after_a_defaulted_one(tmp_path):
    # ARG A=default / ARG B (no default), both used in FROM - the old
    # heuristic would stop at A (has "=") and never see B at all.
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    b_dir = root / "applications" / "b"
    b_dir.mkdir(parents=True)
    (b_dir / "Dockerfile").write_text("FROM scratch\n")

    app_dir = root / "applications" / "consumer"
    app_dir.mkdir(parents=True)
    (app_dir / "Dockerfile").write_text(
        "ARG A=default\nARG B\nFROM $A AS stage1\nFROM $B\n"
    )

    project = CHProject(root, cloudharness_path=root, config=CHDeployConfig())
    deps = project["consumer"].dockerfile.base_dependencies
    assert deps[0] == "a"  # unresolved - no scanned app/base-image named "a"
    assert deps[1].path == project["b"].dockerfile.path


def test_base_dependencies_empty_without_a_dockerfile(tmp_path):
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    (root / "applications" / "noimg" / "deploy").mkdir(parents=True)
    project = CHProject(root, cloudharness_path=root, config=CHDeployConfig())
    assert project["noimg"].dockerfile.base_dependencies == []


def test_base_image_requires_chain_transitively_discovered():
    # cloudharness-flask FROM cloudharness-base: cloudharness-base is never
    # named by any app directly, only reachable by following
    # cloudharness-flask's own base_dependencies - it must still get its own
    # artifact, and cloudharness-flask's artifact must show requires: [it].
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["taskdep"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    by_image = {a["image"]: a for a in artifacts}

    flask = by_image["testprojectname/cloudharness-flask"]
    assert flask["requires"] == [
        {"image": "testprojectname/cloudharness-base", "alias": "CLOUDHARNESS_BASE"}
    ]

    base = by_image["testprojectname/cloudharness-base"]
    assert "requires" not in base  # leaf - nothing to build before it


def test_explicit_and_guessed_build_dependency_dedupe():
    # myapp declares dependencies.build: [cloudharness-flask] explicitly, and
    # its own Dockerfile also does FROM $CLOUDHARNESS_FLASK - same dependency
    # from both sources, must appear exactly once in requires.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["myapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    myapp = next(a for a in artifacts if a["image"] == "testprojectname/myapp")
    assert myapp["requires"] == [
        {"image": "testprojectname/cloudharness-flask", "alias": "CLOUDHARNESS_FLASK"}
    ]


def test_app_both_deployed_and_a_build_dependency_gets_one_artifact():
    # myapp is directly included AND a build dependency of dependantapp (and
    # myapp-mytask is a task of an included app AND a build dependency of
    # dependantapp too) - neither should be emitted twice.
    project = CHProject(
        RESOURCES,
        cloudharness_path=CLOUDHARNESS_ROOT,
        config=CHDeployConfig(includes=["dependantapp", "myapp"]),
    )
    artifacts = project.skaffold.generate(write_on_disk=False)["build"]["artifacts"]
    images = [a["image"] for a in artifacts]
    assert len(images) == len(set(images))
    assert images.count("testprojectname/myapp") == 1
    assert images.count("testprojectname/myapp-mytask") == 1


def test_app_with_explicit_deployment_image_is_never_built(tmp_path):
    # Mirrors the legacy `build = not bool(deployment_image)` rule: an app that
    # declares harness.deployment.image has a prebuilt/external image, so skaffold
    # must skip its artifact, entrypoint override and unit tests entirely - but
    # its task still builds normally.
    root = tmp_path
    (root / "deployment-configuration").mkdir(parents=True)
    (root / "deployment-configuration" / "values-template.yaml").write_text(
        "name: testproj\n"
    )
    app_dir = root / "applications" / "myapp"
    (app_dir / "tasks" / "mytask").mkdir(parents=True)
    (app_dir / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "tasks" / "mytask" / "Dockerfile").write_text("FROM scratch\n")
    (app_dir / "deploy").mkdir(parents=True)
    (app_dir / "deploy" / "values.yaml").write_text(
        "harness:\n"
        "  deployment:\n"
        "    image: someregistry/prebuilt:latest\n"
        "  test:\n"
        "    unit:\n"
        "      enabled: true\n"
        "      commands: ['pytest']\n"
    )

    project = CHProject(root, cloudharness_path=root, config=CHDeployConfig())
    result = project.skaffold.generate(write_on_disk=False)
    artifacts = result["build"]["artifacts"]
    images = [a["image"] for a in artifacts]

    assert "testproj/myapp" not in images
    assert "testproj/myapp-mytask" in images
    assert result.get("test", []) == []

    overrides = result["deploy"]["helm"]["releases"][0]["artifactOverrides"]["apps"]
    assert "myapp" not in overrides
