
import socket
import glob
import subprocess
import os
from os.path import join, dirname, isdir, basename, exists, relpath, sep, dirname as dn
import json
import collections
import requests
from ruamel.yaml import YAML
import shutil
import logging
import fileinput

from cloudharness_utils.constants import NEUTRAL_PATHS, DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH, \
    APPS_PATH, BUILD_FILENAMES, EXCLUDE_PATHS
from . import CH_ROOT

yaml = YAML(typ='safe')
BASE_TEMPLATES_PATH = CH_ROOT


REPLACE_TEXT_FILES_EXTENSIONS = (
    '.js', '.md', '.py', '.js', '.ts', '.tsx', '.txt', 'Dockerfile', 'yaml', 'json', '.ejs'
)


def image_name_from_dockerfile_path(dockerfile_path, base_name=None):
    return get_image_name(app_name_from_path(dockerfile_path), base_name)


def app_name_from_path(dockerfile_path):
    return "-".join(p for p in dockerfile_path.split("/") if p not in NEUTRAL_PATHS)


def get_sub_paths(base_path):
    return tuple(path for path in glob.glob(base_path + "/*") if isdir(path))


def find_file_paths(base_directory, file_name):
    return tuple(dirname(path).replace(sep, "/") for path in
                 glob.glob(f"{base_directory}/**/{file_name}", recursive=True))


def find_subdirs(base_path):
    if exists(base_path):
        return (join(base_path, d) for d in os.listdir(base_path) if isdir(join(base_path, d)))
    return tuple()


def find_dockerfiles_paths(base_directory):
    return find_file_paths(base_directory, 'Dockerfile')


def get_parent_app_name(app_relative_path):
    return app_relative_path.split("/")[0] if "/" in app_relative_path else ""


def get_image_name(app_name, base_name=None):
    return (base_name + '/' + app_name) if base_name else app_name


def env_variable(name, value):
    return {'name': f"{name}".upper(), 'value': value}


def get_cluster_ip():
    out = subprocess.check_output(
        ['kubectl', 'cluster-info'], timeout=10).decode("utf-8")
    ip = out.split('\n')[0].split('://')[1].split(':')[0]
    return ip if not "kubernetes.docker.internal" == ip else get_host_address()


def get_host_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    return s.getsockname()[0]


def robust_load_json(json_path):
    """
    Supports json with // comments
    """
    try:
        with open(json_path) as f:
            return json.load(f)
    except:
        with open(json_path) as f:
            return json.loads("".join(line for line in f if "//" not in line))


def get_json_template(json_path, base_default=False):
    default_template_path = join(
        BASE_TEMPLATES_PATH, DEPLOYMENT_CONFIGURATION_PATH, basename(json_path))
    dict_template = {}
    if base_default and exists(default_template_path):
        dict_template = robust_load_json(default_template_path)
    if exists(json_path):
        override_tpl = robust_load_json(json_path)
        if override_tpl:
            dict_template = dict_merge(dict_template or {}, override_tpl)
    return dict_template or {}


def get_template(yaml_path, base_default=False):
    default_template_path = join(
        BASE_TEMPLATES_PATH, DEPLOYMENT_CONFIGURATION_PATH, basename(yaml_path))
    dict_template = {}
    if base_default and exists(default_template_path):
        with open(default_template_path) as f:
            dict_template = yaml.load(f)
    if exists(yaml_path):
        with open(yaml_path) as f:
            override_tpl = yaml.load(f)
            if override_tpl:
                dict_template = dict_merge(dict_template or {}, override_tpl)
    return dict_template or {}


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
        if any(path in src_dir for path in EXCLUDE_PATHS):
            continue

        for dirname in dirs:
            if source in dirname:
                dirpath = join(src_dir, dirname)
                movedircontent(dirpath, dirpath.replace(
                    source, to_python_module(replace)))

    for src_dir, dirs, files in os.walk(root_src_dir):
        for file_ in files:
            if not any(file_.endswith(ext) for ext in REPLACE_TEXT_FILES_EXTENSIONS):
                continue

            src_file = join(src_dir, file_)
            replace_in_file(src_file, source, replace)


def replace_in_file(src_file, source, replace):
    if src_file.endswith('.py') or basename(src_file) == 'Dockerfile':
        replace = to_python_module(replace)
    with fileinput.FileInput(src_file, inplace=True) as file:
        try:
            for line in file:
                print(line.replace(source, replace), end='')
        except UnicodeDecodeError:
            pass


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
        if not exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = join(src_dir, file_)
            dst_file = join(dst_dir, file_)
            if exists(dst_file):
                os.remove(dst_file)
            try:
                shutil.copy(src_file, dst_dir)
            except:
                logging.warning("Error copying file %s to %s.",
                                src_file, dst_dir)


