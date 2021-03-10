"""Notice, this test needs a fully operating kubernetes with argo environment in the container running the test"""
import requests
import yaml



from .test_env import set_test_environment

set_test_environment()

from cloudharness.workflows import operations, tasks
from cloudharness import set_debug
from cloudharness.workflows import argo
from cloudharness.utils.config import CloudharnessConfig

set_debug()

execute = False

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
        print(op.execute())


def test_parallel_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)))
    print('\n', yaml.dump(op.to_workflow()))
    if execute:
        print(op.execute())




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

    op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)), pod_context=operations.PodExecutionContext('a', 'b'))
    workflow = op.to_workflow()
    assert 'affinity'  in workflow['spec']
    affinity_expr = workflow['spec']['affinity']['podAffinity']['requiredDuringSchedulingIgnoredDuringExecution'][0]['labelSelector']['matchExpressions'][0]
    assert affinity_expr['key'] == 'a'
    assert affinity_expr['values'][0] == 'b'

    for task in workflow['spec']['templates']:
        assert  task['metadata']['labels']['a'] == 'b'

