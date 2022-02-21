import shutil
import cloudharness
import yaml

from cloudharness_utilities.helm import *
from cloudharness_utilities.preprocessing import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = './deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(HERE))


def test_preprocess_build_overrides():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, include=['samples', 'myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='dev', local=False, tag=1, registry='reg')


    res = preprocess_build_overrides(root_paths=[CLOUDHARNESS_ROOT, RESOURCES], helm_values=values, merge_build_path="/tmp/build")
    assert len(res) == 3
    assert "/tmp/build" in res[2]
    assert os.path.exists("/tmp/build")

    assert os.path.exists(os.path.join("/tmp/build/", BASE_IMAGES_PATH, "cloudharness-base/testfile")) 
    assert os.path.exists(os.path.join("/tmp/build/", BASE_IMAGES_PATH, "cloudharness-base/Dockerfile")) 
    assert not os.path.exists(os.path.join("/tmp/build/", BASE_IMAGES_PATH, "cloudharness-base-debian")) 
    assert not os.path.exists(os.path.join("/tmp/build/", APPS_PATH, "events")) 

    assert os.path.exists(os.path.join("/tmp/build/", APPS_PATH, "accounts/deploy/values.yaml")) 

    shutil.rmtree("/tmp/build")
