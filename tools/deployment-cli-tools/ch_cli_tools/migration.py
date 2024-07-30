"""
Utilities to perform a migration of the deployment to the latest supported version.
"""
import os
import json

from . import HERE
from cloudharness_utils.constants import APPS_PATH
from .utils import get_sub_paths, search_word_in_file, search_word_in_folder

TO_CHECK = ["deploy", "tasks", "Dockerfile"]


def perform_migration(base_root, accept_all=False):
    all_files_detected = []
    for file in os.listdir(os.path.join(HERE, "migrations")):
        f = open(os.path.join(HERE, "migrations", file), "r")
        migration_json = json.load(f)

        sub_paths = []
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

        for app_path in sub_paths:
            # Iterate the folders and files to check if they need to be migrated
            for sub_path in TO_CHECK:
                to_check = os.path.join(app_path, sub_path)
                if os.path.isdir(to_check):
                    for migration_obj in migration_json["deprecated"]:
                        files = search_word_in_folder(to_check, migration_obj["keyword"])
                        for file in files:
                            file_path = os.path.join(to_check, file)
                            print("#########################################")
                            print(f"Running migration on {file_path}")
                            print("#########################################")
                            all_files_detected.append(file_path)
                            for word_to_replace in migration_obj["to_be_replaced"]:
                                read_file_and_replace(
                                    file_path,
                                    word_to_replace["old"],
                                    word_to_replace["new"],
                                    accept_all,
                                )
                elif os.path.isfile(to_check):
                    for migration_obj in migration_json["deprecated"]:
                        if len(search_word_in_file(to_check, migration_obj["keyword"])) > 0:
                            print("#########################################")
                            print(f"Running migration on {to_check}")
                            print("#########################################")
                            all_files_detected.append(to_check)
                            for word_to_replace in migration_obj["to_be_replaced"]:
                                read_file_and_replace(
                                    to_check,
                                    word_to_replace["old"],
                                    word_to_replace["new"],
                                    accept_all,
                                )
    print("=========================================")
    print("=== Cloud Harness migration completed ===")
    print("=========================================")
    print("### Summary of the files to check post migration ###")
    for file in all_files_detected:
        print(f"{file}")
    print("=========================================")
    print("===           End of Summary          ===")
    print("=========================================")


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
