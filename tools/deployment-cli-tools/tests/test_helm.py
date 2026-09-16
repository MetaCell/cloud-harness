from ch_cli_tools.helm import *
from ch_cli_tools.configurationgenerator import *
from ch_cli_tools import configurationgenerator
from ch_cli_tools.preprocessing import preprocess_build_overrides, generate_hash_based_image_tags
import logging
import pytest
import shutil
import subprocess

import pytest
from ch_cli_tools import configurationgenerator
from ch_cli_tools.configurationgenerator import *
from ch_cli_tools.helm import *
from ch_cli_tools.preprocessing import (
    generate_hash_based_image_tags,
    preprocess_build_overrides,
)
from ch_cli_tools.instances import *

HERE = os.path.dirname(os.path.realpath(__file__))
RESOURCES = os.path.join(HERE, 'resources')
CLOUDHARNESS_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))


def exists(path):
    return path.exists()


def render_helm_chart(chart_path):
    completed = subprocess.run(
        ["helm", "template", str(chart_path)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return [manifest for manifest in yaml.load_all(completed.stdout) if manifest]


def find_manifest(manifests, kind, name):
    for manifest in manifests:
        if manifest.get("kind") == kind and manifest.get("metadata", {}).get("name") == name:
            return manifest
    raise AssertionError(f"Could not find {kind}/{name}")


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
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['image'] == 'reg/testprojectname/accounts:1'

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
    assert values[KEY_TASK_IMAGES]['cloudharness-base'] == 'reg/testprojectname/cloudharness-base:1'
    assert values[KEY_TASK_IMAGES]['myapp-mytask'] == 'reg/testprojectname/myapp-mytask:1'
    assert values[KEY_TASK_IMAGES]['cloudharness-flask'] == 'reg/testprojectname/cloudharness-flask:1'
    # Not indicated as a build dependency
    assert 'cloudharness-base-debian' not in values[KEY_TASK_IMAGES]

    with open(helm_path / 'charts/myapp/values.yaml', 'r') as values_file:
        chart_values = yaml.load(values_file)  # Check if the values.yaml is valid YAML
    assert chart_values is not None, "values.yaml should be valid YAML"
    assert chart_values["test"] == "dev"


def test_collect_nobuild(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values'
    values = create_helm_chart([RESOURCES], output_path=out_folder, include=['myapp'],
                               exclude=['events'], domain="my.local",
                               namespace='test', env='nobuild', local=False, tag=1, registry='reg')
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'custom-image'
    assert values[KEY_APPS]['myapp']['build'] == False


def test_collect_helm_values_harness_image_name_override(tmp_path):
    out_folder = tmp_path / 'test_collect_helm_values_harness_image_name_override'

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['myapp'],
                               domain="my.local", namespace='test', env='imagename', local=False, tag=1, registry='reg')

    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'reg/testprojectname/custom-myapp:1'
    assert values[KEY_APPS]['myapp'][KEY_TASK_IMAGES]['myapp-mytask'] == 'reg/testprojectname/custom-myapp-mytask:1'


def test_collect_helm_values_noreg_noinclude(tmp_path):
    out_path = tmp_path / 'test_collect_helm_values_noreg_noinclude'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_path, domain="my.local",
                               namespace='test', env='dev', local=False, tag=1)

    # Auto values
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'testprojectname/myapp:1'
    assert values[KEY_APPS]['myapp'][KEY_HARNESS]['name'] == 'myapp'
    assert values[KEY_APPS]['legacy'][KEY_HARNESS]['name'] == 'legacy'
    assert values[KEY_APPS]['accounts'][KEY_HARNESS]['deployment']['image'] == 'testprojectname/accounts:1'

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

    # Check source images
    # KEYCLOAK is overriden and mybase and mybase2 should appear as they have been collected
    assert values["source_images"] == {
        "GOLANG": "golang:1.26",
        "ROCKYLINUX": "rockylinux/rockylinux:10.1-minimal",
        "SENTRY": "sentry:9.1.2",
        "KEYCLOAK": "myregistry.mykeycloak:99.9",
        "mybase": "foo:bar",
        "mybase2": "spam:egg",
        "NODE": "node:22-alpine",
    }


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


def test_collect_app_defaults_env_specific(tmp_path):
    """value-template-[env].yaml overrides value-template.yaml application defaults"""
    conf_path = tmp_path / DEPLOYMENT_CONFIGURATION_PATH
    conf_path.mkdir(parents=True)
    (conf_path / 'value-template.yaml').write_text('base: 1\nenv-defaults: base\n')
    (conf_path / 'value-template-dev.yaml').write_text('env-defaults: dev\n')

    assert collect_app_defaults(tmp_path, env=('dev',)) == {
        'base': 1, 'env-defaults': 'dev'}
    assert collect_app_defaults(tmp_path, env=('other',)) == {
        'base': 1, 'env-defaults': 'base'}, 'value-template-dev.yaml loaded for the wrong environment'
    assert collect_app_defaults(tmp_path) == {
        'base': 1, 'env-defaults': 'base'}, 'value-template-dev.yaml loaded without environment'


def test_init_app_values_env_specific_defaults(tmp_path, monkeypatch):
    """Cloudharness application defaults, including the environment specific ones,
    apply to the applications of any root, and are overridden by the current root"""
    ch_root = tmp_path / 'cloudharness'
    (ch_root / DEPLOYMENT_CONFIGURATION_PATH).mkdir(parents=True)
    (ch_root / DEPLOYMENT_CONFIGURATION_PATH /
     'value-template.yaml').write_text('ch-defaults: base\nenv-defaults: ch-base\n')
    (ch_root / DEPLOYMENT_CONFIGURATION_PATH /
     'value-template-dev.yaml').write_text('ch-env-defaults: ch-dev\nenv-defaults: ch-dev\n')

    deployment_root = tmp_path / 'deployment'
    (deployment_root / APPS_PATH / 'myapp').mkdir(parents=True)
    (deployment_root / DEPLOYMENT_CONFIGURATION_PATH).mkdir(parents=True)
    (deployment_root / DEPLOYMENT_CONFIGURATION_PATH /
     'value-template-dev.yaml').write_text('env-defaults: root-dev\n')

    monkeypatch.setattr(configurationgenerator, 'CH_ROOT', str(ch_root))

    values = init_app_values(deployment_root, exclude=(), env=('dev',))
    assert values['myapp']['ch-defaults'] == 'base'
    assert values['myapp']['ch-env-defaults'] == 'ch-dev', 'cloudharness value-template-dev.yaml not applied'
    assert values['myapp']['env-defaults'] == 'root-dev', 'current root must take precedence'

    values = init_app_values(deployment_root, exclude=(), env=())
    assert 'ch-env-defaults' not in values['myapp']
    assert values['myapp']['env-defaults'] == 'ch-base'


def test_collect_app_defaults_env_specific_chart(tmp_path):
    """The deployment root value-template-[env].yaml lands in the generated chart values"""
    out_folder = tmp_path / 'test_collect_app_defaults_env_specific_chart'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', env='dev', local=False, tag=1, include=["myapp"])

    assert values[KEY_APPS]['myapp']['env-defaults'] == 'resources-dev'

    out_folder = tmp_path / 'test_collect_app_defaults_no_env_chart'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', local=False, tag=1, include=["myapp"])

    assert 'env-defaults' not in values[KEY_APPS]['myapp']


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
    try:
        create_helm_chart([CLOUDHARNESS_ROOT, f"{RESOURCES}/wrong-dependencies"], output_path=out_folder, domain="my.local",
                          namespace='test', env='prod', local=False, tag=1, include=["wrong-services"])
    except ValuesValidationException:
        pytest.fail("Should not error because of missing use_services dependency")


def test_validate_dependencies_accepts_app_local_build_images():
    values = {
        KEY_APPS: {
            'portal': {
                KEY_HARNESS: {
                    'dependencies': {
                        'soft': [],
                        'hard': [],
                        'build': ['cloudharness-base', 'cloudharness-django'],
                    },
                    'use_services': [],
                },
                KEY_TASK_IMAGES: {
                    'cloudharness-base': 'reg/project/cloudharness-base:1',
                    'cloudharness-django': 'reg/project/cloudharness-django:1',
                },
            }
        },
        KEY_TASK_IMAGES: {},
    }

    validate_dependencies(values)


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


def test_cnpg_postgres_parameters_render_only_when_set(tmp_path):
    out_folder = tmp_path / 'test_cnpg_postgres_parameters_render_only_when_set'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='withpostgres', local=False, include=["myapp"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.load(values_file)
    postgres = values['apps']['myapp']['harness']['database']['postgres']
    postgres['operator'] = True
    postgres['parameters'] = {
        # Simulate generated YAML values where on/off can be parsed as booleans before Helm renders the chart.
        'autovacuum': True,
        'max_connections': '200',
        'shared_buffers': '1GB',
        'synchronous_commit': True,
        'track_io_timing': False,
    }
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    db_name = values['apps']['myapp']['harness']['database']['name']
    cluster = find_manifest(manifests, 'Cluster', db_name)
    assert cluster['spec']['postgresql']['parameters'] == {
        'autovacuum': 'true',
        'max_connections': '200',
        'shared_buffers': '1GB',
        'synchronous_commit': 'true',
        'track_io_timing': 'false',
    }

    postgres['parameters'] = {}
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    cluster = find_manifest(manifests, 'Cluster', db_name)
    assert 'postgresql' not in cluster['spec']

    postgres.pop('parameters')
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    cluster = find_manifest(manifests, 'Cluster', db_name)
    assert 'postgresql' not in cluster['spec']


def test_statefulset_option(tmp_path):
    out_folder = tmp_path / 'test_statefulset_option'
    # nfsserver is included to provide the storage class values needed by the usenfs case
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='withpostgres', local=False, include=["myapp", "nfsserver"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.load(values_file)

    myapp = values['apps']['myapp']
    harness = myapp['harness']
    dep_name = harness['deployment']['name']
    db_name = harness['database']['name']
    service_name = harness['service']['name']

    harness['deployment']['auto'] = True
    harness['deployment']['volume'] = {
        'name': 'myapp-data', 'mountpath': '/data', 'size': '1Gi', 'auto': True,
    }
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    # Default: Deployments with the Recreate/affinity workaround and a standalone PVC
    manifests = render_helm_chart(helm_path)
    dep = find_manifest(manifests, 'Deployment', dep_name)
    assert dep['spec']['strategy']['type'] == 'Recreate'
    assert 'affinity' in dep['spec']['template']['spec']
    find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    db_dep = find_manifest(manifests, 'Deployment', db_name)
    assert db_dep['spec']['strategy']['type'] == 'Recreate'
    assert 'affinity' in db_dep['spec']['template']['spec']
    find_manifest(manifests, 'PersistentVolumeClaim', db_name)

    # Opt in to StatefulSets: volumes are provisioned via volumeClaimTemplates. The legacy
    # volume migration (job copying a pre-existing PVC found by `lookup` into the statefulset
    # volumes) cannot be exercised here: `helm template` runs without a cluster, so `lookup`
    # finds nothing.
    harness['deployment']['statefulset'] = True
    harness['database']['statefulset'] = True
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    sts = find_manifest(manifests, 'StatefulSet', dep_name)
    assert sts['spec']['serviceName'] == service_name
    # OrderedReady would block template updates while an existing pod is unready,
    # so a crash-looping pod could never be replaced by its own fix.
    assert sts['spec']['podManagementPolicy'] == 'Parallel'
    assert 'strategy' not in sts['spec']
    assert 'affinity' not in sts['spec']['template']['spec']
    assert 'initContainers' not in sts['spec']['template']['spec']
    claims = [v['persistentVolumeClaim']['claimName']
              for v in sts['spec']['template']['spec']['volumes'] if 'persistentVolumeClaim' in v]
    assert 'myapp-data' not in claims
    assert sts['spec']['volumeClaimTemplates'][0]['metadata']['name'] == 'myapp-data'
    assert not any(m for m in manifests
                   if m.get('kind') == 'PersistentVolumeClaim' and m.get('metadata', {}).get('name') == 'myapp-data')

    db_sts = find_manifest(manifests, 'StatefulSet', db_name)
    assert db_sts['spec']['serviceName'] == db_name
    assert db_sts['spec']['podManagementPolicy'] == 'Parallel'
    assert 'strategy' not in db_sts['spec']
    assert 'affinity' not in db_sts['spec']['template']['spec']
    assert 'initContainers' not in db_sts['spec']['template']['spec']
    assert db_sts['spec']['volumeClaimTemplates'][0]['metadata']['name'] == db_name
    assert not any(m for m in manifests
                   if m.get('kind') == 'PersistentVolumeClaim' and m.get('metadata', {}).get('name') == db_name)
    find_manifest(manifests, 'Service', db_name)
    # without a legacy PVC no migration resources are rendered
    assert not any(m for m in manifests if 'volume-migration' in m.get('metadata', {}).get('name', ''))

    # nfs (shared) volumes are never per-replica: the statefulset keeps mounting the common
    # PVC by claimName and no volumeClaimTemplates are created.
    harness['deployment']['volume']['usenfs'] = True
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    sts = find_manifest(manifests, 'StatefulSet', dep_name)
    assert 'volumeClaimTemplates' not in sts['spec']
    claims = [v['persistentVolumeClaim']['claimName']
              for v in sts['spec']['template']['spec']['volumes'] if 'persistentVolumeClaim' in v]
    assert 'myapp-data' in claims
    shared_pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    assert shared_pvc['spec']['accessModes'] == ['ReadWriteMany']

    # volume.auto: false means the PVC is managed externally: always reference it by
    # claimName, never via volumeClaimTemplates.
    harness['deployment']['volume']['usenfs'] = False
    harness['deployment']['volume']['auto'] = False
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    sts = find_manifest(manifests, 'StatefulSet', dep_name)
    assert 'volumeClaimTemplates' not in sts['spec']
    claims = [v['persistentVolumeClaim']['claimName']
              for v in sts['spec']['template']['spec']['volumes'] if 'persistentVolumeClaim' in v]
    assert 'myapp-data' in claims


def test_volume_write_many(tmp_path):
    out_folder = tmp_path / 'test_volume_write_many'
    # nfsserver is deliberately not included: a ReadWriteMany volume must not rely on it
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='withpostgres', local=False, include=["myapp"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.load(values_file)

    harness = values['apps']['myapp']['harness']
    dep_name = harness['deployment']['name']

    harness['deployment']['auto'] = True
    volume = {'name': 'myapp-data', 'mountpath': '/data', 'size': '1Gi', 'auto': True}
    harness['deployment']['volume'] = volume

    def render():
        with open(values_path, 'w') as values_file:
            yaml.dump(values, values_file)
        return render_helm_chart(helm_path)

    # a null storage class is omitted, so the cluster default one is used
    volume['storageClass'] = None
    manifests = render()
    pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    assert 'storageClassName' not in pvc['spec']

    # a storage class can be set on a ReadWriteOnce volume, which keeps the node pinning
    volume['storageClass'] = 'gp3'
    manifests = render()
    pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    assert pvc['spec']['accessModes'] == ['ReadWriteOnce']
    assert pvc['spec']['storageClassName'] == 'gp3'
    dep = find_manifest(manifests, 'Deployment', dep_name)
    assert dep['spec']['strategy']['type'] == 'Recreate'
    assert 'affinity' in dep['spec']['template']['spec']

    # a writeMany volume keeps its storage class, and its pod is neither pinned to a node nor
    # recreated on update
    volume['writeMany'] = True
    manifests = render()
    pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    assert pvc['spec']['accessModes'] == ['ReadWriteMany']
    assert pvc['spec']['storageClassName'] == 'gp3'
    dep = find_manifest(manifests, 'Deployment', dep_name)
    assert 'strategy' not in dep['spec']
    assert 'affinity' not in dep['spec']['template']['spec']

    # writeMany with an explicit ReadWriteMany capable storage class
    volume['storageClass'] = 'efs-sc'
    manifests = render()
    pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    assert pvc['spec']['accessModes'] == ['ReadWriteMany']
    assert pvc['spec']['storageClassName'] == 'efs-sc'

    # a null storage class is omitted from a ReadWriteMany claim too
    volume['storageClass'] = None
    manifests = render()
    pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    assert 'storageClassName' not in pvc['spec']
    volume['storageClass'] = 'efs-sc'
    manifests = render()
    assert find_manifest(manifests, 'PersistentVolumeClaim',
                         'myapp-data')['spec']['storageClassName'] == 'efs-sc'

    # ReadWriteMany volumes are shared: a statefulset keeps mounting the common PVC by
    # claimName instead of provisioning one per replica
    harness['deployment']['statefulset'] = True
    manifests = render()
    sts = find_manifest(manifests, 'StatefulSet', dep_name)
    assert 'volumeClaimTemplates' not in sts['spec']
    claims = [v['persistentVolumeClaim']['claimName']
              for v in sts['spec']['template']['spec']['volumes'] if 'persistentVolumeClaim' in v]
    assert 'myapp-data' in claims
    pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    assert pvc['spec']['accessModes'] == ['ReadWriteMany']

    # the storage class of a per-replica statefulset volume is configurable too
    volume['writeMany'] = False
    volume['storageClass'] = 'gp3'
    manifests = render()
    sts = find_manifest(manifests, 'StatefulSet', dep_name)
    claim_template = sts['spec']['volumeClaimTemplates'][0]
    assert claim_template['metadata']['name'] == 'myapp-data'
    assert claim_template['spec']['accessModes'] == ['ReadWriteOnce']
    assert claim_template['spec']['storageClassName'] == 'gp3'


def test_volume_storage_class_default(tmp_path):
    out_folder = tmp_path / 'test_volume_storage_class_default'
    # samples declares a volume, myapp does not
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='withpostgres', local=False, include=["samples", "myapp"], exclude=["legacy"])

    # the value-template default applies to the volume declared by the application
    volume = values[KEY_APPS]['samples'][KEY_HARNESS]['deployment']['volume']
    assert volume['mountpath']
    assert volume['storageClass'] == 'standard'

    # ... and the defaults alone do not make a volume: a volume-less application has none
    assert not values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment'].get('volume')

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    manifests = render_helm_chart(helm_path)
    sts = find_manifest(manifests, 'StatefulSet', values[KEY_APPS]['samples'][KEY_HARNESS]['deployment']['name'])
    assert sts['spec']['volumeClaimTemplates'][0]['spec']['storageClassName'] == 'standard'


def test_volume_without_mountpath_is_rejected():
    harness = {'name': 'myapp', KEY_DEPLOYMENT: {'volume': {'name': 'myapp-data', 'size': '1Gi'}}}
    with pytest.raises(ValuesValidationException):
        clear_unused_volume_configuration(harness)

    # the defaults alone are dropped, a declared volume is kept
    harness = {'name': 'myapp', KEY_DEPLOYMENT: {'volume': {'storageClass': 'standard'}}}
    clear_unused_volume_configuration(harness)
    assert 'volume' not in harness[KEY_DEPLOYMENT]

    volume = {'name': 'myapp-data', 'mountpath': '/data', 'storageClass': 'standard'}
    harness = {'name': 'myapp', KEY_DEPLOYMENT: {'volume': volume}}
    clear_unused_volume_configuration(harness)
    assert harness[KEY_DEPLOYMENT]['volume'] == volume


def test_volume_usenfs_prevails(tmp_path):
    out_folder = tmp_path / 'test_volume_usenfs_prevails'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='withpostgres', local=False, include=["myapp", "nfsserver"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.load(values_file)

    harness = values['apps']['myapp']['harness']
    harness['deployment']['auto'] = True
    # colliding settings: the nfs server storage class and access mode prevail
    harness['deployment']['volume'] = {
        'name': 'myapp-data', 'mountpath': '/data', 'size': '1Gi', 'auto': True,
        'usenfs': True, 'writeMany': False, 'storageClass': 'efs-sc',
    }
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    pvc = find_manifest(manifests, 'PersistentVolumeClaim', 'myapp-data')
    nfs_class = f"{values['namespace']}-{values['apps']['nfsserver']['storageClass']['name']}"
    assert pvc['spec']['storageClassName'] == nfs_class
    assert pvc['spec']['accessModes'] == ['ReadWriteMany']
    dep = find_manifest(manifests, 'Deployment', harness['deployment']['name'])
    assert 'affinity' not in dep['spec']['template']['spec']


def test_validate_volumes_warns_on_nfs_collisions(caplog):
    volume = {'name': 'myapp-data', 'usenfs': True, 'writeMany': False, 'storageClass': 'efs-sc'}
    values = {'apps': {'myapp': {KEY_HARNESS: {'deployment': {'volume': volume}}}}}

    with caplog.at_level(logging.WARNING):
        validate_volumes(values)
    assert 'the nfs server storage class prevails' in caplog.text
    assert 'always mounted ReadWriteMany' in caplog.text

    # no collision: nothing to warn about
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        validate_volumes({'apps': {'myapp': {KEY_HARNESS: {'deployment': {'volume': {
            'name': 'myapp-data', 'usenfs': True, 'writeMany': True}}}}}})
        validate_volumes({'apps': {'myapp': {KEY_HARNESS: {'deployment': {'volume': {
            'name': 'myapp-data', 'storageClass': 'efs-sc', 'writeMany': True}}}}}})
        validate_volumes({'apps': {'myapp': {KEY_HARNESS: {'deployment': {}}}}})
    assert not caplog.text


def test_database_storage_class(tmp_path):
    out_folder = tmp_path / 'test_database_storage_class'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='withpostgres', local=False, include=["myapp"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.load(values_file)

    database = values['apps']['myapp']['harness']['database']
    db_name = database['name']

    def render():
        with open(values_path, 'w') as values_file:
            yaml.dump(values, values_file)
        return render_helm_chart(helm_path)

    # not set by default: the claim carries no storage class, so the cluster default one is used.
    # The storage class is immutable on an existing claim, hence never set implicitly: database
    # volumes of existing deployments must keep rendering without it.
    assert database['storageClass'] is None
    manifests = render()
    assert 'storageClassName' not in find_manifest(manifests, 'PersistentVolumeClaim', db_name)['spec']

    database['storageClass'] = 'gp3'
    manifests = render()
    assert find_manifest(manifests, 'PersistentVolumeClaim', db_name)['spec']['storageClassName'] == 'gp3'

    # statefulset databases provision their volume through volumeClaimTemplates
    database['statefulset'] = True
    manifests = render()
    sts = find_manifest(manifests, 'StatefulSet', db_name)
    assert sts['spec']['volumeClaimTemplates'][0]['spec']['storageClassName'] == 'gp3'
    database['storageClass'] = None
    manifests = render()
    sts = find_manifest(manifests, 'StatefulSet', db_name)
    assert 'storageClassName' not in sts['spec']['volumeClaimTemplates'][0]['spec']

    # the postgres operator cluster storage honours the same setting
    database['statefulset'] = False
    database['postgres']['operator'] = True
    database['storageClass'] = 'gp3'
    manifests = render()
    assert find_manifest(manifests, 'Cluster', db_name)['spec']['storage']['storageClass'] == 'gp3'
    database['storageClass'] = None
    manifests = render()
    assert 'storageClass' not in find_manifest(manifests, 'Cluster', db_name)['spec']['storage']


def test_statefulset_leader_service(tmp_path):
    out_folder = tmp_path / 'test_statefulset_leader_service'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='withpostgres', local=False, include=["myapp"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.load(values_file)

    harness = values['apps']['myapp']['harness']
    dep_name = harness['deployment']['name']
    service_name = harness['service']['name']
    rw_name = f"{service_name}-rw"

    def ingress_paths(manifests):
        ingress = find_manifest(manifests, 'Ingress', 'myapp')
        return [path for rule in ingress['spec']['rules'] for path in rule['http']['paths']]

    # write methods in uri_role_mapping without statefulset: no leader service, no leader routing
    harness['uri_role_mapping'] = harness.get('uri_role_mapping', []) + [
        {'uri': '/api/edit/*', 'methods': ['POST', 'PUT', 'PATCH']},
        {'uri': '/upload', 'methods': ['POST']},
        {'uri': '/api/remove', 'methods': ['DELETE']},
        {'uri': '/readonly', 'methods': ['GET']},
    ]
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    assert not any(m for m in manifests
                   if m.get('kind') == 'Service' and m.get('metadata', {}).get('name') == rw_name)
    assert not any(p for p in ingress_paths(manifests)
                   if p['backend']['service']['name'] == rw_name)

    harness['deployment']['statefulset'] = True
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    rw_service = find_manifest(manifests, 'Service', rw_name)
    assert rw_service['spec']['selector']['app'] == dep_name
    assert rw_service['spec']['selector']['statefulset.kubernetes.io/pod-name'] == f"{dep_name}-0"
    main_service = find_manifest(manifests, 'Service', service_name)
    assert rw_service['spec']['ports'] == main_service['spec']['ports']

    paths = ingress_paths(manifests)
    rw_paths = {p['path']: p for p in paths if p['backend']['service']['name'] == rw_name}
    # wildcard uris map to Prefix rules, plain uris to ImplementationSpecific; any write method
    # (POST/PUT/PATCH/DELETE) triggers leader routing, while entries without one (the default
    # catch-all, /readonly) are not routed to the leader
    assert set(rw_paths) == {'/api/edit', '/upload', '/api/remove'}
    assert rw_paths['/api/edit']['pathType'] == 'Prefix'
    assert rw_paths['/upload']['pathType'] == 'ImplementationSpecific'
    # the catch-all still routes to the normal service
    assert any(p for p in paths
               if p['path'] == '/' and p['backend']['service']['name'] == service_name)


def test_gatekeeper_native_configuration_rendering_and_checksum(tmp_path):
    out_folder = tmp_path / 'test_gatekeeper_native_configuration'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      local=False, tls=True, include=["myapp", "accounts"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.load(values_file)

    app_harness = values['apps']['myapp']['harness']
    app_harness['secured'] = True
    app_harness['proxy']['gatekeeper']['configuration'] = {
        'same-site-cookie': 'None',
        'enable-pkce': False,
        'http-only-cookie': True,
        'cors-exposed-headers': ['X-Request-ID', 'X-Trace-ID'],
    }
    values['proxy']['gatekeeper']['configuration'] = {
        'same-site-cookie': 'Strict',
        'enable-pkce': True,
        'max-token-size': 65536,
    }

    def render_gatekeeper():
        with open(values_path, 'w') as values_file:
            yaml.dump(values, values_file)
        manifests = render_helm_chart(helm_path)
        config = find_manifest(manifests, 'ConfigMap', 'mysubdomain-gk')
        deployment = find_manifest(manifests, 'Deployment', 'mysubdomain-gk')
        return (
            yaml.load(config['data']['proxy.yml']),
            deployment['spec']['template']['metadata']['annotations']['checksum/config'],
        )

    tls_config, tls_checksum = render_gatekeeper()
    assert tls_config['secure-cookie'] is True
    assert tls_config['same-site-cookie'] == 'None'
    assert tls_config['enable-pkce'] is False
    assert tls_config['http-only-cookie'] is True
    assert tls_config['max-token-size'] == 65536
    assert tls_config['cors-exposed-headers'] == ['X-Request-ID', 'X-Trace-ID']

    values['tls'] = False
    non_tls_config, non_tls_checksum = render_gatekeeper()
    assert non_tls_config['secure-cookie'] is False
    assert non_tls_config['same-site-cookie'] == 'Lax'
    assert non_tls_config['enable-pkce'] is False
    assert non_tls_config['max-token-size'] == 65536
    assert non_tls_checksum != tls_checksum

    values['tls'] = True
    app_harness['proxy']['gatekeeper']['configuration'].pop('same-site-cookie')
    inherited_config, inherited_checksum = render_gatekeeper()
    assert inherited_config['same-site-cookie'] == 'Strict'
    assert inherited_config['enable-pkce'] is False
    assert inherited_checksum != tls_checksum


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
    merge_build_path = str(tmp_path / '.overrides')

    first_pass = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples', 'myapp'],
                                   exclude=['events'], domain="my.local",
                                   namespace='test', env='dev', local=False, tag=None, registry='reg')
    assert first_pass[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['image'] == 'reg/testprojectname/myapp'

    def create():
        values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples', 'myapp'],
                                   exclude=['events'], domain="my.local",
                                   namespace='test', env='dev', local=False, tag=None, registry='reg')
        preprocess_build_overrides([CLOUDHARNESS_ROOT, RESOURCES], values, merge_build_path=merge_build_path)
        generate_hash_based_image_tags([CLOUDHARNESS_ROOT, RESOURCES], values, merge_build_path=merge_build_path)
        return values

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


def test_network_policy_defaults_from_value_template(tmp_path):
    """Verify that allowedNamespaces set in a root directory's value-template.yaml
    propagates into app values and is not reset to []."""
    out_folder = tmp_path / 'test_network_policy_defaults_from_value_template'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['myapp'],
                               domain="my.local", namespace='test', env='dev', local=False, tag=1)

    network = values[KEY_APPS]['myapp'][KEY_HARNESS]['deployment']['network']
    assert network is not None, "network config should be present"
    allowed = network.get('allowedNamespaces') or []
    assert 'test-namespace' in allowed, (
        f"allowedNamespaces from value-template override should contain 'test-namespace', got: {allowed}"
    )

    out_folder = tmp_path / 'test_chart_metadata_optional_overrides'
    create_helm_chart(
        [CLOUDHARNESS_ROOT, RESOURCES],
        output_path=out_folder,
        include=['myapp'],
        domain="my.local",
        namespace='custom-ns',
        name='custom-chart',
        chart_version='9.8.7',
        app_version='4.5.6',
        env='dev',
        local=False,
        tag=1,
        registry='reg'
    )

    chart_path = out_folder / HELM_CHART_PATH / 'Chart.yaml'
    with open(chart_path, 'r') as chart_file:
        chart = yaml.load(chart_file)
    assert chart['name'] == 'custom-chart'
    assert chart['version'] == '9.8.7'
    assert chart['appVersion'] == '4.5.6'
    assert chart['metadata']['namespace'] == 'custom-ns'


def test_exclude_single_task(tmp_path):
    out_folder = tmp_path / 'test_exclude_single_task'

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='withpostgres', local=False, include=["myapp"], exclude=["myapp-mytask"])

    assert "myapp-mytask" not in values["task-images"], "myapp-mytask has been excluded, so should not appear in the task images"

    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='fulldep', local=False, include=["dependantapp"], exclude=["myapp-mytask"])

    assert "myapp-mytask" in values[KEY_TASK_IMAGES], (
        "myapp-mytask is excluded but still required by dependantapp, so it should be kept"
    )


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


def test_app_depends_on_task_only(tmp_path):
    out_folder = tmp_path / 'test_app_depends_on_task_only'

    # taskdep depends on a base image (cloudharness-flask, which its Dockerfile uses) and
    # on myapp-mytask, a task image owned by another app (myapp) that is not listed as a
    # dependency itself. The owner app must be pulled in to build the task image, but must
    # not be deployed.
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               env='', local=False, include=["taskdep"], exclude=[])

    assert "myapp-mytask" in values[KEY_TASK_IMAGES], "cross-app task image must be built"
    assert "cloudharness-flask" in values[KEY_TASK_IMAGES], "declared base-image build dep must be kept"
    assert "myapp" not in values[KEY_APPS], "owner app must be built but not deployed"


def find_manifests(manifests, kind, name=None):
    return [manifest for manifest in manifests
            if manifest.get("kind") == kind and
            (name is None or manifest.get("metadata", {}).get("name") == name)]


def render_with_secrets(tmp_path, name, secrets, secretmanagers=None, app='myapp', include=None, patch=None):
    """Generate the chart, override the application secrets and render it."""
    out_folder = tmp_path / name
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='', local=False, include=include or [app], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts', ignore_errors=True)
    values_path = helm_path / 'values.yaml'
    with open(values_path) as values_file:
        values = yaml.load(values_file)
    values['apps'][app]['harness']['secrets'] = secrets
    # the test applications are not deployed by default, but we need the deployment to
    # check how the secrets are mounted
    values['apps'][app]['harness']['deployment']['auto'] = True
    if secretmanagers is not None:
        values['secretmanagers'] = secretmanagers
    if patch:
        patch(values)
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    return render_helm_chart(helm_path)


def secrets_volume(manifests, app='myapp'):
    deployment = find_manifest(manifests, 'Deployment', app)
    volumes = [v for v in deployment['spec']['template']['spec']['volumes'] if v['name'] == 'secrets']
    assert volumes, "the secrets volume is not mounted"
    return volumes[0]


def test_secrets_simple_definitions(tmp_path):
    """The legacy plain value forms keep creating the application secret and a plain secret volume"""
    manifests = render_with_secrets(tmp_path, 'test_secrets_simple_definitions', {
        'unsecureSecret': 'a value',
        'secureSecret': None,
        'random-static-secret': '',
        'random-dynamic-secret': '?',
    })

    secret = find_manifest(manifests, 'Secret', 'myapp')
    assert secret['stringData']['unsecureSecret'] == 'a value'
    # rendering happens without a cluster, so this is always a first install:
    # empty and null values are randomly generated, ? is refreshed at every upgrade
    assert len(secret['stringData']['secureSecret']) == 20
    assert len(secret['stringData']['random-static-secret']) == 20
    assert secret['stringData']['random-dynamic-secret'] == '?'

    assert secrets_volume(manifests) == {'name': 'secrets', 'secret': {'secretName': 'myapp'}}


def test_secrets_rich_definition_defaults_to_cloudharness(tmp_path):
    """Without a manager, the rich form behaves exactly like the plain form"""
    manifests = render_with_secrets(tmp_path, 'test_secrets_rich_definition_defaults_to_cloudharness', {
        'withDefault': {'default': 'a value'},
        'explicitManager': {'manager': 'cloudharness', 'default': '?'},
        'noDefault': {'manager': 'cloudharness'},
    })

    secret = find_manifest(manifests, 'Secret', 'myapp')
    assert secret['stringData']['withDefault'] == 'a value'
    assert secret['stringData']['explicitManager'] == '?'
    assert len(secret['stringData']['noDefault']) == 20
    # the rich form must never be rendered as an unrecognized value
    assert not any('formatnotrecognized' in key for key in secret['stringData'])

    assert secrets_volume(manifests) == {'name': 'secrets', 'secret': {'secretName': 'myapp'}}


def test_secrets_unmanaged(tmp_path):
    """An explicitly null manager creates nothing: the secret is expected to exist already"""
    manifests = render_with_secrets(tmp_path, 'test_secrets_unmanaged', {
        'existing': {'manager': None},
    })

    assert not find_manifests(manifests, 'Secret', 'myapp'), "no secret must be created for unmanaged secrets"
    # mounted as optional: a missing secret must not block the pod from starting
    assert secrets_volume(manifests) == {'name': 'secrets', 'secret': {'secretName': 'myapp', 'optional': True}}


def test_secrets_unmanaged_mixed_with_cloudharness(tmp_path):
    """Unmanaged secrets are simply left out of the application secret"""
    manifests = render_with_secrets(tmp_path, 'test_secrets_unmanaged_mixed_with_cloudharness', {
        'managed': 'a value',
        'existing': {'manager': None},
    })

    secret = find_manifest(manifests, 'Secret', 'myapp')
    assert secret['stringData']['managed'] == 'a value'
    assert 'existing' not in secret['stringData']
    # the whole secret is mounted, so the out of band entry shows up as well
    assert secrets_volume(manifests) == {'name': 'secrets', 'secret': {'secretName': 'myapp'}}


def test_secrets_onepassword_manager(tmp_path):
    manifests = render_with_secrets(tmp_path, 'test_secrets_onepassword_manager', {
        'opSecret': {'manager': 'onepassword', 'path': 'vaults/my-vault/items/my-item'},
        'opField': {'manager': 'onepassword', 'path': 'my-item', 'field': 'credential'},
    }, secretmanagers={'onepassword': {'vault': 'default-vault'}})

    item = find_manifest(manifests, 'OnePasswordItem', 'myapp-opsecret')
    assert item['apiVersion'] == 'onepassword.com/v1'
    assert item['spec']['itemPath'] == 'vaults/my-vault/items/my-item'

    # the item name alone is completed with the globally configured vault
    item = find_manifest(manifests, 'OnePasswordItem', 'myapp-opfield')
    assert item['spec']['itemPath'] == 'vaults/default-vault/items/my-item'

    assert not find_manifests(manifests, 'Secret', 'myapp'), "externally managed secrets are not created by CloudHarness"

    assert secrets_volume(manifests) == {
        'name': 'secrets',
        'projected': {
            'sources': [
                {'secret': {'name': 'myapp', 'optional': True}},
                {'secret': {'name': 'myapp-opfield', 'items': [{'key': 'credential', 'path': 'opField'}]}},
                {'secret': {'name': 'myapp-opsecret', 'items': [{'key': 'password', 'path': 'opSecret'}]}},
            ]
        }
    }


def test_secrets_aws_manager(tmp_path):
    manifests = render_with_secrets(tmp_path, 'test_secrets_aws_manager', {
        'awsSecret': {'manager': 'aws', 'arn': 'arn:aws:secretsmanager:eu-west-1:1:secret:mine', 'property': 'password'},
    }, secretmanagers={'aws': {'store': 'aws-store', 'refreshInterval': '30m'}})

    external = find_manifest(manifests, 'ExternalSecret', 'myapp-awssecret')
    assert external['apiVersion'] == 'external-secrets.io/v1beta1'
    assert external['spec']['secretStoreRef'] == {'name': 'aws-store', 'kind': 'ClusterSecretStore'}
    assert external['spec']['refreshInterval'] == '30m'
    assert external['spec']['target']['name'] == 'myapp-awssecret'
    assert external['spec']['data'] == [{
        'secretKey': 'value',
        'remoteRef': {'key': 'arn:aws:secretsmanager:eu-west-1:1:secret:mine', 'property': 'password'},
    }]

    assert secrets_volume(manifests) == {
        'name': 'secrets',
        'projected': {
            'sources': [
                {'secret': {'name': 'myapp', 'optional': True}},
                {'secret': {'name': 'myapp-awssecret', 'items': [{'key': 'value', 'path': 'awsSecret'}]}},
            ]
        }
    }


def test_secrets_aws_manager_version(tmp_path):
    """A `version` setting pins the secret to a VersionStage or VersionId"""
    manifests = render_with_secrets(tmp_path, 'test_secrets_aws_manager_version', {
        'awsSecret': {'manager': 'aws', 'arn': 'arn:aws:secretsmanager:eu-west-1:1:secret:mine', 'version': 'AWSPREVIOUS'},
    }, secretmanagers={'aws': {'store': 'aws-store'}})

    external = find_manifest(manifests, 'ExternalSecret', 'myapp-awssecret')
    assert external['spec']['data'] == [{
        'secretKey': 'value',
        'remoteRef': {'key': 'arn:aws:secretsmanager:eu-west-1:1:secret:mine', 'version': 'AWSPREVIOUS'},
    }]


def test_secrets_mixed_managers(tmp_path):
    """CloudHarness and externally managed secrets are exposed in the same directory"""
    manifests = render_with_secrets(tmp_path, 'test_secrets_mixed_managers', {
        'local': 'a value',
        'opSecret': {'manager': 'onepassword', 'path': 'vaults/my-vault/items/my-item', 'default': 'ignored locally'},
    })

    secret = find_manifest(manifests, 'Secret', 'myapp')
    assert secret['stringData']['local'] == 'a value'
    assert 'opSecret' not in secret['stringData'], "the value of an externally managed secret is never written in the chart"

    assert find_manifests(manifests, 'OnePasswordItem', 'myapp-opsecret')
    assert secrets_volume(manifests) == {
        'name': 'secrets',
        'projected': {
            'sources': [
                {'secret': {'name': 'myapp'}},
                {'secret': {'name': 'myapp-opsecret', 'items': [{'key': 'password', 'path': 'opSecret'}]}},
            ]
        }
    }


def test_secrets_unknown_manager_setting_fails(tmp_path):
    with pytest.raises(subprocess.CalledProcessError) as error:
        render_with_secrets(tmp_path, 'test_secrets_unknown_manager_setting_fails', {
            'opSecret': {'manager': 'onepassword'},
        })
    assert "requires a 'path'" in error.value.stderr


def test_secrets_of_a_dependency_are_mounted(tmp_path):
    """Applications see the secrets of their dependencies, whatever the manager"""
    def depend_on_myapp(values):
        values['apps']['dependantapp']['harness']['deployment']['auto'] = True
        values['apps']['dependantapp']['harness']['dependencies']['hard'] = ['myapp']

    manifests = render_with_secrets(tmp_path, 'test_secrets_of_a_dependency_are_mounted', {
        'local': 'a value',
        'opSecret': {'manager': 'onepassword', 'path': 'vaults/my-vault/items/my-item'},
    }, include=['myapp', 'dependantapp'], patch=depend_on_myapp)

    deployment = find_manifest(manifests, 'Deployment', 'dependantapp')
    volumes = [v for v in deployment['spec']['template']['spec']['volumes'] if v['name'] == 'cloudharness-myapp']
    assert volumes == [{
        'name': 'cloudharness-myapp',
        'projected': {
            'sources': [
                {'secret': {'name': 'myapp'}},
                {'secret': {'name': 'myapp-opsecret', 'items': [{'key': 'password', 'path': 'opSecret'}]}},
            ]
        }
    }]

    mounts = [m for m in deployment['spec']['template']['spec']['containers'][0]['volumeMounts']
              if m['name'] == 'cloudharness-myapp']
    assert mounts[0]['mountPath'] == '/opt/cloudharness/resources/secrets/myapp'


def test_secrets_definitions_survive_the_values_generation(tmp_path):
    """The rich form must reach the chart untouched, an explicitly null manager included:
    losing it would silently turn an unmanaged secret into a CloudHarness managed one"""
    out_folder = tmp_path / 'test_secrets_definitions_survive_the_values_generation'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='secrets', local=False, include=["myapp"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts', ignore_errors=True)
    values_path = helm_path / 'values.yaml'
    with open(values_path) as values_file:
        values = yaml.load(values_file)
    secrets = values['apps']['myapp']['harness']['secrets']
    assert 'manager' in secrets['unmanagedSecret'], "the explicitly null manager must be kept"
    assert secrets['unmanagedSecret']['manager'] is None
    assert secrets['richSecret'] == {
        'manager': 'onepassword',
        'path': 'vaults/my-vault/items/my-item',
        'default': 'a local value',
    }

    values['apps']['myapp']['harness']['deployment']['auto'] = True
    with open(values_path, 'w') as values_file:
        yaml.dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    secret = find_manifest(manifests, 'Secret', 'myapp')
    assert secret['stringData']['plainSecret'] == 'a value'
    assert 'unmanagedSecret' not in secret['stringData'], "unmanaged secrets are never created"
    assert 'richSecret' not in secret['stringData'], "externally managed secrets are never created"
    assert find_manifests(manifests, 'OnePasswordItem', 'myapp-richsecret')


def secret_values(secrets):
    return {KEY_APPS: {'myapp': {KEY_HARNESS: {'secrets': secrets}}}}


def test_validate_secrets_accepts_both_definition_forms():
    validate_secrets(secret_values({
        'plain': 'a value',
        'tobeset': None,
        'static': '',
        'dynamic': '?',
        'rich': {'default': 'a value'},
        'managed': {'manager': 'onepassword', 'path': 'vaults/v/items/i'},
        'unmanaged': {'manager': None},
        # unknown managers are valid: applications can contribute their own
        'custom': {'manager': 'my-own-manager', 'whatever': {'nested': True}},
    }))
    validate_secrets(secret_values({}))
    validate_secrets(secret_values(None))


def test_validate_secrets_rejects_malformed_definitions():
    with pytest.raises(ValuesValidationException, match="secret alist of application myapp"):
        validate_secrets(secret_values({'alist': ['a', 'b']}))

    with pytest.raises(ValuesValidationException, match="`manager` must be"):
        validate_secrets(secret_values({'badmanager': {'manager': {'name': 'onepassword'}}}))

    with pytest.raises(ValuesValidationException, match="`default` must be"):
        validate_secrets(secret_values({'baddefault': {'default': {'a': 'b'}}}))

    with pytest.raises(ValuesValidationException, match="expected a map of secret definitions"):
        validate_secrets(secret_values(['a', 'b']))


def test_collect_helm_values_source_images_merge(tmp_path):
    out_path = tmp_path / 'test_collect_helm_values_source_images_merge'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_path,
                               include=["samples", "myapp"], domain="my.local",
                               namespace='test', env='nreg', local=False, tag=1, registry='reg')

    source_images = values.get("source_images")
    assert source_images["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert "NODE" in source_images


def test_collect_helm_values_source_images_merge_no_include(tmp_path):
    out_path = tmp_path / 'test_collect_helm_values_source_images_merge'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_path, domain="my.local",
                               namespace='test', env='nreg', local=False, tag=1, registry='reg')

    source_images = values.get("source_images")
    assert source_images["KEYCLOAK"] == "myregistry.myapp:15.3"
    assert "NODE" in source_images


def test_instances_expand_into_applications(tmp_path):
    """An instance is deployed as an application of its own, inheriting the parent's configuration."""
    out_folder = tmp_path / 'test_instances_expand_into_applications'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples'],
                               domain="my.local", namespace='test', env='dev', local=False, tag=1, registry='reg')

    apps = values[KEY_APPS]
    assert 'samples-instance1' in apps, 'including an application includes its instances'
    instance = apps['samples-instance1']
    parent = apps['samples']

    # Its own host: the parent's subdomain and aliases are never inherited
    assert instance[KEY_HARNESS]['subdomain'] == 'samples1'
    assert not instance[KEY_HARNESS]['aliases']
    assert parent[KEY_HARNESS]['subdomain'] == 'www'
    assert parent[KEY_HARNESS]['aliases'] == ['samples']

    # Its own resources
    assert instance[KEY_HARNESS]['name'] == 'samples-instance1'
    assert instance[KEY_HARNESS]['service']['name'] == 'samples-instance1'
    assert instance[KEY_HARNESS][KEY_DEPLOYMENT]['name'] == 'samples-instance1'
    assert instance[KEY_HARNESS][KEY_DATABASE]['name'] == 'samples-instance1-db'
    assert instance[KEY_HARNESS][KEY_DEPLOYMENT]['volume']['name'] == \
        'samples-instance1-my-shared-volume', 'an instance must not mount the parent claim'
    assert parent[KEY_HARNESS][KEY_DEPLOYMENT]['volume']['name'] == 'my-shared-volume'

    # The parent's image, built once
    assert instance['build'] is False
    assert instance['image'] == parent['image']
    assert instance[KEY_HARNESS][KEY_DEPLOYMENT]['image'] == parent[KEY_HARNESS][KEY_DEPLOYMENT]['image']
    assert not instance[KEY_TASK_IMAGES]

    # Inherited configuration, with the instance's own values merged over it
    assert instance[KEY_HARNESS]['secured'] == parent[KEY_HARNESS]['secured']
    assert instance[KEY_HARNESS][KEY_DEPLOYMENT]['replicas'] == 1
    assert parent[KEY_HARNESS][KEY_DEPLOYMENT]['replicas'] == 2
    assert instance[KEY_HARNESS]['envmap']['ENVIRONMENT_TEST_B'] == 123


def test_instances_expand_without_include(tmp_path):
    out_folder = tmp_path / 'test_instances_expand_without_include'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                               namespace='test', env='dev', local=False, tag=1, registry='reg')

    instance = values[KEY_APPS]['samples-instance1']
    assert instance[KEY_HARNESS]['subdomain'] == 'samples1'
    assert instance['build'] is False
    assert instance['image'] == values[KEY_APPS]['samples']['image']


