import shutil
import yaml

from cloudharness_utilities.utils import *

HERE = os.path.dirname(os.path.realpath(__file__)).replace(os.path.sep, '/')

def test_image_name_from_docker_path():
    assert app_name_from_path("a") == 'a'
    assert app_name_from_path("a/b") == 'a-b'
    assert app_name_from_path("a/src/b") == 'a-b'
    assert app_name_from_path("a/tasks/b") == 'a-b'
    assert app_name_from_path("cloudharness/a/b") == 'cloudharness-a-b'


def test_merge_configuration_directories():
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
        a = yaml.safe_load(f)
    assert a['a'] == 'a1'
    assert a['b']['ba'] == 'ba1'
    assert a['b']['bb'] == 'bb'
    assert a['b']['bc'] == 'bc'


    with open(os.path.join(res_path, "sub", "a.yaml")) as f:
        a = yaml.safe_load(f)
    assert a['a'] == 'a1'
    assert a['b']['ba'] == 'ba1'
    assert a['b']['bb'] == 'bb'
    assert a['b']['bc'] == 'bc'
    shutil.rmtree(res_path)
