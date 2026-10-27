import pathlib
import glob
import os
import shutil
from typing import Union
from functools import cache
from os.path import join, dirname, isdir, basename, exists, relpath, sep
import re
from pathlib import Path
from ruamel.yaml import YAML

from cloudharness_utils.constants import NEUTRAL_PATHS, DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, \
    STATIC_IMAGES_PATH, APPS_PATH

from ..utils import BASE_TEMPLATES_PATH, dict_merge, merge_configuration_directories, yaml

# Round trip handler, for the cases where the key order of the source document
# (or of the dumped dictionary) must be preserved: the safe representer in the
# shared ch_cli_tools.utils sorts mapping keys alphabetically.
yaml_rt = YAML()
yaml_rt.default_flow_style = False


def image_name_from_dockerfile_path(dockerfile_path, base_name=None) -> str:
    return get_image_name(app_name_from_path(dockerfile_path), base_name)


def app_name_from_path(dockerfile_path):
    return "-".join(p for p in dockerfile_path.split("/") if p not in NEUTRAL_PATHS)


def clean_path(path):
    return "/".join(p for p in path.split("/") if p not in NEUTRAL_PATHS)


def get_app_relative_to_base_path(base_path, dockerfile_path):
    return clean_path(relpath(dockerfile_path, base_path))


def find_file_paths(base_directory, file_name):
    return tuple(dirname(path).replace(sep, "/") for path in
                 glob.glob(f"{base_directory}/**/{file_name}", recursive=True))


def find_subdirs(base_path):
    if exists(base_path):
        return (join(base_path, d) for d in os.listdir(base_path) if isdir(join(base_path, d)))
    return tuple()


def find_dockerfiles_paths(base_directory: str) -> tuple[str, ...]:
    all_dockerfiles = find_file_paths(base_directory, 'Dockerfile')

    # We want to remove all dockerfiles that are not in a git repository
    # This will exclude the cloned dependencies and other repos cloned for convenience
    dockerfiles_without_git: list[str] = []

    for dockerfile in all_dockerfiles:
        directory = dockerfile
        while not os.path.samefile(directory, base_directory):
            if os.path.exists(os.path.join(directory, '.git')):
                break
            directory = os.path.dirname(directory)
        else:
            dockerfiles_without_git.append(dockerfile.replace(os.sep, "/"))

    return tuple(p for p in dockerfiles_without_git if not re.search(r'(^|/).*dependencies.*/', p + '/'))


# Directory names that hold Dockerfiles belonging to something other than the application's own
# buildable image: task images, deprecated subapps, and instance overrides.
NON_BUILDABLE_DOCKERFILE_SEGMENTS = frozenset({'tasks', 'subapps', 'instances'})


def is_buildable_dockerfile_path(path: str) -> bool:
    """Whether a Dockerfile path belongs to the application's own buildable image, i.e. is not
    nested under a `tasks`, `subapps` or `instances` directory.

    Matches by path segment rather than substring, so an application or resource directory whose
    name merely contains one of these words (e.g. `myinstances`) is not excluded by mistake.
    """
    return not (set(Path(path).parts) & NON_BUILDABLE_DOCKERFILE_SEGMENTS)


def get_parent_app_name(app_relative_path):
    return app_relative_path.split("/")[0] if "/" in app_relative_path else ""


def strip_registry_tag(full_image_name, registry_url=""):
    if not full_image_name:
        return None
    return full_image_name.replace(registry_url, "").split(":")[0]


def get_image_name(app_name, base_name=None):
    if not app_name:
        return None
    return (base_name + '/' + app_name) if base_name else app_name


def env_variable(name, value):
    return {'name': f"{name}".upper(), 'value': str(value)}


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


def read_dockerignore(base_path: Union[str, pathlib.Path]) -> tuple:
    dockerignore = pathlib.Path(base_path) / '.dockerignore'
    if not dockerignore.exists():
        return None
    with dockerignore.open() as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return tuple(lines) if lines else ()


@cache
def guess_build_dependencies_from_dockerfile(filename):
    dependencies = []
    if "Dockerfile" not in str(filename):
        filename = join(filename, "Dockerfile")
    if not os.path.exists(filename):
        return dependencies
    with open(filename) as f:
        for line in f:
            if line.startswith("ARG") and not "=" in line:
                dependencies.append(line.split()[1].lower().replace("_", "-"))
            else:
                break
    return dependencies


@cache
def get_dockerfile_baseimg_args(filename: str) -> dict[str, str]:
    """Gets the ARGS from a Dockerfile image (if ARGS is used directly in the FROM of the Dockerfile)"""
    file = Path(filename)
    if file.is_dir() and file.name != "Dockerfile":
        file /= "Dockerfile"
    if not file.exists():
        return {}
    content = file.read_text()
    found_args = {}
    args: dict[str, str] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        cmd, *rest = line.split()
        arg = rest[0] if len(rest) > 0 else ""
        match cmd:
            case "ARG" if "=" in rest[0]:
                key, val = arg.split("=")
                found_args[key] = val
            case "FROM" if arg[1:] in found_args:  # $NAME case
                key = arg[1:]
                args[key] = found_args[key]
            case "FROM" if arg[2:-1] in found_args:  # ${NAME} case
                key = arg[2:-1]
                args[key] = found_args[key]
            case _:
                continue
    return args


def get_image_source(helm_values) -> dict[str, str]:
    return helm_values.get("source_images", {})


def clean_image_name(image_name: str) -> str:
    """
    Cleans the image name by removing all unallowed characters and converting it to lowercase.
    """
    return re.sub(r'[^a-zA-Z0-9-]', '', image_name.lower()).strip('-')  # Remove unallowed characters and trim
