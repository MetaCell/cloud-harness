"""Notice, this test needs a fully operating kubernetes with argo environment in the container running the test"""
import requests
import yaml

from cloudharness.workflows.utils import is_accounts_present
from .test_env import set_test_environment

set_test_environment()

from cloudharness.workflows import operations, tasks
from cloudharness import set_debug
from cloudharness.workflows import argo
from cloudharness.utils.config import CloudharnessConfig

set_debug()

execute = False
verbose = True

assert 'registry' in CloudharnessConfig.get_configuration()


def test_sync_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    task = tasks.PythonTask('my-task', f)
    assert 'registry' in CloudharnessConfig.get_configuration()
    op = operations.DistributedSyncOperation('test-sync-op-', task)
    print('\n', yaml.dump(op.to_workflow()))
    
    if execute:
        print(op.execute())


def test_pipeline_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.PipelineOperation('test-pipeline-op-', (tasks.PythonTask('step1', f), tasks.PythonTask('step2', f)))
    print('\n', yaml.dump(op.to_workflow()))
    if execute:
        op.execute()


def test_parallel_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)))
    print('\n', yaml.dump(op.to_workflow()))
    if execute:
        op.execute()


def test_simpledag_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    # p3 runs after p1 and p2 finish
    op = operations.SimpleDagOperation('test-dag-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)),
                                       tasks.PythonTask('p3', f))
    print('\n', yaml.dump(op.to_workflow()))
    if execute:
        print(op.execute())


def test_custom_task_workflow():
    task = operations.CustomTask('download-file', 'workflows-extract-download', url='https://www.bing.com')
    op = operations.PipelineOperation('test-custom-op-', (task,))
    print('\n', yaml.dump(op.to_workflow()))
    if execute:
        print(op.execute())


