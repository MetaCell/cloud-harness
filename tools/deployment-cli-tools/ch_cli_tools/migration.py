"""
Utilities to perform a migration of the deployment to the latest supported version.
"""

import os
import json

from . import HERE
from cloudharness_utils.constants import APPS_PATH
from .utils import (
    get_sub_paths,
    search_word_in_file,
    search_word_in_folder,
    search_word_by_pattern,
)

TO_CHECK = ["deploy", "tasks", "Dockerfile"]


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


def perform_migration(base_root, accept_all=False):
    all_files_detected = []

    # Iterate the list of files and replace the old word with the new word
    def replace_in_files(app_path, files, words):
        for file in files:
            file_path = os.path.join(app_path, file)
            print(f">>> Running migration on {file_path} <<<")
            all_files_detected.append(file_path)
            for word_to_replace in words:
                read_file_and_replace(
                    file_path,
                    word_to_replace["old"],
                    word_to_replace["new"],
                    accept_all,
                )

    # Iterate migrations, patterns and search the keyword using the pattern given.
    # If the keyword is found then replace the list of words given from the old to the new
    def run_migrations_with_pattern(app_path, with_pattern):
        for single_migration in with_pattern:
            for pattern in single_migration["patterns"]:
                results = search_word_by_pattern(
                    app_path, pattern, single_migration["keyword"]
                )
                replace_in_files(
                    app_path,
                    results,
                    single_migration["to_be_replaced"]
                )

    # Iterate the TO_CHECK array that is set to search inside the deploy and tasks folder
    # plus the Dockerfile. If the keyword is found inside one of these folders or in the
    # Dockerfile then replace the list of words given from the old to the new
    def run_migrations_without_pattern(app_path, without_pattern):
        for sub_path in TO_CHECK:
            to_check = os.path.join(app_path, sub_path)
            if os.path.isdir(to_check):
                for migration_obj in without_pattern:
                    files = search_word_in_folder(
                        to_check,
                        migration_obj["keyword"]
                    )
                    replace_in_files(
                        app_path,
                        files,
                        migration_obj["to_be_replaced"]
                    )
            elif os.path.isfile(to_check):
                for migration_obj in without_pattern:
                    keyword = migration_obj["keyword"]
                    if len(search_word_in_file(to_check, keyword)) > 0:
                        print(f">>> Running migration on {to_check} <<<")
                        all_files_detected.append(to_check)
                        for word_to_replace in migration_obj["to_be_replaced"]:
                            read_file_and_replace(
                                to_check,
                                word_to_replace["old"],
                                word_to_replace["new"],
                                accept_all,
                            )

    # Parse the migration and separate the ones with patterns and without
    def extract_migrations(migration_obj):
        migrations_with_pattern = []
        migrations_without_pattern = []
        for single_migration in migration_obj["deprecated"]:
            if "patterns" in single_migration:
                migrations_with_pattern.append(single_migration)
            else:
                migrations_without_pattern.append(single_migration)
        return migrations_with_pattern, migrations_without_pattern

    # Iterate all the migration files and run the migrations
    for file in os.listdir(os.path.join(HERE, "migrations")):
        with open(os.path.join(HERE, "migrations", file), "r") as f:
            migration_dict = json.load(f)

            sub_paths = []
            # Find all the apps in the base root
            if isinstance(base_root, list):
                app_base_path = [
                    os.path.join(base_root_path, APPS_PATH)
                    for base_root_path in base_root
                ]
                for app_path in app_base_path:
                    sub_paths.extend(get_sub_paths(app_path))
            else:
                app_base_path = os.path.join(base_root, APPS_PATH)
                sub_paths = get_sub_paths(app_base_path)

            with_pattern, without_pattern = extract_migrations(migration_dict)
            # Iterate all the application folders and run the migrations
            for app_path in sub_paths:
                run_migrations_with_pattern(app_path, with_pattern)
                run_migrations_without_pattern(app_path, without_pattern)
    print("=========================================")
    print(">>> Cloud Harness migration completed <<<")
    print("=========================================")
    print(">>>         Migration Summary         <<<")
    for file in all_files_detected:
        print(f"{file}")
    print("=========================================")
    print(">>>           End of Summary          <<<")
    print("=========================================")
