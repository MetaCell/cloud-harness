import glob
import subprocess
import os
import collections
import oyaml as yaml
import shutil
import logging



from .constants import HERE, NEUTRAL_PATHS, DEPLOYMENT_CONFIGURATION_PATH


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