def test_instance_excluded_individually(tmp_path):
    """A single instance is left out with --exclude, without affecting its parent."""
    out_folder = tmp_path / 'test_instance_excluded_individually'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples'],
                               exclude=['samples-instance1'], domain="my.local", namespace='test', env='dev',
                               local=False, tag=1, registry='reg')

    assert 'samples-instance1' not in values[KEY_APPS]
    assert 'samples' in values[KEY_APPS]
    # an excluded instance leaves no collected files behind either
    assert not (out_folder / HELM_CHART_PATH / 'resources' / 'samples-instance1').exists()


def test_instance_include_pulls_in_its_parent(tmp_path):
    """Including an instance alone deploys the application it inherits its image from too."""
    out_folder = tmp_path / 'test_instance_include_pulls_in_its_parent'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder,
                               include=['samples-instance1'], domain="my.local", namespace='test', env='dev',
                               local=False, tag=1, registry='reg')

    assert 'samples-instance1' in values[KEY_APPS]
    assert 'samples' in values[KEY_APPS]
    assert values[KEY_APPS]['samples-instance1']['image'] == values[KEY_APPS]['samples']['image']


def test_instance_resources_are_overlaid_on_the_application(tmp_path):
    """An instance's resources override the application's file by file, and it inherits the rest."""
    out_folder = tmp_path / 'test_instance_resources'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples'],
                      domain="my.local", namespace='test', env='dev', local=False, tag=1, registry='reg')

    helm_path = out_folder / HELM_CHART_PATH
    instance_resources = helm_path / 'resources' / 'samples-instance1'
    assert (instance_resources / 'example.yaml').exists()
    assert (instance_resources / 'myConfig.json').exists(), \
        'a resource the instance does not override is inherited'

    shutil.rmtree(helm_path / 'charts', ignore_errors=True)
    manifests = render_helm_chart(helm_path)

    # the overridden resource carries the instance's content...
    overridden = find_manifest(manifests, 'ConfigMap', 'samples-instance1-example')
    assert 'an instance overridden' in overridden['data']['important_config.yaml']
    # ...the inherited one the application's, and it is not empty (the configmap is looked up
    # by deployment name, so a missing instance directory renders an empty value)
    inherited = find_manifest(manifests, 'ConfigMap', 'samples-instance1-my-config')
    parent_config = find_manifest(manifests, 'ConfigMap', 'samples-my-config')
    assert inherited['data']['myConfig.json'].strip()
    assert inherited['data'] == parent_config['data']
    # the application keeps its own
    parent = find_manifest(manifests, 'ConfigMap', 'samples-example')
    assert 'an instance overridden' not in parent['data']['important_config.yaml']


