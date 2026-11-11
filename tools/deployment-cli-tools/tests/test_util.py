from pathlib import Path

import pytest

from ch_cli_tools.utils import discover_root_paths, get_yaml_parser


def write_tree_from_yaml(
    root: Path, text: str | None = None, *, path: Path | None = None
) -> Path:
    if text is not None and path is not None:
        raise ValueError("Pass only one of text or path, not both")
    if text is None and path is None:
        raise ValueError("Pass one of text or path")
    spec = get_yaml_parser().load(path if path is not None else text) or {}
    return write_tree(root, spec)


def write_tree(root: Path, spec: dict) -> Path:
    for name, content in spec.items():
        path = root / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            write_tree(path, content)
        elif isinstance(content, str):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        else:
            raise TypeError(
                f"{name!r}: expected a dict (folder) or str (file content), got {type(content).__name__}"
            )
    return root


def test_write_tree_creates_nested_files_and_dirs(tmp_path):
    write_tree(
        tmp_path,
        {
            "deployment-configuration": {
                "values-template.yaml": "name: testproj\n",
            },
            "applications": {
                "myapp": {
                    "deploy": {"values.yaml": "harness:\n  subdomain: mysubdomain\n"},
                },
            },
        },
    )

    assert (tmp_path / "deployment-configuration").is_dir()
    assert (
        tmp_path / "deployment-configuration" / "values-template.yaml"
    ).read_text() == "name: testproj\n"
    assert (
        tmp_path / "applications" / "myapp" / "deploy" / "values.yaml"
    ).read_text() == ("harness:\n  subdomain: mysubdomain\n")


def test_write_tree_creates_empty_directory(tmp_path):
    write_tree(tmp_path, {"applications": {"dependee": {}}})

    dependee = tmp_path / "applications" / "dependee"
    assert dependee.is_dir()
    assert list(dependee.iterdir()) == []


def test_write_tree_returns_root(tmp_path):
    assert write_tree(tmp_path, {"a.txt": "hello"}) is tmp_path


def test_write_tree_rejects_unsupported_value_type(tmp_path):
    with pytest.raises(TypeError):
        write_tree(tmp_path, {"bad": 123})


def test_write_tree_can_extend_an_existing_directory(tmp_path):
    write_tree(tmp_path, {"applications": {"myapp": {"Dockerfile": "FROM scratch\n"}}})
    write_tree(
        tmp_path, {"applications": {"otherapp": {"Dockerfile": "FROM scratch\n"}}}
    )

    assert (tmp_path / "applications" / "myapp" / "Dockerfile").exists()
    assert (tmp_path / "applications" / "otherapp" / "Dockerfile").exists()


def test_write_tree_from_yaml_creates_nested_files_and_dirs(tmp_path):
    write_tree_from_yaml(
        tmp_path,
        """
        deployment-configuration:
          values-template.yaml: |
            name: testproj
        applications:
          myapp:
            Dockerfile: "FROM scratch\\n"
            deploy:
              values.yaml: |
                harness:
                  subdomain: mysubdomain
    """,
    )

    assert (
        tmp_path / "deployment-configuration" / "values-template.yaml"
    ).read_text() == "name: testproj\n"
    assert (
        tmp_path / "applications" / "myapp" / "Dockerfile"
    ).read_text() == "FROM scratch\n"
    assert (
        tmp_path / "applications" / "myapp" / "deploy" / "values.yaml"
    ).read_text() == ("harness:\n  subdomain: mysubdomain\n")


def test_write_tree_from_yaml_creates_empty_directory(tmp_path):
    write_tree_from_yaml(
        tmp_path,
        """
        applications:
          dependee: {}
    """,
    )

    dependee = tmp_path / "applications" / "dependee"
    assert dependee.is_dir()
    assert list(dependee.iterdir()) == []


def test_write_tree_from_yaml_returns_root(tmp_path):
    assert write_tree_from_yaml(tmp_path, "a.txt: hello\n") is tmp_path


def test_write_tree_from_yaml_rejects_unsupported_value_type(tmp_path):
    with pytest.raises(TypeError):
        write_tree_from_yaml(tmp_path, "bad: 123\n")


def test_write_tree_from_yaml_handles_empty_document(tmp_path):
    assert write_tree_from_yaml(tmp_path, "") is tmp_path
    assert list(tmp_path.iterdir()) == []


def test_write_tree_from_yaml_reads_from_path(tmp_path):
    source = tmp_path / "source.yaml"
    source.write_text(
        "applications:\n  myapp:\n    Dockerfile: |\n      FROM scratch\n"
    )
    out = tmp_path / "out"
    out.mkdir()

    write_tree_from_yaml(out, path=source)

    assert (
        out / "applications" / "myapp" / "Dockerfile"
    ).read_text() == "FROM scratch\n"


def test_write_tree_from_yaml_rejects_both_text_and_path(tmp_path):
    source = tmp_path / "source.yaml"
    source.write_text("a.txt: hello\n")

    with pytest.raises(ValueError):
        write_tree_from_yaml(tmp_path, "a.txt: hello\n", path=source)


def test_write_tree_from_yaml_rejects_neither_text_nor_path(tmp_path):
    with pytest.raises(ValueError):
        write_tree_from_yaml(tmp_path)


def test_discover_root_paths_puts_subdirectories_before_current(tmp_path):
    write_tree(
        tmp_path,
        {
            "deployment-configuration": {},
            "cloud-harness": {"deployment-configuration": {}},
            "applications": {"myapp": {}},
        },
    )

    assert discover_root_paths(tmp_path) == [tmp_path / "cloud-harness", tmp_path]


def test_discover_root_paths_orders_subdirectories_by_name(tmp_path):
    write_tree(
        tmp_path,
        {
            "zeta": {"deployment-configuration": {}},
            "alpha": {"deployment-configuration": {}},
        },
    )

    assert discover_root_paths(tmp_path) == [tmp_path / "alpha", tmp_path / "zeta"]


def test_discover_root_paths_skips_hidden_blueprint_and_nested(tmp_path):
    write_tree(
        tmp_path,
        {
            "deployment-configuration": {},
            ".history": {"deployment-configuration": {}},
            "blueprint": {"deployment-configuration": {}},
            "tools": {"tests": {"resources": {"deployment-configuration": {}}}},
        },
    )

    assert discover_root_paths(tmp_path) == [tmp_path]


def test_discover_root_paths_ignores_deployment_configuration_file(tmp_path):
    write_tree(tmp_path, {"cloud-harness": {"deployment-configuration": "not a dir"}})

    assert discover_root_paths(tmp_path) == []


def test_discover_root_paths_warns_about_a_skipped_scaffold(tmp_path, caplog):
    write_tree(tmp_path, {"blueprint": {"deployment-configuration": {}}, "deployment-configuration": {}})

    assert discover_root_paths(tmp_path) == [tmp_path]
    assert "blueprint" in caplog.text
