"""Notice, this test needs a fully operating kubernetes with argo environment in the container running the test"""
import time

from cloudharness.workflows import operations
from cloudharness import set_debug

set_debug()

import yaml
from .test_env import set_default_environment

set_default_environment()


def test_sync_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    task = operations.PythonTask('my-task', f)

    op = operations.DistributedSyncOperation('test-sync-op-', task)
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_pipeline_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.PipelineOperation('test-pipeline-op-', (operations.PythonTask('step1', f), operations.PythonTask('step2', f)))
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_parallel_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    op = operations.ParallelOperation('test-parallel-op-', (operations.PythonTask('p1', f), operations.PythonTask('p2', f)))
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_simpledag_workflow():
    def f():
        import time
        time.sleep(2)
        print('whatever')

    # p3 runs after p1 and p2 finish
    op = operations.SimpleDagOperation('test-dag-op-', (operations.PythonTask('p1', f), operations.PythonTask('p2', f)),
                                operations.PythonTask('p3', f))
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())

def test_custom_task_workflow():
    task = operations.CustomTask('download-file', 'cloudharness-workflows-extract-download', url='https://www.bing.com')
    op = operations.PipelineOperation('test-custom-op-', (task, ))
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_custom_connected_task_workflow():
    shared_directory = '/mnt/shared'
    task_write = operations.CustomTask('download-file', 'cloudharness-workflows-extract-download', url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')
    task_print = operations.CustomTask('print-file', 'cloudharness-workflows-print-file', file_path=shared_directory + '/README.md')
    op = operations.PipelineOperation('test-custom-connected-op-', (task_write, task_print), shared_directory=shared_directory)
    # op.execute()
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())


def test_result_task_workflow():
    task_write = operations.CustomTask('download-file', 'cloudharness-workflows-extract-download', url='https://raw.githubusercontent.com/openworm/org.geppetto/master/README.md')

    op = operations.DistributedSyncOperationWithResults('test-sync-results-', task_write)


    # op.execute()
    print('\n', yaml.dump(op.to_workflow()))
    print(op.execute())



# op = operations.ParallelOperation('my_op', [task, operations.CustomTask('my-coreg', 'coregistration-init')])
