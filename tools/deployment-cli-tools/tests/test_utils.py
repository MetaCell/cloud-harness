import shutil


from ch_cli_tools.utils import *


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

        assert os.path.exists(os.path.join(res_path, "a.yaml"))
        assert os.path.exists(os.path.join(res_path, "b.yaml"))
        assert os.path.exists(os.path.join(res_path, "c.yaml"))

        assert os.path.exists(os.path.join(res_path, "sub", "a.yaml"))
        assert os.path.exists(os.path.join(res_path, "sub", "b.yaml"))
        assert os.path.exists(os.path.join(res_path, "sub", "c.yaml"))

        with open(os.path.join(res_path, "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'

        with open(os.path.join(res_path, "sub", "a.yaml")) as f:
            a = yaml.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'

        assert os.path.exists(os.path.join(res_path, "a.json"))
        assert os.path.exists(os.path.join(res_path, "b.json"))
        assert os.path.exists(os.path.join(res_path, "c.json"))

        with open(os.path.join(res_path, "a.json")) as f:
            a = json.load(f)
        assert a['a'] == 'a1'
        assert a['b']['ba'] == 'ba1'
        assert a['b']['bb'] == 'bb'
        assert a['b']['bc'] == 'bc'
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
    assert check_docker_manifest_exists("gcr.io/metacellllc", "cloudharness/cloudharness-base", "latest")
    assert not check_docker_manifest_exists("gcr.io/metacellllc", "cloudharness/cloudharness-base", "RANDOM_TAG")


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
