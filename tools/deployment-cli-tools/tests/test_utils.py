import shutil

import pytest


from ch_cli_tools.utils import *

from pathlib import Path


HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')


def test_image_name_from_docker_path():
    assert image_name_from_dockerfile_path("a") == 'a'
    assert image_name_from_dockerfile_path("a/b") == 'a-b'
    assert image_name_from_dockerfile_path("a/src/b") == 'a-b'
    assert image_name_from_dockerfile_path("a/tasks/b") == 'a-b'
    assert image_name_from_dockerfile_path("cloudharness/a/b") == 'cloudharness-a-b'
    assert image_name_from_dockerfile_path("cloudharness/a/b", 'reg') == 'reg/cloudharness-a-b'


def test_merge_configuration_directories():
    try:
        basedir = os.path.join(HERE, "resources")
        res_path = os.path.join(basedir, 'conf-res')
        if os.path.exists(res_path):
            shutil.rmtree(res_path)

        merge_configuration_directories(os.path.join(basedir, 'conf-source1'), res_path)
        merge_configuration_directories(os.path.join(basedir, 'conf-source2'), res_path)

        deploy = os.path.join(res_path, "deploy")
        assert os.path.exists(os.path.join(deploy, "a.yaml"))
        assert os.path.exists(os.path.join(deploy, "b.yaml"))
        assert os.path.exists(os.path.join(deploy, "c.yaml"))

        assert os.path.exists(os.path.join(deploy, "sub", "a.yaml"))
        assert os.path.exists(os.path.join(deploy, "sub", "b.yaml"))
        assert os.path.exists(os.path.join(deploy, "sub", "c.yaml"))

        with open(os.path.join(deploy, "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'

        with open(os.path.join(deploy, "sub", "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'

        assert os.path.exists(os.path.join(deploy, "a.json"))
        assert os.path.exists(os.path.join(deploy, "b.json"))
        assert os.path.exists(os.path.join(deploy, "c.json"))

        with open(os.path.join(deploy, "a.json")) as f:
            a = json.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'
    finally:
        if os.path.exists(res_path):
            shutil.rmtree(res_path)


def test_merge_configuration_directories_envs():
    try:
        basedir = os.path.join(HERE, "resources")
        res_path = os.path.join(basedir, 'conf-res-envs')
        if os.path.exists(res_path):
            shutil.rmtree(res_path)

        merge_configuration_directories(os.path.join(basedir, 'conf-source1'), res_path, ("dev",))
        #

        deploy = os.path.join(res_path, "deploy")
        assert os.path.exists(os.path.join(deploy, "a.yaml"))
        assert os.path.exists(os.path.join(deploy, "b.yaml"))

        assert os.path.exists(os.path.join(deploy, "sub", "a.yaml"))
        assert os.path.exists(os.path.join(deploy, "sub", "b.yaml"))

        with open(os.path.join(deploy, "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'dev'

        merge_configuration_directories(os.path.join(basedir, 'conf-source2'), res_path)
        assert os.path.exists(os.path.join(deploy, "c.yaml"))

        with open(os.path.join(deploy, "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'a1'
    finally:
        if os.path.exists(res_path):
            shutil.rmtree(res_path)


def test_guess_build_dependencies_from_dockerfile():
    deps = guess_build_dependencies_from_dockerfile(os.path.join(HERE, "resources/applications/myapp"))
    assert len(deps) == 1
    assert deps[0] == "cloudharness-flask"

    deps = guess_build_dependencies_from_dockerfile(os.path.join(HERE, "resources/applications/myapp/tasks/mytask"))
    assert len(deps) == 0


def test_check_docker_manifest_exists():
    assert check_docker_manifest_exists("quay.io", "keycloak/keycloak", "latest")
    assert not check_docker_manifest_exists("quay.io", "keycloak/keycloak", "RANDOM_TAG")


def test_search_word_in_file():
    assert len(search_word_in_file(os.path.join(HERE, './resources/applications/migration_app/Dockerfile'), "CLOUDHARNESS_BASE_DEBIAN")) == 1


def test_search_word_in_folder():
    assert len(search_word_in_folder(os.path.join(HERE, './resources/applications/migration_app/'), "CLOUDHARNESS_BASE_DEBIAN")) == 2


def test_find_dockerfile_paths():

    myapp_path = os.path.join(HERE, "resources/applications/myapp")
    if not os.path.exists(os.path.join(myapp_path, "dependencies/a/.git")):
        os.makedirs(os.path.join(myapp_path, "dependencies/a/.git"))

    dockerfiles = find_dockerfiles_paths(myapp_path)
    assert len(dockerfiles) == 2
    assert next(d for d in dockerfiles if d.endswith("myapp")), "Must find the Dockerfile in the root directory"
    assert next(d for d in dockerfiles if d.endswith("myapp/tasks/mytask")), "Must find the Dockerfile in the tasks directory"


class TestReplaceInDict:
    def test_does_not_replace_in_keys(_):
        src_dict = {
            'foo': 1,
            'bar': 2,
            'baz': 3,
            'foobar': 4,
        }

        new_dict = replace_in_dict(src_dict, 'foo', 'xxx')

        assert new_dict.keys() == src_dict.keys()

    def test_replaces_in_values(_):
        src_dict = {
            'a': 'foo',
            'b': 'bar',
            'c': 'baz',
            'd': 3,
            'e': 'foobar',
        }

        new_dict = replace_in_dict(src_dict, 'foo', 'xxx')

        assert new_dict == {
            'a': 'xxx',
            'b': 'bar',
            'c': 'baz',
            'd': 3,
            'e': 'xxxbar',
        }

    def test_replaces_in_values_within_lists(_):
        src_dict = {
            'a': ['foo', 'bar', 'baz', 3, 'foobar'],
        }

        new_dict = replace_in_dict(src_dict, 'foo', 'xxx')

        assert new_dict['a'] == ['xxx', 'bar', 'baz', 3, 'xxxbar']

    def test_replaces_in_values_within_nested_dict(_):
        src_dict = {
            'a': {
                'a': 'foo',
                'b': 'bar',
                'c': 'foobar',
                'e': ['foo', 'bar', 'foobar'],
            },
        }

        new_dict = replace_in_dict(src_dict, 'foo', 'xxx')

        assert new_dict['a'] == {
            'a': 'xxx',
            'b': 'bar',
            'c': 'xxxbar',
            'e': ['xxx', 'bar', 'xxxbar']
        }


def test__get_dockerfile_baseimg_args__no_file():
    resources = Path(HERE) / "resources"

    # no file
    args = get_dockerfile_baseimg_args(resources / "doesnotexist" / "Dockerfile")
    assert args == {}

    # no file from folder
    args = get_dockerfile_baseimg_args(resources / "doesnotexist")
    assert args == {}


def test__get_dockerfile_baseimg_args__no_dep():
    resources = Path(HERE) / "resources"

    # no real base dependance
    nodep_dockerfile = resources / "applications" / "dependantapp" / "Dockerfile"

    args = get_dockerfile_baseimg_args(nodep_dockerfile)
    assert args == {}

    # no real base dependance from folder
    nodep_dockerfile = resources / "applications" / "dependantapp"

    args = get_dockerfile_baseimg_args(nodep_dockerfile)
    assert args == {}


def test__get_dockerfile_baseimg_args__with_deps():
    resources = Path(HERE) / "resources"

    # with deps
    dockerfile = resources / "applications" / "newapp1" / "Dockerfile"

    args = get_dockerfile_baseimg_args(dockerfile)
    assert "mybase" in args
    assert args["mybase"] == "foo:bar"
    assert "mybase2" in args
    assert args["mybase2"] == "spam:egg"
    assert "mybase3" not in args

    # with deps from folder
    dockerfile = resources / "applications" / "newapp1"

    args = get_dockerfile_baseimg_args(dockerfile)
    assert "mybase" in args
    assert args["mybase"] == "foo:bar"
    assert "mybase2" in args
    assert args["mybase2"] == "spam:egg"
    assert "mybase3" not in args