def test_instance_templates_are_overlaid_on_the_application(tmp_path):
    """An instance's helm templates are collected over the application's."""
    out_folder = tmp_path / 'test_instance_templates'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['myapp'],
                      domain="my.local", namespace='test', env='dev', local=False, tag=1, registry='reg')

    helm_path = out_folder / HELM_CHART_PATH
    assert (helm_path / 'templates' / 'myapp-inst1' / 'mytemplate.yaml').exists()
    assert (helm_path / 'resources' / 'myapp-inst1' / 'instanceonly.txt').exists()
    assert (helm_path / 'resources' / 'myapp-inst1' / 'aresource.txt').exists()

    shutil.rmtree(helm_path / 'charts', ignore_errors=True)
    manifests = render_helm_chart(helm_path)
    rendered = find_manifest(manifests, 'ConfigMap', 'myapp-inst1-instance-template')
    assert rendered['data']['subdomain'] == 'myinstance'


def test_instance_does_not_inherit_the_parent_connect_string(tmp_path):
    """A connection string points at one database: an instance never inherits the parent's."""
    out_folder = tmp_path / 'test_instance_connect_string'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples'],
                               domain="my.local", namespace='test', env='dev', local=False, tag=1, registry='reg')

    instance_db = values[KEY_APPS]['samples-instance1'][KEY_HARNESS][KEY_DATABASE]
    parent_db = values[KEY_APPS]['samples'][KEY_HARNESS][KEY_DATABASE]
    assert instance_db['connect_string'] != parent_db['connect_string']

    # an instance that declares none is left with an empty one, to be supplied per instance at
    # deploy time, rather than silently connecting to the parent's database
    parent = {KEY_HARNESS: {KEY_DATABASE: {'type': 'postgres', 'connect_string': 'parent connection'}}}
    instance = build_instance_values(parent, 'myapp', 'i1', {KEY_HARNESS: {'subdomain': 'myapp1'}})
    assert instance[KEY_HARNESS][KEY_DATABASE]['connect_string'] == ''
    assert parent[KEY_HARNESS][KEY_DATABASE]['connect_string'] == 'parent connection'


