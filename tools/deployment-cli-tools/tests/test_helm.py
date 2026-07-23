from ch_cli_tools.helm import *
from ch_cli_tools.configurationgenerator import *
from ch_cli_tools.preprocessing import preprocess_build_overrides, generate_hash_based_image_tags
import pytest
import shutil
import subprocess

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
    return [manifest for manifest in yaml.safe_load_all(completed.stdout) if manifest]


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
        values = yaml.safe_load(values_file)
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
        yaml.safe_dump(values, values_file)

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
        yaml.safe_dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    cluster = find_manifest(manifests, 'Cluster', db_name)
    assert 'postgresql' not in cluster['spec']

    postgres.pop('parameters')
    with open(values_path, 'w') as values_file:
        yaml.safe_dump(values, values_file)

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
        values = yaml.safe_load(values_file)

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
        yaml.safe_dump(values, values_file)

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
        yaml.safe_dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    sts = find_manifest(manifests, 'StatefulSet', dep_name)
    assert sts['spec']['serviceName'] == service_name
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
        yaml.safe_dump(values, values_file)

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
        yaml.safe_dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    sts = find_manifest(manifests, 'StatefulSet', dep_name)
    assert 'volumeClaimTemplates' not in sts['spec']
    claims = [v['persistentVolumeClaim']['claimName']
              for v in sts['spec']['template']['spec']['volumes'] if 'persistentVolumeClaim' in v]
    assert 'myapp-data' in claims


def test_statefulset_leader_service(tmp_path):
    out_folder = tmp_path / 'test_statefulset_leader_service'
    create_helm_chart([CLOUDHARNESS_ROOT, RESOURCES], output_path=out_folder, domain="my.local",
                      env='withpostgres', local=False, include=["myapp"], exclude=["legacy"])

    helm_path = out_folder / HELM_CHART_PATH
    shutil.rmtree(helm_path / 'charts')
    values_path = helm_path / 'values.yaml'
    with open(values_path, 'r') as values_file:
        values = yaml.safe_load(values_file)

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
        yaml.safe_dump(values, values_file)

    manifests = render_helm_chart(helm_path)
    assert not any(m for m in manifests
                  if m.get('kind') == 'Service' and m.get('metadata', {}).get('name') == rw_name)
    assert not any(p for p in ingress_paths(manifests)
                  if p['backend']['service']['name'] == rw_name)

    harness['deployment']['statefulset'] = True
    with open(values_path, 'w') as values_file:
        yaml.safe_dump(values, values_file)

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
    chart = yaml.safe_load(open(chart_path, 'r'))
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
