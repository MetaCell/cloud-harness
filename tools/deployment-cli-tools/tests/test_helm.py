from ch_cli_tools.helm import *
from ch_cli_tools.configurationgenerator import *
import pytest

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def exists(path):
    return path.exists()


def test_collect_helm_values(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples', 'myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='dev', local=False, tag=1, registry='reg')

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

    # Auto values
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'reg/testprojectname/myapp:1'
    assert values[KEY_APPS]['myapp']['build'] == True
    assert values.apps['myapp'].harness.deployment.image == 'reg/testprojectname/myapp:1'
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['name'] == 'myapp'
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['name'] == 'legacy'
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['image'] == 'reg/cloud-harness/accounts:1'

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
    assert values['database']['auto'] is False

    # legacy reading
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['auto'] is True
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['deployment']['auto'] is False

    helm_path = out_folder / HELM_CHART_PATH

    # Check files
    assert exists(helm_path)
    assert exists(helm_path / 'values.yaml')
    assert exists(helm_path / 'resources' / 'accounts' / 'realm.json')
    assert exists(helm_path / 'resources' / 'accounts' / 'aresource.txt')
    assert exists(helm_path / 'resources' / 'myapp' / 'aresource.txt')
    assert exists(helm_path / 'templates' / 'myapp' / 'mytemplate.yaml')

    # Checl base and task images
    assert values[KEY_TASK_IMAGES]
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES]
    assert values[KEY_TASK_IMAGES]['cloudharness-base'] == 'reg/testprojectname/cloudharness-base:1', "Cloudharness base image is overridden, so takes the main project name prefix"
    assert values[KEY_TASK_IMAGES]['myapp-mytask'] == 'reg/testprojectname/myapp-mytask:1'
    assert values[KEY_TASK_IMAGES]['cloudharness-flask'] == 'reg/cloud-harness/cloudharness-flask:1'
    # Not indicated as a build dependency
    assert 'cloudharness-base-debian' not in values[KEY_TASK_IMAGES]

    chart_values = yaml.safe_load(open(helm_path / 'charts/myapp/values.yaml', 'r'))  # Check if the values.yaml is valid YAML
    assert chart_values is not None, "values.yaml should be valid YAML"
    assert chart_values["test"] == "dev"


def test_collect_nobuild(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values'
    values = create_helm_chart([RESOURCES], output_path=out_folder, include=['myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='nobuild', local=False, tag=1, registry='reg')
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'custom-image'
    assert values[KEY_APPS]['myapp']['build'] == False


def test_collect_helm_values_noreg_noinclude(tmp_path):
    out_path = tmp_path / 'test_collect_helm_values_noreg_noinclude'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_path, domain="my.local",
                               namespace='test', env='dev', local=False, tag=1)

    # Auto values
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'testprojectname/myapp:1'
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['name'] == 'myapp'
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['name'] == 'legacy'
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['image'] == 'cloud-harness/accounts:1'

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
    assert values['database']['auto'] is False

    # legacy reading
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['auto'] is True
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['deployment']['auto'] is False

    helm_path = out_path / HELM_CHART_PATH

    # Check files
    assert exists(helm_path)
    assert exists(helm_path / 'values.yaml')
    assert exists(helm_path / 'resources' / 'accounts' / 'realm.json')
    assert exists(helm_path / 'resources' / 'accounts' / 'aresource.txt')
    assert exists(helm_path / 'resources' / 'myapp' / 'aresource.txt')
    assert exists(helm_path / 'templates' / 'myapp' / 'mytemplate.yaml')

    assert values[KEY_TASK_IMAGES]
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES]
    assert values[KEY_TASK_IMAGES]['cloudharness-base'] == 'testprojectname/cloudharness-base:1'
    assert values[KEY_TASK_IMAGES]['myapp-mytask'] == 'testprojectname/myapp-mytask:1'
    assert values[KEY_TASK_IMAGES]['my-common'] == 'testprojectname/my-common:1'


def test_collect_helm_values_precedence(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values_precedence'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["events"])

    # Values.yaml from current app must override values-prod.yaml from cloudharness
    assert values[KEY_APPS]['events']['kafka']['resources']['limits']['memory'] == 'overridden'
    assert values[KEY_APPS]['events']['kafka']['resources']['limits']['cpu'] == 'overridden-prod'


def test_collect_helm_values_multiple_envs(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values_multiple_envs'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', env=['dev', 'test'], local=False, tag=1, include=["myapp"])

    assert values[KEY_APPS]['myapp']['test'] is True, 'values-test not loaded'
    assert values[KEY_APPS]['myapp']['dev'] is True, 'values-dev not loaded'
    assert values[KEY_APPS]['myapp']['a'] == 'test', 'values-test not overriding'


def test_collect_helm_values_wrong_dependencies_validate(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values_wrong_dependencies_validate'
    with pytest.raises(ValuesValidationException):
        create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=out_folder, domain="my.local",
                          namespace='test', env='prod', local=False, tag=1, include=["wrong-hard"])
    try:
        create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=out_folder, domain="my.local",
                          namespace='test', env='prod', local=False, tag=1, include=["wrong-soft"])

    except ValuesValidationException as e:
        pytest.fail("Should not error because of wrong soft dependency")

    with pytest.raises(ValuesValidationException):
        create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=out_folder, domain="my.local",
                          namespace='test', env='prod', local=False, tag=1, include=["wrong-build"])
    with pytest.raises(ValuesValidationException):
        create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=out_folder, domain="my.local",
                          namespace='test', env='prod', local=False, tag=1, include=["wrong-services"])