def test_instance_renders_its_own_manifests(tmp_path):
    """The instance gets the full set of manifests on its own subdomain, backed by its own workload."""
    out_folder = tmp_path / 'test_instance_renders_its_own_manifests'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['samples'],
                      domain="my.local", namespace='test', env='dev', local=False, tag=1, registry='reg')

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts', ignore_errors=True)
    manifests = render_helm_chart(helm_path)

    statefulset = find_manifest(manifests, 'StatefulSet', 'samples-instance1')
    find_manifest(manifests, 'Service', 'samples-instance1')

    containers = statefulset['spec']['template']['spec']['containers']
    app_container = next(c for c in containers if c['name'] == 'samples-instance1')
    env = {e['name']: e.get('value') for e in app_container['env']}
    assert env['CH_CURRENT_APP_NAME'] == 'samples-instance1', \
        'the instance must read its own configuration, not the parent one'

    # Its own claim: sharing the parent's would give the instance the parent's data
    claims = [c['metadata']['name'] for c in statefulset['spec'].get('volumeClaimTemplates', [])]
    parent_claims = [c['metadata']['name']
                     for c in find_manifest(manifests, 'StatefulSet', 'samples')['spec'].get('volumeClaimTemplates', [])]
    assert claims and not set(claims) & set(parent_claims)

    # Its own database secret
    instance_secret = find_manifest(manifests, 'Secret', 'samples-instance1-db')
    parent_secret = find_manifest(manifests, 'Secret', 'samples-db')
    assert instance_secret['stringData']['connect_string'] != parent_secret['stringData']['connect_string']

    # Its own host, served by its own gatekeeper
    hosts = {}
    for manifest in manifests:
        if manifest.get('kind') != 'Ingress':
            continue
        for rule in manifest['spec']['rules']:
            for path in rule['http']['paths']:
                hosts.setdefault(rule['host'], set()).add(path['backend']['service']['name'])

    assert 'samples1.my.local' in hosts
    assert 'samples-instance1' in hosts['samples1.my.local']
    assert 'samples1-gk' in hosts['samples1.my.local']
    # the parent keeps its own hosts, and the instance never serves them
    assert 'samples-instance1' not in hosts['samples.my.local']
    assert 'samples-instance1' not in hosts['www.my.local']

    gatekeeper = find_manifest(manifests, 'ConfigMap', 'samples1-gk')
    proxy_config = yaml.load(gatekeeper['data']['proxy.yml'])
    assert proxy_config['redirection-url'] == 'https://samples1.my.local'
    assert proxy_config['upstream-url'].startswith('http://samples-instance1.')


