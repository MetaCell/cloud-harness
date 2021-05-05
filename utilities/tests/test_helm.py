import shutil
import yaml

from cloudharness_utilities.helm import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
OUT = './deployment'
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(HERE))


def test_collect_helm_values():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, include=['samples', 'myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='dev', local=False, tag=1, registry='reg')

    # Auto values
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'reg/cloudharness/myapp:1'
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['name'] == 'myapp'
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['name'] == 'legacy'
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['image'] == 'reg/cloudharness/accounts:1'

    # First level include apps
    assert 'samples' in values[KEY_APPS]
    assert 'myapp' in values[KEY_APPS]

    # Not included
    assert 'jupyterhub' not in values[KEY_APPS]

    # Dependency include first level
    assert 'accounts' in values[KEY_APPS]
    assert 'legacy' in values[KEY_APPS]

    # Dependency include second level
    assert 'argo' in values[KEY_APPS]

    # Explicit exclude overrides include
    assert 'events' not in values[KEY_APPS]

    # Base values kept
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['subdomain'] == 'accounts'

    # Defaults
    assert 'service' in values[KEY_APPS]['legacy'][KEY_HARNESS]
    assert 'common' in values[KEY_APPS]['legacy']
    assert 'common' in values[KEY_APPS]['accounts']
    # Values overriding
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['port'] == 'overridden'

    # Environment specific overriding
    assert values[KEY_APPS]['accounts']['a'] == 'dev'
    assert values['a'] == 'dev'
    assert values['database']['auto'] == False

    # legacy reading
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['auto'] == 'overridden'
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['deployment']['auto'] == 'legacy'

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

    assert values[KEY_TASK_IMAGES]
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES]
    assert values[KEY_TASK_IMAGES]['cloudharness-base'] == 'reg/cloudharness/cloudharness-base:1'
    assert values[KEY_TASK_IMAGES]['myapp-mytask'] == 'reg/cloudharness/myapp-mytask:1'

    shutil.rmtree(OUT)