def movedircontent(root_src_dir, root_dst_dir):
    """
    Does copy and merge (shutil.copytree requires that the destination does not exist)
    :param root_src_dir:
    :param root_dst_dir:
    :return:
    """
    logging.info('Moving directory content from %s to %s',
                 root_src_dir, root_dst_dir)
    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = join(src_dir, file_)
            dst_file = join(dst_dir, file_)

            try:
                shutil.move(src_file, join(
                    dst_dir, basename(src_file)))
            except:
                logging.warning("Error moving file %s to %s.",
                                src_file, dst_dir, exc_info=True)
    shutil.rmtree(root_src_dir)


def merge_configuration_directories(source, dest):
    if source == dest:
        return
    if not exists(source):
        logging.warning(
            "Trying to merge the not existing directory: %s", source)
        return
    if not exists(dest):
        shutil.copytree(
            source, dest, ignore=shutil.ignore_patterns(*EXCLUDE_PATHS))
        return

    for src_dir, dirs, files in os.walk(source):
        if any(path in src_dir for path in EXCLUDE_PATHS):
            continue
        dst_dir = src_dir.replace(source, dest, 1)
        if not exists(dst_dir):
            os.makedirs(dst_dir)
        for fname in files:
            if fname in BUILD_FILENAMES:
                continue
            fpath = join(src_dir, fname)
            frel = relpath(fpath, start=source)
            fdest = join(dest, frel)
            if not exists(fdest):
                shutil.copy2(fpath, fdest)
            elif file_is_yaml(fpath):

                try:
                    merge_yaml_files(fpath, fdest)
                    logging.info(
                        f"Merged/overridden file content of {fdest} with {fpath}")
                except Exception as e:
                    logging.warning(f"Overwriting file {fdest} with {fpath}")
                    shutil.copy2(fpath, fdest)
            else:
                logging.warning(f"Overwriting file {fdest} with {fpath}")
                shutil.copy2(fpath, fdest)


def merge_yaml_files(fname, fdest):
    with open(fname) as f:
        content_src = yaml.load(f)
    merge_to_yaml_file(content_src, fdest)


def merge_to_yaml_file(content_src, fdest):
    if not content_src:
        return
    if not exists(fdest):
        merged = content_src
    else:
        with open(fdest) as f:
            content_dest = yaml.load(f)

        merged = dict_merge(
            content_dest, content_src) if content_dest else content_src

    if not exists(dirname(fdest)):
        os.makedirs(dirname(fdest))
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
    if merge_dct is None:
        return dct

    if not add_keys:
        merge_dct = {
            k: merge_dct[k]
            for k in set(dct).intersection(set(merge_dct))
        }

    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.abc.Mapping)):
            dct[k] = dict_merge(dct[k], merge_dct[k], add_keys=add_keys)
        else:
            dct[k] = merge_dct[k]

    return dct


def merge_app_directories(root_paths, destination) -> None:
    """ Merge directories if they refer to the same application

    Directories are merged in the destination from the root_paths list. The latter overrides the former.
    Yaml files are merged, other files are overwritten.
    """
    if not exists(destination):
        os.makedirs(destination)
    else:
        shutil.rmtree(destination)

    for rpath in root_paths:
        merge_configuration_directories(join(rpath, BASE_IMAGES_PATH),
                                        join(destination, BASE_IMAGES_PATH))
        merge_configuration_directories(join(rpath, STATIC_IMAGES_PATH),
                                        join(destination, STATIC_IMAGES_PATH))
        merge_configuration_directories(join(rpath, APPS_PATH),
                                        join(destination, APPS_PATH))
        merge_configuration_directories(join(rpath, 'libraries'),
                                        join(destination, 'libraries'))
        merge_configuration_directories(join(rpath, 'client'),
                                        join(destination, 'client'))
        merge_configuration_directories(join(rpath, 'deployment-configuration'),
                                        join(destination, 'deployment-configuration'))


def to_python_module(name):
    return name.replace('-', '_')


def guess_build_dependencies_from_dockerfile(filename):
    dependencies = []
    if not "Dockerfile" in filename:
        filename = join(filename, "Dockerfile")
    with open(filename) as f:
        for line in f:
            if line.startswith("ARG") and not "=" in line:
                dependencies.append(line.split()[1].lower().replace("_", "-"))
            else:
                break
    return dependencies