def test_instance_colliding_with_an_application_is_rejected(tmp_path):
    """An instance and an application under the same key would be merged into one, whichever
    root path declares each of them."""
    first, second = tmp_path / 'first', tmp_path / 'second'
    (first / APPS_PATH / 'myapp' / 'deploy' / INSTANCES_PATH / 'other').mkdir(parents=True)
    (second / APPS_PATH / 'myapp-other' / 'deploy').mkdir(parents=True)

    check_instance_collisions([first])
    check_instance_collisions([second])
    with pytest.raises(ValuesValidationException, match='myapp-other'):
        check_instance_collisions([first, second])
    with pytest.raises(ValuesValidationException, match='myapp-other'):
        check_instance_collisions([second, first])
    check_instance_collisions([first, second], exclude=['myapp-other'])

    # the check is made by the generator before anything is read
    with pytest.raises(ValuesValidationException, match='myapp-other'):
        create_helm_chart([CLOUDHARNESS_ROOT, first, second], output_path=tmp_path / 'out', include=['myapp'],
                          domain="my.local", namespace='test', local=False, tag=1, registry='reg')


def test_instance_directory_colliding_with_a_task_is_rejected(tmp_path):
    """Task image ownership is resolved by longest name prefix, so an instance named `print` on
    an application owning `myapp-print-file` would take the image over and it would never build.
    The collision is caught when instances are collected, before anything reads task images."""
    app_path = tmp_path / APPS_PATH / 'myapp'
    (app_path / 'tasks' / 'print-file').mkdir(parents=True)
    instance_path = app_path / 'deploy' / INSTANCES_PATH / 'print'
    instance_path.mkdir(parents=True)
    (instance_path / 'values.yaml').write_text('harness:\n  subdomain: myprint\n')

    with pytest.raises(ValuesValidationException, match='myapp-print-file'):
        collect_instances('myapp', [tmp_path])

    assert resolve_task_image_owner('myapp-print-file', {'myapp', 'myapp-print'}) == 'myapp-print', \
        'the prefix match this guards against'


