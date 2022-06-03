from email.mime import base
from genericpath import exists
import os

import shutil
from glob import glob
from os.path import join, basename, isabs, relpath

from cloudharness_utilities.helm import KEY_APPS, KEY_TASK_IMAGES

from .utils import app_name_from_path, merge_app_directories, merge_configuration_directories, find_subdirs
from .constants import APPS_PATH, HELM_CHART_PATH, DEPLOYMENT_CONFIGURATION_PATH, DEPLOYMENT_PATH, \
    BASE_IMAGES_PATH, STATIC_IMAGES_PATH



def preprocess_build_overrides(root_paths, helm_values, merge_build_path=".overrides"):
    if not isabs(merge_build_path):
        merge_build_path = join(os.getcwd(), merge_build_path)
    if len(root_paths) < 2:
        return root_paths
    if not os.path.exists(merge_build_path):
        os.makedirs(merge_build_path)
    else:
        shutil.rmtree(merge_build_path)
    merged = False
    artifacts = {}

    def merge_appdir(root_path, base_path):
        app_name = app_name_from_path(basename(base_path))
        dest_path = join(
                        merge_build_path,
                        relpath( base_path, root_path)
                    )
        merge_configuration_directories(artifacts[app_name], dest_path)
        merge_configuration_directories(base_path, dest_path)
        

    for root_path in root_paths:

        for base_path in find_subdirs(join(root_path, BASE_IMAGES_PATH)):
            app_name = app_name_from_path(basename(base_path))
            if app_name not in artifacts:
                artifacts[app_name] = base_path
            elif app_name in helm_values[KEY_TASK_IMAGES]:
                libraries_path = join(root_path, 'libraries')
                if exists(libraries_path):
                    merge_configuration_directories(
                        libraries_path,
                        join(merge_build_path, 'libraries')
                    )
                merge_appdir(root_path, base_path)
                merged = True

    for root_path in root_paths:
        for base_path in find_subdirs(join(root_path, STATIC_IMAGES_PATH)):
            app_name = app_name_from_path(basename(base_path))
            if app_name not in artifacts:
                artifacts[app_name] = base_path
            elif app_name in helm_values[KEY_TASK_IMAGES]:
                merge_appdir(root_path, base_path)
                merged = True

    for root_path in root_paths:
        for base_path in find_subdirs(join(root_path, APPS_PATH)):
            app_name = app_name_from_path(basename(base_path))
            if app_name not in artifacts:
                artifacts[app_name] = base_path

            elif app_name.replace("-", "_") in helm_values[KEY_APPS]:
                merge_appdir(root_path, base_path)
                merged = True

    return (root_paths + [merge_build_path]) if merged else root_paths

def get_build_paths(root_paths, helm_values, merge_build_path=".overrides"):
    """
    Gets the same paths from preprocess_build_overrides
    """
    if not isabs(merge_build_path):
        merge_build_path = join(os.getcwd(), merge_build_path)

    artifacts = {}

    for root_path in root_paths:

        for base_path in find_subdirs(join(root_path, BASE_IMAGES_PATH)):
            app_name = app_name_from_path(basename(base_path))
            if app_name not in helm_values[KEY_TASK_IMAGES]:
                continue
            if app_name not in artifacts:
                artifacts[app_name] = base_path
            else:
                artifacts[app_name] = join(
                        merge_build_path,
                        relpath( base_path, root_path)
                    )
    for root_path in root_paths:
        for base_path in find_subdirs(join(root_path, STATIC_IMAGES_PATH)):
            
            app_name = app_name_from_path(basename(base_path))
            if app_name not in helm_values[KEY_TASK_IMAGES]:
                continue
            if app_name not in artifacts:
                artifacts[app_name] = base_path
            else:
                artifacts[app_name] = join(
                        merge_build_path,
                        relpath( base_path, root_path)
                    )

    for root_path in root_paths:
        for base_path in find_subdirs(join(root_path, APPS_PATH)):
            app_name = app_name_from_path(basename(base_path))
            if app_name.replace("-", "_") not in helm_values[KEY_APPS]:
                continue
            if app_name not in artifacts:
                artifacts[app_name] = base_path
            else:
                artifacts[app_name] = join(
                        merge_build_path,
                        relpath( base_path, root_path)
                    )

    return artifacts
