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
    