def test_collect_instances_skips_hidden_directories(tmp_path):
    instances_dir = tmp_path / APPS_PATH / 'myapp' / 'deploy' / INSTANCES_PATH
    (instances_dir / '.hidden').mkdir(parents=True)
    (instances_dir / 'real').mkdir(parents=True)
    (instances_dir / 'real' / 'values.yaml').write_text('harness:\n  subdomain: real\n')

    assert set(collect_instances('myapp', [tmp_path])) == {'real'}


def test_collect_instances_of_an_application_without_any(tmp_path):
    (tmp_path / APPS_PATH / 'myapp' / 'deploy').mkdir(parents=True)
    assert collect_instances('myapp', [tmp_path]) == {}
    assert collect_instances('missing', [tmp_path]) == {}, 'an application absent from a root declares nothing there'


def test_collect_instances_merges_the_roots_declaring_the_same_instance(tmp_path):
    for root, replicas in (('first', 1), ('second', 2)):
        instance_path = tmp_path / root / APPS_PATH / 'myapp' / 'deploy' / INSTANCES_PATH / 'inst'
        instance_path.mkdir(parents=True)
        (instance_path / 'values.yaml').write_text(f'harness:\n  deployment:\n    replicas: {replicas}\n{root}: true\n')

    instances = collect_instances('myapp', [tmp_path / 'first', tmp_path / 'second'])
    assert instances['inst'][KEY_HARNESS][KEY_DEPLOYMENT]['replicas'] == 2, 'a later root wins'
    assert instances['inst']['first'] and instances['inst']['second'], 'what a root does not override is kept'


