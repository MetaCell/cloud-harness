
import contextlib
import pathlib
import socket
import glob
import subprocess
from dataclasses import dataclass
from typing import Any, Union
import requests
import os
from functools import cache
from os.path import join, dirname, isdir, basename, exists, relpath, sep, dirname as dn
import json
import collections
import re
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
import shutil
import logging
import fileinput
import pathspec
from pathlib import Path

from cloudharness_utils.constants import NEUTRAL_PATHS, DEPLOYMENT_CONFIGURATION_PATH, BASE_IMAGES_PATH, STATIC_IMAGES_PATH, \
    APPS_PATH, EXCLUDE_PATHS, VALUES_OVERRIDES_PATH
from . import CH_ROOT

yaml = YAML(typ='safe')
BASE_TEMPLATES_PATH = CH_ROOT


REPLACE_TEXT_FILES_EXTENSIONS = (
    '.js', '.md', '.py', '.js', '.ts', '.tsx', '.txt', 'Dockerfile', 'yaml', 'json', '.ejs'
)

SKIP_DIRS = ('node_modules',)


def image_name_from_dockerfile_path(dockerfile_path, base_name=None) -> str:
    return get_image_name(app_name_from_path(dockerfile_path), base_name)


def app_name_from_path(dockerfile_path):
    return "-".join(p for p in dockerfile_path.split("/") if p not in NEUTRAL_PATHS)


def clean_path(path):
    return "/".join(p for p in path.split("/") if p not in NEUTRAL_PATHS)


def get_app_relative_to_base_path(base_path, dockerfile_path):
    return clean_path(relpath(dockerfile_path, base_path))


def get_sub_paths(base_path):
    return tuple(path for path in glob.glob(base_path + "/*") if isdir(path))


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


