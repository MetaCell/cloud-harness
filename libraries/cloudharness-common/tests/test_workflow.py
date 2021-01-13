"""Notice, this test needs a fully operating kubernetes with argo environment in the container running the test"""
import time
from cloudharness.utils.config import CloudharnessConfig as conf
from .test_env import set_test_environment
set_test_environment()

from cloudharness.workflows import operations, tasks
from cloudharness import set_debug

set_debug()

import yaml




def test_sync_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    task = tasks.PythonTask('my-task', f)

    op = operations.DistributedSyncOperation('test-sync-op-', task)
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_pipeline_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.PipelineOperation('test-pipeline-op-', (tasks.PythonTask('step1', f), tasks.PythonTask('step2', f)))
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_parallel_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)))
    print('\n', yaml.dump(op.to_workflow()))
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
    print(op.execute())

def test_custom_task_workflow():
    task = operations.CustomTask('download-file', 'workflows-extract-download', url='https://www.bing.com')
    op = operations.PipelineOperation('test-custom-op-', (task, ))
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_custom_connected_task_workflow():
    shared_directory = '/mnt/shared'
    task_write = operations.CustomTask('download-file', 'workflows-extract-download', shared_directory = shared_directory, url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')
    task_print = operations.CustomTask('print-file', 'workflows-print-file', shared_directory = shared_directory, file_path=shared_directory + '/README.md')
    op = operations.PipelineOperation('test-custom-connected-op-', (task_write, task_print), shared_directory=shared_directory, shared_volume_size = 100)
    # op.execute()
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_result_task_workflow():
    task_write = operations.CustomTask('download-file', 'workflows-extract-download', url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')

    op = operations.DistributedSyncOperationWithResults('test-sync-results-', task_write)


    # op.execute()
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())



# op = operations.ParallelOperation('my_op', [task, operations.CustomTask('my-coreg', 'coregistration-init')])