def test_custom_connected_task_workflow():
    shared_directory = '/mnt/shared'
    task_write = operations.CustomTask('download-file', 'workflows-extract-download',
                                       shared_directory=shared_directory,
                                       url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')
    task_print = operations.CustomTask('print-file', 'workflows-print-file', shared_directory=shared_directory,
                                       file_path=shared_directory + '/README.md')
    op = operations.PipelineOperation('test-custom-connected-op-', (task_write, task_print),
                                      shared_directory=shared_directory, shared_volume_size=100)
    # op.execute()
    print('\n', yaml.dump(op.to_workflow()))
    if execute:
        print(op.execute())


def test_single_task_shared():
    shared_directory = 'myclaim:/mnt/shared'
    task_write = operations.CustomTask('download-file', 'workflows-extract-download',
                                       url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')
    op = operations.SingleTaskOperation('test-custom-connected-op-', task_write,
                                        shared_directory=shared_directory, shared_volume_size=100)
    wf = op.to_workflow()
    print('\n', yaml.dump(wf))

    accounts_offset = 1 if is_accounts_present() else 0
    assert len(op.volumes) == 1
    assert len(wf['spec']['volumes']) == 2 + accounts_offset
    assert wf['spec']['volumes'][1+accounts_offset]['persistentVolumeClaim']['claimName'] == 'myclaim'
    if accounts_offset == 1:
        assert wf['spec']['volumes'][1]['secret']['secretName'] == 'accounts'
    assert len(wf['spec']['templates'][0]['container']['volumeMounts']) == 2 + accounts_offset
    if execute:
        print(op.execute())

def test_single_task_shared_rwx():
    shared_directory = 'myclaim:/mnt/shared:rwx'
    task_write = operations.CustomTask('download-file', 'workflows-extract-download',
                                       url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')
    op = operations.SingleTaskOperation('test-custom-connected-op-', task_write,
                                        shared_directory=shared_directory, shared_volume_size=100)
    wf = op.to_workflow()
    print('\n', yaml.dump(wf))

    accounts_offset = 1 if is_accounts_present() else 0
    assert len(op.volumes) == 1
    assert len(wf['spec']['volumes']) == 2 + accounts_offset
    assert wf['spec']['volumes'][1+accounts_offset]['persistentVolumeClaim']['claimName'] == 'myclaim'
    if accounts_offset == 1:
        assert wf['spec']['volumes'][1]['secret']['secretName'] == 'accounts'
    assert len(wf['spec']['templates'][0]['container']['volumeMounts']) == 2 + accounts_offset

    assert not 'affinity' in wf['spec'], "Pod affinity should not be added for rwx volumes"

def test_single_task_shared_multiple():
    shared_directory = ['myclaim:/mnt/shared', 'myclaim2:/mnt/shared2:ro']
    task_write = operations.CustomTask('download-file', 'workflows-extract-download',
                                       url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')
    op = operations.SingleTaskOperation('test-custom-connected-op-', task_write,
                                        shared_directory=shared_directory)
    wf = op.to_workflow()
    print('\n', yaml.dump(wf))
    accounts_offset = 1 if is_accounts_present() else 0

    assert len(op.volumes) == 2
    assert len(wf['spec']['volumes']) == 3 + accounts_offset
    assert wf['spec']['volumes'][1+accounts_offset]['persistentVolumeClaim']['claimName'] == 'myclaim'
    assert len(wf['spec']['templates'][0]['container']['volumeMounts']) == 3 + accounts_offset

    assert wf['spec']['templates'][0]['container']['volumeMounts'][2+accounts_offset]['readonly']

    assert wf['spec']['templates'][0]['metadata']['labels']['usesvolume']

    assert 'affinity' in wf['spec']
    assert len(wf['spec']['affinity']['podAffinity'][
                   'requiredDuringSchedulingIgnoredDuringExecution']) == 2, "A pod affinity for each volume is expected"
    affinity_expr = \
        wf['spec']['affinity']['podAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][0]['labelSelector'][
            'matchExpressions'][0]
    assert affinity_expr['key'] == 'usesvolume'
    assert affinity_expr['values'][0] == 'myclaim'
    if execute:
        print(op.execute())


def test_single_task_shared_script():
    shared_directory = 'myclaim:/mnt/shared'
    task_write = tasks.BashTask('download-file', source="ls -la")
    op = operations.SingleTaskOperation('test-custom-connected-op-', task_write,
                                        shared_directory=shared_directory, shared_volume_size=100)
    wf = op.to_workflow()
    print('\n', yaml.dump(wf))
    accounts_offset = 1 if is_accounts_present() else 0

    assert len(op.volumes) == 1
    assert len(wf['spec']['volumes']) == 2+accounts_offset
    assert wf['spec']['volumes'][1+accounts_offset]['persistentVolumeClaim']['claimName'] == 'myclaim'
    assert len(wf['spec']['templates'][0]['script']['volumeMounts']) == 2+accounts_offset

    
    


def test_result_task_workflow():
    task_write = operations.CustomTask('download-file', 'workflows-extract-download',
                                       url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')

    op = operations.DistributedSyncOperationWithResults('test-sync-results-', task_write)

    # op.execute()
    print('\n', yaml.dump(op.to_workflow()))
    if execute:
        print(op.execute())


def test_get_workflows():
    if execute:
        assert len(argo.get_workflows())


def test_submit_workflow():
    WORKFLOW = 'https://raw.githubusercontent.com/argoproj/argo/v2.12.2/examples/dag-diamond-steps.yaml'

    resp = requests.get(WORKFLOW)
    manifest: dict = yaml.safe_load(resp.text)
    if execute:
        wf = argo.submit_workflow(manifest)
        assert wf
        assert wf.name


def test_get_workflow():
    if not execute:
        return
    WORKFLOW = 'https://raw.githubusercontent.com/argoproj/argo/v2.12.2/examples/dag-diamond-steps.yaml'

    resp = requests.get(WORKFLOW)
    manifest: dict = yaml.safe_load(resp.text)
    wf = argo.submit_workflow(manifest)
    wf = argo.get_workflow(wf.name)
    assert wf
    assert wf.name
    try:
        argo.get_workflow('riuhfsdhsdfsfisdf')
        assert 1 == 0  # not found raises exception
    except:
        pass


def test_get_workflow_logs():
    if not execute:
        return
    WORKFLOW = 'https://raw.githubusercontent.com/argoproj/argo/v2.12.2/examples/dag-diamond-steps.yaml'

    resp = requests.get(WORKFLOW)
    manifest: dict = yaml.safe_load(resp.text)
    wf = argo.submit_workflow(manifest)
    logs = argo.get_workflow_logs(wf.name)
    assert all(log for log in logs)


def test_workflow_with_context():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)),
                                      pod_context=operations.PodExecutionContext('a', 'b'))
    workflow = op.to_workflow()
    assert 'affinity' in workflow['spec']
    affinity_expr = workflow['spec']['affinity']['podAffinity']['preferredDuringSchedulingIgnoredDuringExecution'][0][
        'podAffinityTerm']['labelSelector']['matchExpressions'][0]
    assert affinity_expr['key'] == 'a'
    assert affinity_expr['values'][0] == 'b'

    for task in workflow['spec']['templates']:
        assert task['metadata']['labels']['a'] == 'b'

    op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)),
                                      pod_context=operations.PodExecutionContext('a', 'b', required=True))
    workflow = op.to_workflow()
    affinity_expr = \
        workflow['spec']['affinity']['podAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][0][
            'labelSelector'][
            'matchExpressions'][0]
    assert affinity_expr['key'] == 'a'
    assert affinity_expr['values'][0] == 'b'

    for task in workflow['spec']['templates']:
        assert task['metadata']['labels']['a'] == 'b'

    op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)),
                                      pod_context=(
                                          operations.PodExecutionContext('a', 'b'),
                                          operations.PodExecutionContext('c', 'd', required=True),
                                          operations.PodExecutionContext('e', 'f')
                                      ))
    workflow = op.to_workflow()
    assert 'affinity' in workflow['spec']
    preferred = workflow['spec']['affinity']['podAffinity']['preferredDuringSchedulingIgnoredDuringExecution']
    assert len(preferred) == 2
    affinity_expr = preferred[0]['podAffinityTerm']['labelSelector']['matchExpressions'][0]

    assert affinity_expr['key'] == 'a'
    assert affinity_expr['values'][0] == 'b'

    for task in workflow['spec']['templates']:
        assert task['metadata']['labels']['a'] == 'b'

    affinity_expr = preferred[1][
        'podAffinityTerm']['labelSelector']['matchExpressions'][0]

    assert affinity_expr['key'] == 'e'
    assert affinity_expr['values'][0] == 'f'

    for task in workflow['spec']['templates']:
        assert task['metadata']['labels']['e'] == 'f'

    affinity_expr = \
        workflow['spec']['affinity']['podAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][0][
            'labelSelector'][
            'matchExpressions'][0]
    assert affinity_expr['key'] == 'c'
    assert affinity_expr['values'][0] == 'd'


def test_gpu_workflow():

    
    from cloudharness.workflows import operations, tasks

    my_task = tasks.CustomTask('my-gpu', 'myapp-mytask', resources={"limits": {"nvidia.com/gpu": 1}})
    op = operations.PipelineOperation('my-op-gpu-', [my_task])
    wf = op.to_workflow()

    if verbose:
        print('\n', yaml.dump(wf))
    assert "nvidia.com/gpu" in wf['spec']['templates'][1]["container"]["resources"]["limits"]