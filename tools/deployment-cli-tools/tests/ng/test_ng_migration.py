"""ch_cli_tools.ng.migration tests. perform_migration is a standalone
search-and-replace tool, independent of CHProject - these exercise it
directly against a throwaway app tree, using the real, shipped migration
rule file (ch_cli_tools/migrations/1_migration.json).
"""

from ch_cli_tools.ng.api import perform_migration
from test_util_ng import write_tree_from_yaml


def test_perform_migration_replaces_deprecated_base_image_name_in_dockerfile(tmp_path):
    write_tree_from_yaml(tmp_path, """
        applications:
          myapp:
            Dockerfile: |
              FROM cloudharness-base-debian
    """)

    perform_migration(str(tmp_path), accept_all=True)

    dockerfile = (tmp_path / "applications" / "myapp" / "Dockerfile").read_text()
    assert dockerfile == "FROM cloudharness-base\n"


def test_perform_migration_replaces_pattern_scoped_keyword_in_yaml(tmp_path):
    write_tree_from_yaml(tmp_path, """
        applications:
          myapp:
            deploy:
              values.yaml: |
                image: CLOUDHARNESS_BASE_DEBIAN
    """)

    perform_migration(str(tmp_path), accept_all=True)

    values = (tmp_path / "applications" / "myapp" / "deploy" / "values.yaml").read_text()
    assert values == "image: CLOUDHARNESS_BASE\n"


def test_perform_migration_leaves_unrelated_content_untouched(tmp_path):
    write_tree_from_yaml(tmp_path, """
        applications:
          myapp:
            Dockerfile: |
              FROM scratch
    """)

    perform_migration(str(tmp_path), accept_all=True)

    dockerfile = (tmp_path / "applications" / "myapp" / "Dockerfile").read_text()
    assert dockerfile == "FROM scratch\n"


def test_perform_migration_accepts_a_list_of_base_roots(tmp_path):
    first = write_tree_from_yaml(tmp_path / "first", """
        applications:
          appone:
            Dockerfile: |
              FROM cloudharness-base-debian
    """)
    second = write_tree_from_yaml(tmp_path / "second", """
        applications:
          apptwo:
            Dockerfile: |
              FROM cloudharness-base-debian
    """)

    perform_migration([str(first), str(second)], accept_all=True)

    assert (first / "applications" / "appone" / "Dockerfile").read_text() == "FROM cloudharness-base\n"
    assert (second / "applications" / "apptwo" / "Dockerfile").read_text() == "FROM cloudharness-base\n"


def test_perform_migration_without_accept_all_prompts_and_respects_the_answer(
    tmp_path, monkeypatch
):
    write_tree_from_yaml(tmp_path, """
        applications:
          myapp:
            Dockerfile: |
              FROM cloudharness-base-debian
    """)
    monkeypatch.setattr("builtins.input", lambda: "n")

    perform_migration(str(tmp_path), accept_all=False)

    dockerfile = (tmp_path / "applications" / "myapp" / "Dockerfile").read_text()
    assert dockerfile == "FROM cloudharness-base-debian\n"