def test_collect_helm_values_build_dependencies(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values_build_dependencies'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["myapp"])

    assert 'cloudharness-flask' in values[KEY_TASK_IMAGES], "Cloudharness-flask is included in the build dependencies"
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES], "Cloudharness-base is included in cloudharness-flask Dockerfile and it should be guessed"
    assert 'cloudharness-base-debian' not in values[KEY_TASK_IMAGES], "Cloudharness-base-debian is not included in any dependency"
    assert 'cloudharness-frontend-build' not in values[KEY_TASK_IMAGES], "cloudharness-frontend-build is not included in any dependency"


def test_collect_helm_values_build_dependencies_nodeps(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values_build_dependencies_nodeps'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["events"])

    assert 'cloudharness-flask' not in values[KEY_TASK_IMAGES], "Cloudharness-flask is not included in the build dependencies"
    assert 'cloudharness-base' not in values[KEY_TASK_IMAGES], "Cloudharness-base is not included in the build dependencies"
    assert 'cloudharness-base-debian' not in values[KEY_TASK_IMAGES], "Cloudharness-base-debian is not included in any dependency"
    assert 'cloudharness-frontend-build' not in values[KEY_TASK_IMAGES], "cloudharness-frontend-build is not included in any dependency"


def test_collect_helm_values_build_dependencies_exclude(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values_build_dependencies_exclude'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', env='prod', local=False, tag=1, include=["workflows"], exclude=["workflows-extract-download"])

    assert 'cloudharness-flask' in values[KEY_TASK_IMAGES], "Cloudharness-flask is included in the build dependencies"
    assert 'cloudharness-base' in values[KEY_TASK_IMAGES], "Cloudharness-base is included in cloudharness-flask Dockerfile and it should be guessed"
    assert 'workflows-extract-download' not in values[KEY_TASK_IMAGES], "workflows-extract-download has been explicitly excluded"


def test_clear_unused_dbconfig(tmp_path):
    out_folder = tmp_path / 'test_clear_unused_dbconfig'

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='withpostgres', local=False, include=["myapp"], exclude=["legacy"])

    # There is a DB config
    assert KEY_DATABASE in values[KEY_APPS]['myapp'][KEY_HARNESS]

    db_config = values[KEY_APPS]['myapp'][KEY_HARNESS][KEY_DATABASE]
    # postgres is set, but other entries are not.
    assert db_config['postgres'] is not None
    assert db_config['postgres']['image'].startswith('postgres:')

    # However, it seems that even after removing unused entries,
    # the finale instance of the HarnessMainConfig class that is created
    # adds back those entries and set them to None.
    assert db_config['mongo'] is None
    assert db_config['neo4j'] is None

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='withmongo', local=False, include=["myapp"], exclude=["legacy"])

    assert KEY_DATABASE in values[KEY_APPS]['myapp'][KEY_HARNESS]
    db_config = values[KEY_APPS]['myapp'][KEY_HARNESS][KEY_DATABASE]

    # mongo is set, but other entries are not.
    assert db_config['mongo'] is not None
    assert db_config['mongo']['image'].startswith('mongo:')
    assert db_config['neo4j'] is None

    assert db_config['postgres'] is None


def test_clear_all_dbconfig_if_nodb(tmp_path):
    out_folder = tmp_path / 'test_clear_all_dbconfig_if_nodb'

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='withoutdb', local=False, include=["myapp"], exclude=["legacy"])

    # There is a DB config
    assert KEY_DATABASE in values[KEY_APPS]['myapp'][KEY_HARNESS]

    # But it is None
    db_config = values[KEY_APPS]['myapp'][KEY_HARNESS][KEY_DATABASE]
    assert db_config is None


def test_tag_hash_generation():
    v1 = generate_tag_from_content(RESOURCES)
    v2 = generate_tag_from_content(RESOURCES, ignore=['myapp'])
    assert v1 != v2
    v3 = generate_tag_from_content(RESOURCES, ignore=['*/myapp/*'])
    assert v3 != v1
    v4 = generate_tag_from_content(RESOURCES, ignore=['applications/myapp/*'])
    assert v4 == v3
    v5 = generate_tag_from_content(RESOURCES, ignore=['/applications/myapp/*'])
    assert v5 == v4

    fname = Path(RESOURCES) / 'applications' / 'myapp' / 'afile.txt'
    try:
        fname.write_text('a')

        v6 = generate_tag_from_content(RESOURCES, ignore=['/applications/myapp/*'])
        assert v6 == v5
        v7 = generate_tag_from_content(RESOURCES)
        assert v7 != v1
    finally:
        fname.unlink()


