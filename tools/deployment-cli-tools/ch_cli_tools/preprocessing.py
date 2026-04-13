from genericpath import exists
import os
import logging
from hashlib import sha1

import shutil
from glob import glob
from os.path import join, basename, dirname, isabs, relpath

from .helm import KEY_APPS, KEY_TASK_IMAGES, KEY_HARNESS, KEY_DEPLOYMENT
from .configurationgenerator import DEFAULT_IGNORE, generate_tag_from_content

from .utils import app_name_from_path, merge_app_directories, merge_configuration_directories, find_subdirs, read_dockerignore, guess_build_dependencies_from_dockerfile
from cloudharness_utils.constants import APPS_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH, DEFAULT_MERGE_PATH, EXCLUDE_PATHS


def preprocess_build_overrides(root_paths, helm_values, merge_build_path=DEFAULT_MERGE_PATH):
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
        app_key = app_name_from_path(basename(base_path))
        dest_path = join(
            merge_build_path,
            relpath(base_path, root_path)
        )
        exclude = read_dockerignore(artifacts[app_key])
        merge_configuration_directories(artifacts[app_key], dest_path, exclude=exclude or tuple(EXCLUDE_PATHS))
        merge_configuration_directories(
            base_path, dest_path,
            exclude=read_dockerignore(base_path) or exclude or tuple(EXCLUDE_PATHS)
        )

    for root_path in root_paths:

        for base_path in find_subdirs(join(root_path, BASE_IMAGES_PATH)):
            app_name = app_name_from_path(basename(base_path))
            exclude = read_dockerignore(base_path) or tuple(EXCLUDE_PATHS)
            if app_name not in artifacts:
                artifacts[app_name] = base_path
            elif app_name in helm_values[KEY_TASK_IMAGES]:
                libraries_path = join(root_path, 'libraries')
                if exists(libraries_path):
                    merge_configuration_directories(
                        libraries_path,
                        join(merge_build_path, 'libraries'),
                        exclude=exclude
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
            elif app_name in helm_values[KEY_APPS]:
                merge_appdir(root_path, base_path)
                merged = True

    if exists(merge_build_path):
        with open(join(merge_build_path, ".dockerignore"), "a") as dst:

            for root_path in root_paths:
                ignore_file = join(root_path, ".dockerignore")
                if os.path.exists(ignore_file):
                    with open(ignore_file) as src:
                        dst.write(src.read())

    return (root_paths + [merge_build_path]) if merged else root_paths


def get_build_paths(root_paths, helm_values, merge_build_path=DEFAULT_MERGE_PATH):
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
                    relpath(base_path, root_path)
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
                    relpath(base_path, root_path)
                )

    for root_path in root_paths:
        for base_path in find_subdirs(join(root_path, APPS_PATH)):
            app_name = app_name_from_path(basename(base_path))
            if app_name not in helm_values[KEY_APPS]:
                continue
            if app_name not in artifacts:
                artifacts[app_name] = base_path
            else:
                artifacts[app_name] = join(
                    merge_build_path,
                    relpath(base_path, root_path)
                )

            for task_path in find_subdirs(join(base_path, 'tasks')):
                task_name = app_name_from_path(relpath(task_path, dirname(base_path)))
                if task_name not in helm_values.get(KEY_TASK_IMAGES, {}):
                    continue
                if task_name not in artifacts:
                    artifacts[task_name] = task_path
                else:
                    artifacts[task_name] = join(
                        merge_build_path,
                        relpath(task_path, root_path)
                    )

    return artifacts


def _split_image_name_and_tag(image_name: str):
    last_slash = image_name.rfind('/')
    last_colon = image_name.rfind(':')
    if last_colon > last_slash:
        return image_name[:last_colon], image_name[last_colon + 1:]
    return image_name, None


def _set_image_tag(image_name: str, new_tag: str) -> str:
    base_name, _ = _split_image_name_and_tag(image_name)
    return f"{base_name}:{new_tag}" if new_tag else base_name