def get_cluster_ip(local=False):
    if local:
        # Try to get LoadBalancer IP from ingress-nginx first (preferred for local dev with minikube tunnel)
        try:
            out = subprocess.check_output([
                'kubectl', '-n', 'ingress-nginx', 'get', 'svc', 'ingress-nginx-controller',
                '-o', 'jsonpath={.status.loadBalancer.ingress[0].ip}'
            ], timeout=5).decode("utf-8").strip()
            if out and out != '<no value>':
                return out
        except:
            pass
        # Try minikube with profile detection for local development
        try:
            # Get current kubectl context to extract minikube profile
            context = subprocess.check_output(['kubectl', 'config', 'current-context'], timeout=5).decode("utf-8").strip()

            # Try with profile if context looks like minikube
            if 'minikube' in context.lower():
                profile = context  # Context name is often the profile name
                try:
                    out = subprocess.check_output(['minikube', '-p', profile, 'ip'], timeout=5).decode("utf-8").strip()
                    if out:
                        return out
                except:
                    pass

            # Try without profile (default minikube)
            out = subprocess.check_output(['minikube', 'ip'], timeout=5).decode("utf-8").strip()
            if out:
                return out
        except:
            pass

        # Try kubectl cluster-info
        try:
            out = subprocess.check_output(
                ['kubectl', 'cluster-info'], timeout=10).decode("utf-8")
            ips = re.findall(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", out)
            if ips:
                return ips[0]
        except:
            pass

    # Fallback to host address (used for non-local deployments)
    return get_host_address()


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

            src_file = pathlib.Path(src_dir) / file_
            replace_in_file(src_file, source, replace)


def confirm(question):
    answer = input(f"{question} (Y/n): ").casefold()
    return answer == "y" if answer else True


def replace_in_file(src_file: pathlib.Path, source: str, replacement) -> None:
    if src_file.name.endswith('.py') or src_file.name == 'Dockerfile':
        replacement = to_python_module(str(replacement))

    with fileinput.input(src_file, inplace=True) as file:
        try:
            for line in file:
                print(line.replace(source, str(replacement)), end='')
        except UnicodeDecodeError:
            pass


def replace_in_dict(src_dict: dict, source: str, replacement: str) -> dict:
    def replace_value(value: Any) -> Any:
        if isinstance(value, str):
            return value.replace(source, replacement)
        if isinstance(value, list):
            return [replace_value(item) for item in value]
        if isinstance(value, dict):
            return replace_in_dict(value, source, replacement)
        return value

    return {
        key: replace_value(value)
        for key, value in src_dict.items()
    }


def copymergedir(source_root_directory: pathlib.Path, destination_root_directory: pathlib.Path) -> None:
    """
    Does copy and merge (shutil.copytree requires that the destination does not exist)
    :param source_root_directory:
    :param destination_root_directory:
    :return:
    """
    logging.info(f'Copying directory {source_root_directory} to {destination_root_directory}')

    for source_directory, dirs, files in os.walk(source_root_directory):  # source_root_directory.walk() from Python 3.12
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        source_directory = pathlib.Path(source_directory)
        destination_directory = destination_root_directory / source_directory.relative_to(source_root_directory)
        destination_directory.mkdir(parents=True, exist_ok=True)

        for file in files:
            source_file = source_directory / file
            destination_file = destination_directory / file

            try:
                source_file.replace(destination_file)
            except:
                logging.warning(f'Error copying file {source_file} to {destination_file}.')


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


def merge_configuration_directories(source: Union[str, pathlib.Path], destination: Union[str, pathlib.Path], envs=(), exclude=EXCLUDE_PATHS) -> None:
    source_path, destination_path = pathlib.Path(source), pathlib.Path(destination)

    if source_path == destination_path and not envs:
        return

    if not source_path.exists():
        logging.warning("Trying to merge the not existing directory: %s", source)
        return

    merge_roots = ('deploy', 'deployment')
    spec = pathspec.PathSpec.from_lines('gitwildmatch', exclude)
    copy_single_files = False

    if not destination_path.exists():
        logging.info("Creating merged directory %s from %s", destination, source)
        merge_roots_set = set(merge_roots)

        def _ignore(directory, contents):
            rel_dir = pathlib.Path(directory).relative_to(source_path)
            ignored = []
            for c in contents:
                if str(rel_dir) == '.' and c in merge_roots_set:
                    ignored.append(c)
                elif spec.match_file(str(rel_dir / c)) or spec.match_file(str(rel_dir / c) + '/'):
                    ignored.append(c)
            return ignored
        shutil.copytree(source_path, destination_path, ignore=_ignore)
    else:
        copy_single_files = True

    for source_directory, dirs, files in os.walk(source_path):  # source_path.walk() from Python 3.12
        _merge_configuration_directory(
            source_path, destination_path, pathlib.Path(source_directory),
            files, envs, spec, copy_single_files=copy_single_files
        )


def _merge_configuration_directory(
        source: pathlib.Path,
        destination: pathlib.Path,
        source_directory: pathlib.Path,
        files: list[str],
        envs=(),
        spec: pathspec.PathSpec = None,
        copy_single_files: bool = False
) -> None:
    rel_path = source_directory.relative_to(source)
    if spec is not None and str(rel_path) != '.' and (
        spec.match_file(str(rel_path)) or spec.match_file(str(rel_path) + '/')
    ):
        return

    destination_directory = destination / source_directory.relative_to(source)
    merge_roots = {'deploy', 'deployment'}
    if source != destination and not copy_single_files and not any(destination_directory.is_relative_to(destination / m) for m in merge_roots):
        return
    destination_directory.mkdir(exist_ok=True)

    for file_name in files:
        source_file_path = source_directory / file_name
        destination_file_path = destination_directory / file_name

        _merge_configuration_file(source_file_path, destination_file_path, envs, copy_single_files=copy_single_files)


def merge_yaml_files(fname, fdest):
    with open(fname) as f:
        content_src = yaml.load(f)
    merge_to_yaml_file(content_src, fdest)


def merge_json_files(fname, fdest):
    with open(fname) as f:
        content_src = json.load(f)
    merge_to_json_file(content_src, fdest)


def merge_to_json_file(content_src, fdest):
    if not content_src:
        return
    if not exists(fdest):
        merged = content_src
    else:
        with open(fdest) as f:
            content_dest = json.load(f)

        merged = dict_merge(
            content_dest, content_src) if content_dest else content_src

    if not exists(dirname(fdest)):
        os.makedirs(dirname(fdest))
    with open(fdest, "w") as f:
        json.dump(merged, f, indent=2)
    return merged


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


merge_operations = {
    ".yaml": merge_yaml_files,
    ".yml": merge_yaml_files,
    ".json": merge_json_files,
}


def _merge_configuration_file(source_file_path: pathlib.Path, destination_file_path: pathlib.Path, envs=(), copy_single_files: bool = False) -> None:
    if not exists(destination_file_path):
        shutil.copy2(source_file_path, destination_file_path)
    ext = source_file_path.suffix.lower()
    merge_files = merge_operations.get(ext, None)

    if source_file_path != destination_file_path:
        if merge_files is not None:
            try:
                merge_files(source_file_path, destination_file_path)
                logging.info(f'Merged/overridden file content of {destination_file_path} with {source_file_path}')
            except:
                logging.warning(f'Merge error: overwriting file {destination_file_path} with {source_file_path}')
                shutil.copy2(source_file_path, destination_file_path)
        elif copy_single_files:
            logging.warning(f'Overwriting file {destination_file_path} with {source_file_path}')
            shutil.copy2(source_file_path, destination_file_path)

    if merge_files is not None:
        # override eventually with environment specific files
        for e in envs:
            env_specific_file = pathlib.Path(str(source_file_path).replace(f'{ext}', f'-{e}{ext}'))
            if exists(env_specific_file):
                try:
                    merge_files(env_specific_file, destination_file_path)
                    logging.info(f'Merged/overridden file content of {destination_file_path} with {env_specific_file}')
                except:
                    pass


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
        if (k in dct and isinstance(dct[k], dict) and
                isinstance(merge_dct[k], collections.abc.Mapping)):
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


def read_dockerignore(base_path: Union[str, pathlib.Path]) -> tuple:
    dockerignore = pathlib.Path(base_path) / '.dockerignore'
    if not dockerignore.exists():
        return None
    with dockerignore.open() as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return tuple(lines) if lines else ()


def to_python_module(name):
    return name.replace('-', '_')


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


@dataclass(frozen=True)
class ChartImageRef:
    """A runtime (non-built) image reference discovered inside a values dict.

    `path` locates the node inside the scanned dict; `value` is what a values file must
    hold there to select the image: the flat string, or a dict of only the identifying
    fields (registry/repository/name/tag), with an empty tag resolved to the chart appVersion.
    """
    path: tuple
    value: Union[str, dict]


def nested_get(doc: dict, path: tuple):
    for segment in path:
        if not isinstance(doc, dict) or segment not in doc:
            return None
        doc = doc[segment]
    return doc


def nested_set(doc: dict, path: tuple, value) -> dict:
    node = doc
    for segment in path[:-1]:
        node = node.setdefault(segment, {})
    node[path[-1]] = value
    return doc


def find_chart_images(node: dict, *, skip_paths: frozenset = frozenset(),
                      app_version: Union[str, None] = None,
                      _path: tuple = ()) -> list:
    """Heuristically finds references to images that CloudHarness does not build itself.

    Matches only an exact key named "image" - never by substring, which would also catch
    imagePullSecrets/pullPolicy - holding one of these shapes:
      - a flat string:                      image: "docker.io/x/y:1"
        (a sibling `imageTag` key, as in the elasticsearch chart, is reported as well)
      - a {repository, registry?, tag?} dict (registry is optional)
      - a {name, tag?} dict

    A dict under "image" matching neither shape (e.g. {pullPolicy, pullSecrets}) is not
    recorded and not recursed into - its sub-keys are never image references.

    `skip_paths` holds paths (as tuples, relative to the scanned dict) that are neither
    recorded nor recursed into. Callers use it to prune the images CloudHarness builds
    itself, which are not overridable image sources: an application's own `image` and
    `harness.deployment.image`, and the `apps` subtree when it is scanned separately.

    `app_version` resolves an empty/missing "tag": vendored charts ship tag: "" and rely on
    Helm's `tag | default .Chart.AppVersion`, so pass the sub-chart appVersion for the
    reported value to state what is actually deployed.
    """
    found = []
    for key, value in node.items():
        path = _path + (key,)
        if path in skip_paths:
            continue
        if key == 'image':
            if isinstance(value, str) and value:
                found.append(ChartImageRef(path=path, value=value))
                if 'imageTag' in node:
                    found.append(ChartImageRef(path=_path + ('imageTag',), value=node['imageTag']))
            elif isinstance(value, dict):
                identity = {k: value[k] for k in ('registry', 'repository', 'name') if k in value}
                if 'repository' in identity or 'name' in identity:
                    tag = value.get('tag') or app_version
                    if tag:
                        identity['tag'] = tag
                    found.append(ChartImageRef(path=path, value=identity))
            continue
        if isinstance(value, dict):
            found.extend(find_chart_images(value, skip_paths=skip_paths,
                                           app_version=app_version, _path=path))
    return found


def write_values_overrides(helm_values: dict, dest_deployment_path: pathlib.Path) -> None:
    """Writes values-overrides.yaml next to values.yaml: every image the chart pulls but does
    not build, in the structure Helm consumes. It is a reference for looking a path up and
    trying an image out by passing the file to helm explicitly; no pipeline applies it, since it
    is regenerated on every run and would only restate the values already in effect.

    - source_images: the Dockerfile base images (build arguments) aggregated at the root
    - <sub-chart name>: the images of each vendored sub-chart copied under charts/<app>, keyed
      by the sub-chart's own Chart.yaml name - the key Helm uses to pass parent values down.
      Empty tags are resolved from the sub-chart appVersion so the file states what is deployed.
    - apps.<app>: the images an application pulls, both the ones declared inline in its own
      values (e.g. jupyterhub) and the ones under its harness configuration (database,
      gatekeeper, extra containers)
    - the remaining root paths: images the generated resources themselves run, such as the
      database backup and the volume migration containers

    The images CloudHarness builds are left out, not being an overridable image source: an
    application's own `image` and `harness.deployment.image` are pruned, unless the application
    declares a prebuilt image instead of being built (`build: false`).

    Values already set at those paths (e.g. from values-template-<env>.yaml) win over the
    vendored defaults, so the file always reflects the effective configuration.
    """
    apps_key, harness_key, database_key, deployment_key = 'apps', 'harness', 'database', 'deployment'

    overrides = {}
    key_comments = {}
    if helm_values.get("source_images"):
        overrides["source_images"] = dict(helm_values["source_images"])
        key_comments["source_images"] = (
            "Dockerfile base images, injected as build arguments.\n"
            "Origin: the ARG defaults declared in each application's own Dockerfile (and\n"
            "CloudHarness's base/static image Dockerfiles), aggregated here at build time."
        )

    # proxy.gatekeeper.image used to override the gatekeeper image for every application.
    # The gatekeeper is now configured at source_images.GATEKEEPER, so no template reads it:
    # reporting it would advertise a path that overrides nothing.
    legacy_gatekeeper_path = ('proxy', 'gatekeeper', 'image')
    if nested_get(helm_values, legacy_gatekeeper_path):
        logging.warning(
            "proxy.gatekeeper.image is set but no longer used: set source_images.GATEKEEPER "
            "to change the gatekeeper image for every application, or "
            "apps.<app>.harness.proxy.gatekeeper.image for a single one")

    # Images the generated resources run, declared at the root of the chart values
    for ref in find_chart_images(helm_values, skip_paths=frozenset({(apps_key,), legacy_gatekeeper_path})):
        nested_set(overrides, ref.path, ref.value)
        key_comments.setdefault(ref.path[0], (
            "Image run by a resource generated by the chart itself.\n"
            "Origin: CloudHarness's own chart defaults, deployment-configuration/helm/values.yaml."
        ))

    for app_name, app_values in helm_values[apps_key].items():
        skip_paths = set()
        # A built application owns its image; everything else it merely pulls
        if app_values.get('build', False):
            skip_paths |= {('image',), (harness_key, deployment_key, 'image')}
        # An application declaring database.image_ref runs the task image built under that
        # reference, which shadows the database type's own image: that one is then not the
        # value to override, so it is not reported as one
        harness_values = app_values.get(harness_key) or {}
        if (harness_values.get(database_key) or {}).get('image_ref'):
            skip_paths.add((harness_key, database_key))
        for ref in find_chart_images(app_values, skip_paths=frozenset(skip_paths)):
            nested_set(overrides, (apps_key, app_name) + ref.path, ref.value)
            key_comments.setdefault(apps_key, (
                "Images declared inline by an application, or pulled through its harness\n"
                "configuration (database, gatekeeper, extra containers).\n"
                "Origin: declared inline in the application's own deploy/values.yaml, or\n"
                "inherited from the harness-wide defaults in deployment-configuration/value-template.yaml\n"
                "(singular)."
            ))

        chart_dir = dest_deployment_path / 'charts' / app_name
        chart_values_path = chart_dir / 'values.yaml'
        if not chart_values_path.exists():
            continue
        chart_meta_path = chart_dir / 'Chart.yaml'
        chart_meta = (load_yaml(chart_meta_path) if chart_meta_path.exists() else None) or {}
        chart_name = chart_meta.get('name') or app_name
        for ref in find_chart_images(load_yaml(chart_values_path) or {}, app_version=chart_meta.get('appVersion')):
            value = ref.value
            existing = nested_get(helm_values, (chart_name,) + ref.path)
            if existing is not None:
                value = dict_merge(value, existing) if isinstance(value, dict) and isinstance(existing, dict) else existing
            nested_set(overrides, (chart_name,) + ref.path, value)
            key_comments.setdefault(chart_name, (
                f"Images of the vendored '{chart_name}' sub-chart (from the {app_name} application),\n"
                "keyed by its own Chart.yaml name - the key Helm uses to pass parent values down.\n"
                f"Origin: the sub-chart's own default values, vendored (checked in as-is from the\n"
                f"upstream chart) at applications/{app_name}/deploy/charts/values.yaml."
            ))

    header = (
        "This file is a reference, auto-generated by `harness-deployment` and overwritten on\n"
        "every run. No pipeline applies it: it lists every image the chart pulls but does not\n"
        "build, at the exact path Helm reads it from, so you can look a path up here or try an\n"
        "image out with `helm ... -f <this file>`. The comment on each key below states where\n"
        "that value originates. To make a change permanent instead, redefine the same path in\n"
        "your own deployment configuration - which file depends on where the image sits, as\n"
        "explained in docs/image-sources.md (e.g. a per-environment\n"
        "deployment-configuration/values-template-<env>.yaml for most root-level keys, but each\n"
        "application's own deploy/values.yaml for anything under apps.<app>)."
    )
    save_yaml_with_comments(dest_deployment_path / VALUES_OVERRIDES_PATH, overrides,
                            header=header, key_comments=key_comments)


def check_response_200(endpoint_url, headers=None):
    resp = requests.get(endpoint_url, headers=headers, timeout=5)
    return resp.status_code == 200


def check_docker_manifest_exists(registry, image_name, tag):
    api_url = f"https://{registry}/v2/{image_name}/manifests/{tag}"
    return check_response_200(api_url, headers={"Accept": "application/vnd.oci.image.manifest.v1+json"})


def check_image_exists_in_registry(registry, image_name, tag, endpoint_url=None):
    """
    Check if an image exists in the registry.
    :param registry: The registry URL (e.g., 'registry.example.com').
    :param image_name: The name of the image (e.g., 'myapp').
    :param tag: The tag of the image (e.g., 'latest').
    :return: True if the image exists, False otherwise.
    """

    if endpoint_url:
        try:
            return check_response_200(f"{endpoint_url}?repository={registry}/{image_name}&tag={tag}")
        except requests.RequestException as e:
            logging.error(f"Error checking image existence at {endpoint_url}: {e}.\nUsing default registry manifest check.")
    return check_docker_manifest_exists(registry, image_name, tag)


def filter_empty_strings(value):
    return value != ""


def search_word_in_file(filename, word):
    if os.path.isdir(filename):
        return []
    matches = []
    with open(filename) as f:
        try:
            if word in f.read():
                matches.append(filename)
        except UnicodeDecodeError:
            # Ignore files that cannot be decoded
            logging.warning(f"Could not read file {filename} due to encoding issues.")
            return []
    return list(filter(filter_empty_strings, matches))


def search_word_in_folder(folder, word):
    matches = []
    files = glob.glob(folder + '/**/*', recursive=True)
    for file in files:
        matches.extend(search_word_in_file(file, word))
    return list(filter(filter_empty_strings, matches))


def search_word_by_pattern(folder, pattern, word):
    if not folder.endswith('/'):
        folder += '/'
    matches = []
    files = glob.glob(folder + pattern, recursive=True)
    for file in files:
        matches.extend(search_word_in_file(file, word))
    return list(filter(filter_empty_strings, matches))


def get_git_commit_hash(path):
    # return the short git commit hash in that path
    # if the path is not a git repo, return None

    try:
        return subprocess.check_output(
            ['git', 'rev-parse', '--short', 'HEAD'], cwd=path).decode("utf-8").strip()
    except:
        return None


def load_yaml(yaml_file: pathlib.Path) -> dict:
    with yaml_file.open('r') as file:
        return yaml.load(file)


def save_yaml(yaml_file: pathlib.Path, data: dict) -> None:
    with yaml_file.open('w') as file:
        yaml.dump(data, file)


def _sorted_deep(value):
    if isinstance(value, dict):
        return {key: _sorted_deep(value[key]) for key in sorted(value)}
    if isinstance(value, list):
        return [_sorted_deep(item) for item in value]
    return value


def save_yaml_with_comments(yaml_file: pathlib.Path, data: dict, header: str = None,
                            key_comments: dict[str, str] = None) -> None:
    """Writes data as YAML (keys sorted at every level, like `save_yaml`), with a comment block
    before the document and, optionally, a comment before each named top-level key."""
    commented = CommentedMap(_sorted_deep(data))
    if header:
        commented.yaml_set_start_comment(header)
    for key, comment in (key_comments or {}).items():
        if key in commented:
            # Leading blank line separates each key's comment from the previous entry
            commented.yaml_set_comment_before_after_key(key, before='\n' + comment)
    handler = YAML()
    handler.default_flow_style = False
    with yaml_file.open('w') as file:
        handler.dump(commented, file)


def get_apps_paths(root, app_name) -> tuple[str]:
    apps_path = []

    if app_name:
        logging.info('### Generating server stubs for %s ###', app_name)
        apps_path = [path for path in root.glob(f'applications/{app_name}') if path.is_dir()]
    else:
        logging.info('### Generating server stubs for all applications ###')
        apps_path = [path for path in root.glob('applications/*') if path.is_dir()]
    return apps_path


def clean_image_name(image_name: str) -> str:
    """
    Cleans the image name by removing all unallowed characters and converting it to lowercase.
    """
    return re.sub(r'[^a-zA-Z0-9-]', '', image_name.lower()).strip('-')  # Remove unallowed characters and trim