def test_collect_helm_values_auto_tag(tmp_path):
    out_folder = str(tmp_path / 'test_collect_helm_values_auto_tag')

    def create():
        return create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples', 'myapp'],
                                 exclude=['events'], domain="my.local",
                                 namespace='test', env='dev', local=False, tag=None, registry='reg')

    BASE_KEY = "cloudharness-base"
    values = create()

    # Auto values are set by using the directory hash
    assert 'reg/testprojectname/myapp:' in values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image']
    assert 'reg/testprojectname/myapp:' in values.apps['myapp'].harness.deployment.image
    assert 'testprojectname/myapp-mytask' in values[KEY_TASK_IMAGES]['myapp-mytask']
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == values.apps['myapp'].harness.deployment.image
    v1 = values.apps['myapp'].harness.deployment.image
    c1 = values["task-images"]["my-common"]
    b1 = values["task-images"][BASE_KEY]
    d1 = values["task-images"]["cloudharness-flask"]

    values = create()
    assert v1 == values.apps['myapp'].harness.deployment.image, "Nothing changed the hash value"
    assert values["task-images"][BASE_KEY] == b1, "Base image should not change following the root .dockerignore"

    fname = Path(RESOURCES) / 'applications' / 'myapp' / 'afile.txt'
    try:
        fname.write_text('a')

        values = create()
        assert v1 != values.apps['myapp'].harness.deployment.image, "Adding the file changed the hash value"
        v2 = values.apps['myapp'].harness.deployment.image
        assert values["task-images"][BASE_KEY] == b1, "Application files should be ignored for base image following the root .dockerignore"
    finally:
        fname.unlink()

    try:
        fname.write_text('a')

        values = create()
        assert v2 == values.apps['myapp'].harness.deployment.image, "Recreated an identical file, the hash value should be the same"
    finally:
        fname.unlink()

    fname = Path(RESOURCES) / 'applications' / 'myapp' / 'afile.ignored'
    try:
        fname.write_text('a')

        values = create()
        assert values["task-images"][BASE_KEY] == b1, "2: Application files should be ignored for base image following the root .dockerignore"

        assert v1 == values.apps['myapp'].harness.deployment.image, "Nothing should change the hash value as the file is ignored in the .dockerignore"
    finally:
        fname.unlink()

    # Dependencies test: if a dependency is changed, the hash should change
    fname = Path(RESOURCES) / 'infrastructure' / 'common-images' / 'my-common' / 'afile'

    try:
        fname.write_text('a')

        values = create()

        assert c1 != values["task-images"]["my-common"], "If content of a static image is changed, the hash should change"
        assert v1 != values.apps['myapp'].harness.deployment.image, "If a static image dependency is changed, the hash should change"
    finally:
        fname.unlink()

    fname = Path(RESOURCES) / 'atestfile'
    try:
        fname.write_text('a')

        values = create()

        assert b1 != values["task-images"][BASE_KEY], "Content for base image is changed, the hash should change"
        assert d1 != values["task-images"]["cloudharness-flask"], "Content for base image is changed, the static image should change"
        assert v1 != values.apps['myapp'].harness.deployment.image, "2 levels dependency: If a base image dependency is changed, the hash should change"
    finally:
        fname.unlink()


def test_exclude_single_task(tmp_path):
    out_folder = tmp_path / 'test_exclude_single_task'

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='withpostgres', local=False, include=["myapp"], exclude=["myapp-mytask"])

    assert "myapp-mytask" not in values["task-images"], "myapp-mytask has been excluded, so should not appear in the task images"

    try:
        values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                                   env='fulldep', local=False, include=["dependantapp"], exclude=["myapp-mytask"])

        assert False, "myapp-mytask has been excluded, but also declared as a dependency, so should not be excluded"
    except ValuesValidationException as e:
        pass


def test_app_depends_on_app(tmp_path):
    out_folder = tmp_path / 'test_app_depends_on_app'

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='', local=False, include=["dependantapp"], exclude=[])
    assert "myapp" in values["task-images"], "myapp should be included as a task image because it is a dependency of dependantapp"
    assert "cloudharness-flask" in values["task-images"], "cloudharness-flask should be included as a task image because it is a dependency of myapp"
    assert "cloudharness-base" in values["task-images"], "cloudharness-flask should be included as a task image because it is a dependency of cloudharness-flask"
    assert "myapp-mytask" in values["task-images"], "task should be also included as build dependencies,as it's required by another task"
    assert "legacy" not in values["task-images"], "legacy should not be included as a task image because it is not a dependency"

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='testincludetask', local=False, include=["dependantapp"], exclude=[])

    assert "myapp" in values["task-images"], "myapp should be included as a task image because it is a dependency of dependantapp"
    assert "myapp-mytask" in values["task-images"], "tasks should be also included as build dependencies, when explicitly included as build dependencies"