def generate_hash_based_image_tags(root_paths, helm_values, merge_build_path=DEFAULT_MERGE_PATH):
    """Recalculate hash-based tags for buildable images using merged build paths.

    This should be called after preprocess_build_overrides. It updates only
    images that are marked to be built in values and keeps existing registry/
    image names unchanged.
    """

    build_paths = get_build_paths(root_paths=root_paths, helm_values=helm_values, merge_build_path=merge_build_path)
    if not build_paths:
        return helm_values

    image_specs = {}

    for app_name, app_values in helm_values.get(KEY_APPS, {}).items():
        if app_name not in build_paths:
            continue
        if app_values.get('build', True) is False:
            continue

        image_name = app_values.get('image') or app_values.get(KEY_HARNESS, {}).get(KEY_DEPLOYMENT, {}).get('image')
        if not image_name:
            continue

        build_dependencies = app_values.get(KEY_HARNESS, {}).get('dependencies', {}).get('build', [])
        image_specs[app_name] = {
            'kind': KEY_APPS,
            'image': image_name,
            'context': build_paths[app_name],
            'dependencies': list(build_dependencies),
        }

    base_image_contexts = {}
    for root_path in root_paths:
        for base_path in find_subdirs(join(root_path, BASE_IMAGES_PATH)):
            base_key = app_name_from_path(basename(base_path))
            # Keep the last occurrence to preserve override precedence used in
            # the original first-pass base image tagging logic.
            base_image_contexts[base_key] = root_path

    for image_key, image_name in helm_values.get(KEY_TASK_IMAGES, {}).items():
        if image_key not in build_paths or not image_name:
            continue

        context_path = base_image_contexts.get(image_key, build_paths[image_key])
        image_specs[image_key] = {
            'kind': KEY_TASK_IMAGES,
            'image': image_name,
            'context': context_path,
            'dependencies': list(guess_build_dependencies_from_dockerfile(build_paths[image_key])),
        }

    if not image_specs:
        return helm_values

    calculated_tags = {}
    pending = set(image_specs.keys())

    while pending:
        progressed = False
        for image_key in list(pending):
            deps = image_specs[image_key]['dependencies']
            unresolved = [dep for dep in deps if dep in image_specs and dep not in calculated_tags]
            if unresolved:
                continue

            context_path = image_specs[image_key]['context']
            ignore_path = os.path.join(context_path, '.dockerignore')
            ignore = set(DEFAULT_IGNORE)
            if os.path.exists(ignore_path):
                with open(ignore_path) as f:
                    ignore = ignore.union({line.strip() for line in f if line.strip() and not line.startswith('#')})

            content_hash = generate_tag_from_content(context_path, ignore)
            dep_tags = "".join(calculated_tags.get(dep, '') for dep in deps)
            calculated_tags[image_key] = sha1((content_hash + dep_tags).encode('utf-8')).hexdigest()

            pending.remove(image_key)
            progressed = True

        if not progressed:
            logging.warning("Could not resolve all hash-tag dependencies for %s, computing remaining tags without dependency chaining", ','.join(sorted(pending)))
            for image_key in list(pending):
                context_path = image_specs[image_key]['context']
                ignore_path = os.path.join(context_path, '.dockerignore')
                ignore = set(DEFAULT_IGNORE)
                if os.path.exists(ignore_path):
                    with open(ignore_path) as f:
                        ignore = ignore.union({line.strip() for line in f if line.strip() and not line.startswith('#')})
                content_hash = generate_tag_from_content(context_path, ignore)
                calculated_tags[image_key] = sha1(content_hash.encode('utf-8')).hexdigest()
                pending.remove(image_key)

    for image_key, image_tag in calculated_tags.items():
        image_spec = image_specs[image_key]
        retagged = _set_image_tag(image_spec['image'], image_tag)

        if image_spec['kind'] == KEY_APPS and image_key in helm_values[KEY_APPS]:
            app_values = helm_values[KEY_APPS][image_key]
            app_values['image'] = retagged
            if KEY_HARNESS in app_values and KEY_DEPLOYMENT in app_values[KEY_HARNESS]:
                app_values[KEY_HARNESS][KEY_DEPLOYMENT]['image'] = retagged
        elif image_spec['kind'] == KEY_TASK_IMAGES and image_key in helm_values[KEY_TASK_IMAGES]:
            helm_values[KEY_TASK_IMAGES][image_key] = retagged

    return helm_values