def test_instance_values_replace_parent_lists():
    """An instance's lists replace the parent's rather than adding to them.

    `uri_role_mapping` is what the gatekeeper whitelists, so the two semantics differ in
    what an instance leaves open: pinned here because the merge rule is documented.
    """
    parent_mapping = [
        {'uri': '/', 'white-listed': True},
        {'uri': '/api/ping', 'white-listed': True},
    ]
    parent_app = {
        KEY_HARNESS: {
            'uri_role_mapping': parent_mapping,
            'env': [{'name': 'WORKERS', 'value': '3'}],
            'envmap': {'A': 'parent', 'B': 'kept'},
        }
    }
    instance = build_instance_values(parent_app, 'myapp', 'i1', {
        KEY_HARNESS: {
            'subdomain': 'myapp1',
            'uri_role_mapping': [{'uri': '/*', 'roles': ['administrator']}],
            'envmap': {'A': 'instance'},
        }
    })[KEY_HARNESS]
    parent = parent_app[KEY_HARNESS]

    # lists are replaced as a whole
    assert instance['uri_role_mapping'] == [{'uri': '/*', 'roles': ['administrator']}]
    assert parent['uri_role_mapping'] == parent_mapping
    # a list the instance does not override is inherited
    assert instance['env'] == [{'name': 'WORKERS', 'value': '3'}]
    # mappings are merged key by key
    assert instance['envmap'] == {'A': 'instance', 'B': 'kept'}
    assert parent['envmap'] == {'A': 'parent', 'B': 'kept'}


