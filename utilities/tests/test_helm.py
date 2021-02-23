import shutil
import yaml

from cloudharness_utilities.helm import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = './deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(HERE))

def test_collect_helm_values():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, include=['samples', 'myapp'], exclude=['events'], domain="my.local",
                               namespace='test', env='dev', local=False)

    # First level include apps
    assert 'samples' in values[KEY_APPS]
    assert 'myapp' in values[KEY_APPS]

    # Not included
    assert 'jupyterhub' not in values[KEY_APPS]

    # Dependency include first level
    assert 'workflows' in values[KEY_APPS]
    assert 'accounts' in values[KEY_APPS]

    # Dependency include second level
    assert 'argo' in values[KEY_APPS]

    # Explicit exclude overrides include
    assert 'events' not in values[KEY_APPS]


    # Values overriding
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['subdomain'] == 'overridden'

    # Environment specific overriding
    assert values[KEY_APPS]['accounts']['a'] == 'dev'
    assert values['a'] == 'dev'
    assert values['database']['auto'] == False

    # legacy reading
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['auto'] == 'overridden'

    helm_path = os.path.join(OUT, HELM_CHART_PATH)

    def exists(*args):
        return os.path.exists(os.path.join(*args))
    # Check files
    assert exists(helm_path)
    assert exists(helm_path, 'values.yaml')
    assert exists(helm_path, 'resources/accounts/realm.json')
    assert exists(helm_path, 'resources/accounts/aresource.txt')
    assert exists(helm_path, 'resources/myapp/aresource.txt')
    assert exists(helm_path, 'templates/myapp/mytemplate.yaml')

    shutil.rmtree(OUT)

