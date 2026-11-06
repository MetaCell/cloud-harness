"""Applies deprecated-pattern migrations across every application in a
CloudHarness project.

Reuses the migration-rule JSON files (ch_cli_tools/migrations/*.json - a
"deprecated" list of {keyword, to_be_replaced, patterns?} rules) and the
existing search/replace utilities (ch_cli_tools.utils.search_word_by_pattern/
search_word_in_folder/search_word_in_file) directly - this is a standalone
text search-and-replace tool, independent of CHProject/values.yaml parsing,
so there's no model concept to port, only the orchestration loop.

perform_migration() algorithm:
1. For each base root, list every applications/* subdirectory.
2. For each migration rule file (sorted for a deterministic order), split its
   rules into "with a glob pattern" (searched via that pattern, e.g.
   **/Dockerfile) and "without one" (searched under each app's own deploy/,
   tasks/ and Dockerfile only).
3. For every match, replace each declared old->new pair, prompting per line
   unless accept_all is set.
"""

import json
from pathlib import Path

from ch_cli_tools.utils import (  # type: ignore
    get_sub_paths,
    search_word_by_pattern,
    search_word_in_file,
    search_word_in_folder,
)
from cloudharness_utils.constants import APPS_PATH

TO_CHECK = ("deploy", "tasks", "Dockerfile")
_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def read_file_and_replace(file, old, new, accept_all=False):
    file_p = open(file, "r+")
    lines = file_p.readlines()
    file_p.seek(0)
    for line in lines:
        if old in line:
            print(f"Found {old} in {file}")

            if not accept_all:
                print(f"Would you like to replace:")
                print(line)
                print(f"with:")
                print(line.replace(old, new))
                print("y/n")

            if accept_all:
                file_p.write(line.replace(old, new))
            elif input() == "y":
                file_p.write(line.replace(old, new))
            else:
                file_p.write(line)
        else:
            file_p.write(line)
    file_p.truncate()
    file_p.close()


def _extract_migrations(migration: dict) -> tuple[list[dict], list[dict]]:
    with_pattern, without_pattern = [], []
    for rule in migration["deprecated"]:
        (with_pattern if "patterns" in rule else without_pattern).append(rule)
    return with_pattern, without_pattern


def _replace_in_files(files, words, accept_all: bool) -> None:
    for file_path in files:
        for word in words:
            read_file_and_replace(file_path, word["old"], word["new"], accept_all)


def _run_with_pattern(app_path: str, rules: list[dict], accept_all: bool) -> list[str]:
    detected = []
    for rule in rules:
        for pattern in rule["patterns"]:
            matches = search_word_by_pattern(app_path, pattern, rule["keyword"])
            detected.extend(matches)
            _replace_in_files(matches, rule["to_be_replaced"], accept_all)
    return detected


def _run_without_pattern(app_path: str, rules: list[dict], accept_all: bool) -> list[str]:
    detected = []
    for sub_path in TO_CHECK:
        to_check = Path(app_path) / sub_path
        for rule in rules:
            if to_check.is_dir():
                matches = search_word_in_folder(str(to_check), rule["keyword"])
            elif to_check.is_file():
                matches = search_word_in_file(str(to_check), rule["keyword"])
            else:
                continue
            detected.extend(matches)
            _replace_in_files(matches, rule["to_be_replaced"], accept_all)
    return detected


def perform_migration(base_root, accept_all=False) -> None:
    base_roots = base_root if isinstance(base_root, list) else [base_root]
    app_paths = [
        app_path
        for root in base_roots
        for app_path in get_sub_paths(str(Path(root) / APPS_PATH))
    ]

    all_files_detected = []
    for migration_file in sorted(_MIGRATIONS_DIR.iterdir()):
        migration = json.loads(migration_file.read_text())
        with_pattern, without_pattern = _extract_migrations(migration)
        for app_path in app_paths:
            all_files_detected.extend(_run_with_pattern(app_path, with_pattern, accept_all))
            all_files_detected.extend(_run_without_pattern(app_path, without_pattern, accept_all))

    print("=========================================")
    print(">>> Cloud Harness migration completed <<<")
    print("=========================================")
    print(">>>         Migration Summary         <<<")
    for file in all_files_detected:
        print(file)
    print("=========================================")
    print(">>>           End of Summary          <<<")
    print("=========================================")