def test_instances_are_collected_with_the_application_they_belong_to(tmp_path):
    """An instance is added to the deployment as soon as its application is read: the values
    collected from a root path hold the instances next to the applications, derived from the
    application's values as merged so far."""
    generator = CloudHarnessHelm([CLOUDHARNESS_ROOT, RESOURCES],
                                 output_path=tmp_path / 'test_instances_collected',
                                 domain="my.local", namespace='test', env=['dev'],
                                 local=False, tag=1, registry='reg')
    merged_so_far = {KEY_APPS: {'myapp': {KEY_HARNESS: {'secured': True, 'subdomain': 'earlier'}}}}

    values = generator.collect_app_values(Path(RESOURCES) / APPS_PATH, helm_values=merged_so_far)

    instance = values['myapp-inst1']
    assert instance[KEY_HARNESS]['subdomain'] == 'myinstance'
    assert instance[KEY_HARNESS]['secured'] is True, 'derived from the application merged so far'
    assert instance['a'] == 'instance-dev-b', 'with the instance values on top'
    assert instance['build'] is False
    assert 'accounts-inst1' not in values, 'applications declaring no instance get none'
    # nothing in the values tells the instance apart: the directories are the only record
    assert instance_names('myapp', [RESOURCES]) == {'inst1'}
    assert instance_names('accounts', [RESOURCES]) == set()


def test_values_vocabulary_is_re_exported():
    """The values keys live in `constants` and the validation exception lives in `common_types`,
    and both are read from `configurationgenerator` by the other cli tools and by these tests:
    dropping the re-export breaks them with an ImportError far from where it was caused."""
    from ch_cli_tools import common_types, constants

    for name in ('KEY_HARNESS', 'KEY_SERVICE', 'KEY_DATABASE', 'KEY_DEPLOYMENT', 'KEY_APPS',
                 'KEY_TASK_IMAGES', 'KEY_TEST_IMAGES'):
        assert getattr(configurationgenerator, name) is getattr(constants, name), \
            f"{name} must stay importable from configurationgenerator"

    assert configurationgenerator.ValuesValidationException is common_types.ValuesValidationException, \
        "ValuesValidationException must stay importable from configurationgenerator"


def test_instance_subdomain_defaults_to_its_directory_name():
    """Creating the directory is enough to reach an instance: without a subdomain of its own it
    answers on its name. An explicit null opts out of the ingress."""
    def subdomain_of(instance_values):
        parent = {KEY_HARNESS: {'subdomain': 'www', 'aliases': ['samples']}}
        return build_instance_values(parent, 'samples', 'instance1', instance_values)[KEY_HARNESS].get('subdomain', '<absent>')

    assert subdomain_of({}) == 'instance1'
    assert subdomain_of({KEY_HARNESS: {'replicas': 2}}) == 'instance1'
    assert subdomain_of({KEY_HARNESS: {'subdomain': 'samples1'}}) == 'samples1'
    assert subdomain_of({KEY_HARNESS: {'subdomain': None}}) is None


def test_instance_values_precedence(tmp_path):
    """Values are layered instance env > instance > application env > application.

    The `myapp` fixture sets `a` in all four files and `dev` only in the application's
    environment values, so the winner and the inheritance are both visible.
    """
    out_folder = tmp_path / 'test_instance_values_precedence'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['myapp'],
                               domain="my.local", namespace='test', env='dev', local=False, tag=1, registry='reg')

    instance = values[KEY_APPS]['myapp-inst1']
    parent = values[KEY_APPS]['myapp']

    # the instance's environment values win over everything
    assert instance['a'] == 'instance-dev-b'
    assert instance[KEY_HARNESS][KEY_DEPLOYMENT]['replicas'] == 4, \
        'the instance values-dev.yaml overrides its values.yaml'
    # what no instance file sets is inherited, environment values included
    assert instance['dev'] is True
    # the application keeps its own
    assert parent['a'] == 'b'
    assert parent[KEY_HARNESS]['subdomain'] == 'mysubdomain'


def test_instance_without_env_values_still_layers_over_the_application(tmp_path):
    """Without the environment, the instance's values.yaml is the top of the chain."""
    out_folder = tmp_path / 'test_instance_values_precedence_noenv'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, include=['myapp'],
                               domain="my.local", namespace='test', local=False, tag=1, registry='reg')

    instance = values[KEY_APPS]['myapp-inst1']
    assert instance['a'] == 'instance-b'
    assert instance[KEY_HARNESS][KEY_DEPLOYMENT]['replicas'] == 3
    assert 'dev' not in instance


def test_instance_inherits_the_application_merged_across_roots(tmp_path):
    """An instance inherits the application's final configuration, not the one of the root its
    directory happens to live in.

    An instance is derived again in every root path that reads its application, from the
    application as merged up to that root and the instance's values from every root: a
    scaffolding overriding an application reaches its instances, and the instance's own values
    still win over it.
    """
    overriding_root = tmp_path / 'overriding_root'
    app_deploy = overriding_root / APPS_PATH / 'myapp' / 'deploy'
    app_deploy.mkdir(parents=True)
    (app_deploy / 'values.yaml').write_text(
        'harness:\n  secured: true\n  deployment:\n    port: 9999\n    replicas: 1\n')

    out_folder = tmp_path / 'test_instance_inherits_merged'
    values = create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES, overriding_root], output_path=out_folder,
                               include=['myapp'], domain="my.local", namespace='test', env='dev',
                               local=False, tag=1, registry='reg')

    # the instance is declared in RESOURCES, the override comes from a later root
    instance = values[KEY_APPS]['myapp-inst1'][KEY_HARNESS]
    assert values[KEY_APPS]['myapp'][KEY_HARNESS][KEY_DEPLOYMENT]['port'] == 9999
    assert instance[KEY_DEPLOYMENT]['port'] == 9999
    assert instance['secured'] is True
    # and what the instance sets for itself still wins over the later root's application values
    assert instance['subdomain'] == 'myinstance'
    assert instance[KEY_DEPLOYMENT]['replicas'] == 4
    assert values[KEY_APPS]['myapp'][KEY_HARNESS][KEY_DEPLOYMENT]['replicas'] == 1
