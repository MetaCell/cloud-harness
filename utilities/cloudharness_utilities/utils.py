import glob
import subprocess
import os
import collections
import oyaml as yaml
import shutil
import logging

from .constants import HERE, NEUTRAL_PATHS, DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH, APPS_PATH

def image_name_from_docker_path(dockerfile_path):
    return get_image_name("-".join(p for p in dockerfile_path.split("/") if p not in NEUTRAL_PATHS))


def get_sub_paths(base_path):
    return tuple(path for path in glob.glob(base_path + "/*") if os.path.isdir(path))


def find_dockerfiles_paths(base_directory):
    return tuple(os.path.dirname(path).replace(os.path.sep, "/") for path in
                 glob.glob(f"{base_directory}/**/Dockerfile", recursive=True))


def get_parent_app_name(app_relative_path):
    return app_relative_path.split("/")[0] if "/" in app_relative_path else ""


def get_image_name(app_name, base_name=None):
    return base_name + '-' + app_name if base_name else app_name


def get_image_name_from_dockerfile_path(self, dockerfile_path, base_name):
    return get_image_name(os.path.basename(os.path.dirname(dockerfile_path)), base_name)


def env_variable(name, value):
    return {'name': f"{name}".upper(), 'value': value}


def get_cluster_ip():
    out = subprocess.check_output(['kubectl', 'cluster-info'], timeout=10).decode("utf-8")
    print(type(out))
    ip = out.split('\n')[0].split('://')[1].split(':')[0]
    return ip


def get_template(yaml_path):
    with open(os.path.join(HERE, DEPLOYMENT_CONFIGURATION_PATH, os.path.basename(yaml_path))) as f:
        dict_template = yaml.safe_load(f)
    if os.path.exists(yaml_path):
        with open(yaml_path) as f:
            override_tpl = yaml.safe_load(f)
            if override_tpl:
                dict_template = dict_merge(dict_template, override_tpl)
    return dict_template


def file_is_yaml(fname):
    return fname[-4:] == 'yaml' or fname[-3:] == 'yml'


def merge_configuration_directories(source, dest):
    if not os.path.exists(dest):
        shutil.copytree(source, dest)
        return

    for fname in glob.glob(source + "/*"):
        frel = os.path.relpath(fname, start=source)
        fdest = os.path.join(dest, frel)

        if os.path.isdir(fname):
            merge_configuration_directories(fname, fdest)
            continue

        if not os.path.exists(fdest):
            shutil.copy(fname, fdest)
        elif file_is_yaml(fname):

            try:
                merge_yaml_files(fname, fdest)
                logging.info(f"Merged/overridden file content of {fdest} with {fname}")
            except yaml.YAMLError as e:
                logging.warning(f"Overwriting file {fdest} with {fname}")
                shutil.copy(fname, fdest)
        else:
            logging.warning(f"Overwriting file {fdest} with {fname}")
            shutil.copy(fname, fdest)


def merge_yaml_files(fname, fdest):
    with open(fname) as f:
        content_src = yaml.safe_load(f)
    merge_to_yaml_file(content_src, fdest)


def merge_to_yaml_file(content_src, fdest):
    if not content_src:
        return
    if not os.path.exists(fdest):
        merged = content_src
    else:
        with open(fdest) as f:
            content_dest = yaml.safe_load(f)

        merged = dict_merge(content_dest, content_src) if content_dest else content_src

    if not os.path.exists(os.path.dirname(fdest)):
        os.makedirs(os.path.dirname(fdest))
    with open(fdest, "w") as f:
        yaml.dump(merged, f)
    return merged


