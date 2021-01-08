import glob
import subprocess
import os
import collections
import oyaml as yaml
import shutil
import logging
import fileinput

from .constants import HERE, NEUTRAL_PATHS, DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH, \
    APPS_PATH, BUILD_FILENAMES


def app_name_from_path(dockerfile_path):
    return get_image_name("-".join(p for p in dockerfile_path.split("/") if p not in NEUTRAL_PATHS))


def get_sub_paths(base_path):
    return tuple(path for path in glob.glob(base_path + "/*") if os.path.isdir(path))


def find_dockerfiles_paths(base_directory):
    return tuple(os.path.dirname(path).replace(os.path.sep, "/") for path in
                 glob.glob(f"{base_directory}/**/Dockerfile", recursive=True))


def get_parent_app_name(app_relative_path):
    return app_relative_path.split("/")[0] if "/" in app_relative_path else ""


def get_image_name(app_name, base_name=None):
    return base_name + '/' + app_name if base_name else app_name


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

def replaceindir(root_src_dir, source, replace):
    """
    Does copy and merge (shutil.copytree requires that the destination does not exist)
    :param root_src_dir:
    :param root_dst_dir:
    :return:
    """
    logging.info('Replacing in directory %s to %s', source, replace)
    for src_dir, dirs, files in os.walk(root_src_dir):
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            with fileinput.FileInput(src_file, inplace=True) as file:
                for line in file:
                    print(line.replace(source, replace), end='')

def copymergedir(root_src_dir, root_dst_dir):
    """
    Does copy and merge (shutil.copytree requires that the destination does not exist)
    :param root_src_dir:
    :param root_dst_dir:
    :return:
    """
    logging.info('Copying directory %s to %s', root_src_dir, root_dst_dir)
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            try:
                shutil.copy(src_file, dst_dir)
            except:
                logging.warning("Error copying file %s to %s.", src_file, dst_dir)

def movedircontent(root_src_dir, root_dst_dir):
    """
    Does copy and merge (shutil.copytree requires that the destination does not exist)
    :param root_src_dir:
    :param root_dst_dir:
    :return:
    """
    logging.info('Moving directory content from %s to %s', root_src_dir, root_dst_dir)
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)

            try:
                shutil.move(src_file, os.path.join(dst_dir, os.path.basename(src_file)))
            except:
                logging.warning("Error moving file %s to %s.", src_file, dst_dir, exc_info=True)

def merge_configuration_directories(source, dest):
    if not os.path.exists(source):
        return
    if not os.path.exists(dest):
        shutil.copytree(source, dest)
        return

    for fname in glob.glob(source + "/*"):
        frel = os.path.relpath(fname, start=source)
        fdest = os.path.join(dest, frel)

        if os.path.basename(fname) in BUILD_FILENAMES:
            continue

        if os.path.isdir(fname):
            merge_configuration_directories(fname, fdest)
            continue

        if not os.path.exists(fdest):
            shutil.copy2(fname, fdest)
        elif file_is_yaml(fname):

            try:
                merge_yaml_files(fname, fdest)
                logging.info(f"Merged/overridden file content of {fdest} with {fname}")
            except yaml.YAMLError as e:
                logging.warning(f"Overwriting file {fdest} with {fname}")
                shutil.copy2(fname, fdest)
        else:
            logging.warning(f"Overwriting file {fdest} with {fname}")
            shutil.copy2(fname, fdest)


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


def merge_app_directories(root_paths, destination) -> None:
    """ Merge directories if they refer to the same application

    Directories are merged in the destination from the root_paths list. The latter overrides the former.
    Yaml files are merged, other files are overwritten.
    """
    if not os.path.exists(destination):
        os.makedirs(destination)
    else:
        shutil.rmtree(destination)

    for rpath in root_paths:
        merge_configuration_directories(os.path.join(rpath, BASE_IMAGES_PATH),
                                        os.path.join(destination, BASE_IMAGES_PATH))
        merge_configuration_directories(os.path.join(rpath, STATIC_IMAGES_PATH),
                                        os.path.join(destination, STATIC_IMAGES_PATH))
        merge_configuration_directories(os.path.join(rpath, APPS_PATH),
                                        os.path.join(destination, APPS_PATH))
        merge_configuration_directories(os.path.join(rpath, 'libraries'),
                                        os.path.join(destination, 'libraries'))
        merge_configuration_directories(os.path.join(rpath, 'client'),
                                        os.path.join(destination, 'client'))
        merge_configuration_directories(os.path.join(rpath, 'deployment-configuration'),
                                        os.path.join(destination, 'deployment-configuration'))