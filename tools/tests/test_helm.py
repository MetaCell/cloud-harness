import shutil

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
    assert values.apps['myapp'].harness.deployment.image == 'reg/cloudharness/myapp:1'
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
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['auto'] == True
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['deployment']['auto'] == False

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

    # Checl base and task images 
    assert values[KEY_TASK_IMAGES]
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES]
    assert values[KEY_TASK_IMAGES]['cloudharness-base'] == 'reg/cloudharness/cloudharness-base:1'
    assert values[KEY_TASK_IMAGES]['myapp-mytask'] == 'reg/cloudharness/myapp-mytask:1'
    # Not indicated as a build dependency
    assert 'cloudharness-base-debian' not in values[KEY_TASK_IMAGES]

    shutil.rmtree(OUT)


def test_collect_helm_values_noreg_noinclude():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, domain="my.local",
                               namespace='test', env='dev', local=False, tag=1)

    # Auto values
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'cloudharness/myapp:1'
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['name'] == 'myapp'
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['name'] == 'legacy'
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['image'] == 'cloudharness/accounts:1'

    # First level include apps
    assert 'samples' in values[KEY_APPS]
    assert 'myapp' in values[KEY_APPS]
    assert 'jupyterhub' in values[KEY_APPS]
    assert 'accounts' in values[KEY_APPS]
    assert 'legacy' in values[KEY_APPS]
    assert 'argo' in values[KEY_APPS]
    assert 'events' in values[KEY_APPS]

    # Base values kept
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['subdomain'] == 'accounts'

    # Defaults
    assert 'service' in values[KEY_APPS]['legacy'][KEY_HARNESS]
    assert 'common' in values[KEY_APPS]['legacy']
    assert 'common' in values[KEY_APPS]['accounts']
    # Values overriding
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['port'] == 'overridden'
    assert values[KEY_APPS]['events']['kafka']['resources']['limits']['memory'] == 'overridden'

    # Environment specific overriding
    assert values[KEY_APPS]['accounts']['a'] == 'dev'
    assert values['a'] == 'dev'
    assert values['database']['auto'] == False

    # legacy reading
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['auto'] == True
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['deployment']['auto'] == False

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
    assert values[KEY_TASK_IMAGES]['cloudharness-base'] == 'cloudharness/cloudharness-base:1'
    assert values[KEY_TASK_IMAGES]['myapp-mytask'] == 'cloudharness/myapp-mytask:1'

    shutil.rmtree(OUT)


def test_collect_helm_values_precedence():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["events"])

    # Values.yaml from current app must override values-prod.yaml from cloudharness
    assert values[KEY_APPS]['events']['kafka']['resources']['limits']['memory'] == 'overridden'
    assert values[KEY_APPS]['events']['kafka']['resources']['limits']['cpu'] == 'overridden-prod'


def test_collect_helm_values_wrong_dependencies_validate():
    try:
        values = create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=OUT, domain="my.local",
                                   namespace='test', env='prod', local=False, tag=1, include=["wrong-hard"])

    except ValuesValidationException as e:
        logging.info("Exception correctly raised %s", e.args)
        assert True
    else:
        assert False, "Should error because of wrong hard dependency"

    try:
        values = create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=OUT, domain="my.local",
                                   namespace='test', env='prod', local=False, tag=1, include=["wrong-soft"])

    except ValuesValidationException as e:
        assert False, "Should not error because of wrong soft dependency"
    else:
        assert True, "No error for wrong soft dependencies"

    try:
        values = create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=OUT, domain="my.local",
                                   namespace='test', env='prod', local=False, tag=1, include=["wrong-build"])

    except ValuesValidationException as e:
        logging.info("Exception correctly raised %s", e.args)
        assert True
    else:
        assert False, "Should error because of wrong build dependency"

    try:
        values = create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=OUT, domain="my.local",
                                   namespace='test', env='prod', local=False, tag=1, include=["wrong-services"])

    except ValuesValidationException as e:
        logging.info("Exception correctly raised %s", e.args)
        assert True
    else:
        assert False, "Should error because of wrong service dependency"


def test_collect_helm_values_build_dependencies():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["myapp"])

    assert 'cloudharness-flask' in values[KEY_TASK_IMAGES], "Cloudharness-flask is included in the build dependencies"
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES], "Cloudharness-base is included in cloudharness-flask Dockerfile and it should be guessed"
    assert 'cloudharness-base-debian' not in values[KEY_TASK_IMAGES], "Cloudharness-base-debian is not included in any dependency"
    assert 'cloudharness-frontend-build' not in values[KEY_TASK_IMAGES], "cloudharness-frontend-build is not included in any dependency"

def test_collect_helm_values_build_dependencies_nodeps():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["events"])


    assert 'cloudharness-flask' not in values[KEY_TASK_IMAGES], "Cloudharness-flask is not included in the build dependencies"
    assert 'cloudharness-base' not in values[KEY_TASK_IMAGES], "Cloudharness-base is not included in the build dependencies"
    assert 'cloudharness-base-debian' not in values[KEY_TASK_IMAGES], "Cloudharness-base-debian is not included in any dependency"
    assert 'cloudharness-frontend-build' not in values[KEY_TASK_IMAGES], "cloudharness-frontend-build is not included in any dependency"

def test_collect_helm_values_build_dependencies_exclude():
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=OUT, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["workflows"], exclude=["workflows-extract-download"])


    assert 'cloudharness-flask' in values[KEY_TASK_IMAGES], "Cloudharness-flask is included in the build dependencies"
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES], "Cloudharness-base is included in cloudharness-flask Dockerfile and it should be guessed"
    assert 'workflows-extract-download' not in values[KEY_TASK_IMAGES], "workflows-extract-download has been explicitly excluded"