def dict_merge(dct, merge_dct, add_keys=True):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.

    This version will return a copy of the dictionary and leave the original
    arguments untouched.

    The optional argument ``add_keys``, determines whether keys which are
    present in ``merge_dict`` but not ``dct`` should be included in the
    new dict.

    Args:
        dct (dict) onto which the merge is executed
        merge_dct (dict): dct merged into dct
        add_keys (bool): whether to add new keys

    Returns:
        dict: updated dict
    """
    dct = dct.copy()
    if not add_keys:
        merge_dct = {
            k: merge_dct[k]
            for k in set(dct).intersection(set(merge_dct))
        }

    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dct[k] = dict_merge(dct[k], merge_dct[k], add_keys=add_keys)
        else:
            dct[k] = merge_dct[k]

    return dct


def find_under_path(base_path, context_path=None, root_path=None, validate=None):
    """ Finds dockerfiles and creates a list containig path info for each dockerfile.

    Find all dockerfiles inside a folder and creates a list of dictionaries containing
    path information to build the docker images.

    Returns:
        A List with the required information to build each docker image. For example:

        [
            {
                "name": "cloudharness-base"
                "rel_path": "infrastructure/base-images/cloudharness-base",
                "abs_path": "/opt/cloud-harness/infrastructure/base-images/cloudharness-base",
                "context_path": "/opt/cloud-harness",
                "origin": "infrastructure/base-images"
            },
            ...
        ]
    """
    founds = []
    abs_base_path = os.path.join(root_path, base_path)
    if validate is None:
        docker_files = [path for path in find_dockerfiles_paths(abs_base_path)]
    else:
        docker_files = (path for path in find_dockerfiles_paths(abs_base_path) if validate(path))

    for dockerfile_path in docker_files:
        dockerfile_rel_path = "" if not context_path else os.path.relpath(dockerfile_path, start=context_path)
        # extract image name
        image_name = image_name_from_docker_path(os.path.relpath(dockerfile_path, start=abs_base_path))
        founds.append({'name': image_name,
                       'rel_path': dockerfile_rel_path,
                       'abs_path': dockerfile_path,
                       'context_path': context_path,
                       'origin': base_path})
    return founds


def merge_found_paths(new:[dict], found: [[dict]] = [])->None:
    """ Add new dockerfile paths to list of found paths

    In case cloud-harness and a cloud-harness based project both are building the
    same image, two items will be returned (see example below).

    Example:
        >>> found = [
            [
                {
                    "name": "cloudharness-base"
                    "rel_path": "infrastructure/base-images/cloudharness-base",
                    "abs_path": "/opt/cloud-harness/infrastructure/base-images/cloudharness-base",
                    "context_path": "/opt/cloud-harness",
                    "origin": "infrastructure/base-images"
                }
            ],
            [
                {
                    "name": "accounts"
                    "rel_path": "",
                    "abs_path": "/opt/cloud-harness/applications/accounts",
                    "context_path": None,
                    "origin": "applications"
                }
            ]
        ]
        >>> new = [
            {
                "name": "accounts"
                "rel_path": "",
                "abs_path": "/opt/my-harness-project/./applications/accounts",
                "context_path": None,
                "origin": "applications"
            }
        ]
        >>> merge_found_paths(new, found)
        [
            [
                {
                    "name": "cloudharness-base"
                    "rel_path": "infrastructure/base-images/cloudharness-base",
                    "abs_path": "/opt/cloud-harness/infrastructure/base-images/cloudharness-base",
                    "context_path": "/opt/cloud-harness",
                    "origin": "infrastructure/base-images"
                }
            ],
            [
                {
                    "name": "accounts"
                    "rel_path": "",
                    "abs_path": "/opt/cloud-harness/applications/accounts",
                    "context_path": None,
                    "origin": "applications"
                },
                {
                    "name": "accounts"
                    "rel_path": "",
                    "abs_path": "/opt/my-harness-project/./applications/accounts",
                    "context_path": None,
                    "origin": "applications"
                }
            ]
        ]
    """
    found_names = {}
    for item in found:
        found_names[item[0]['name']] = True

    # merge new items into found collection
    for new_item in new:
        if found_names.get(new_item['name'], False):
            for found_item in found:
                if found_item[0]['name'] == new_item['name']:
                    found_item.append(new_item)
                    break
        else:
            found.append([new_item])


def collect_under_paths(root_paths, validate) -> [[dict]]:
        """ Collect all path information in a CH project to build the docker images

        In case cloud-harness and a cloud-harness based project both are building the
        same image, two items will be created (see example below).

        Returns:
            A List with the required information to build each docker image. For example:
            [
                [
                    {
                        "name": "cloudharness-base"
                        "rel_path": "infrastructure/base-images/cloudharness-base",
                        "abs_path": "/opt/cloud-harness/infrastructure/base-images/cloudharness-base",
                        "context_path": "/opt/cloud-harness",
                        "origin": "infrastructure/base-images"
                    }
                ],
                [
                    {
                        "name": "accounts"
                        "rel_path": "",
                        "abs_path": "/opt/cloud-harness/applications/accounts",
                        "context_path": None,
                        "origin": "applications"
                    },
                    {
                        "name": "accounts"
                        "rel_path": "",
                        "abs_path": "/opt/my-harness-project/./applications/accounts",
                        "context_path": None,
                        "origin": "applications"
                    }
                ],
                ...
            ]
        """
        collected = []

        for root_path in root_paths:
            batch = []
            batch += find_under_path(BASE_IMAGES_PATH, context_path=root_path, 
                                     root_path=root_path, validate=validate)
            # Build static images that will be use as base for other images
            batch += find_under_path(STATIC_IMAGES_PATH, root_path=root_path, validate=validate)
            batch += find_under_path(APPS_PATH, root_path=root_path, validate=validate)
            
            merge_found_paths(batch, collected)

        return collected



def merge_app_directories(root_paths, validate)->None:
        """ Merge directories if they refer to the same application
        
        If an application's folder is found both in cloud-harness and
        in the cloud-harness based project, then the directories are 
        merged together in cloudharness directory and the other directory
        is deleted.
        """
        for dpaths in collect_under_paths(root_paths, validate):
            if len(dpaths) != 1:
                log_merging_operation(dpaths)
                for index, dpath in enumerate(dpaths):
                    if index != 0:
                        logging.info("[MERGE] (%s) into (%s)" % (dpath['abs_path'], dpaths[0]['abs_path']))
                        merge_configuration_directories(dpath['abs_path'], dpaths[0]['abs_path'])
                        shutil.rmtree(dpath['abs_path'])

def log_merging_operation(dpaths:[dict]) -> None:
        logging_message = f"\n\nFound multiple dockerfiles for the next image ({dpaths[0]['name']}):\n\n"
        for dpath in dpaths:
            logging_message += f"{dpath['abs_path']}\n"
        logging_message += "\nWill proceed to merge the two folder.\n\n"
        logging.info(logging_message)