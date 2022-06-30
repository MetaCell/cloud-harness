# Workflows Python API

## Concepts
### What are workflows?

Workflows can be seen as kind of structured batch operation running in the cluster using on-demand resources.
Workflows are composed by one on one tasks and can be of the following types depending how the tasks are arranged:
- Simple workflow with one task
- Workflow with parallel tasks
- Pipeline workflow with tasks running sequentially
- Simple DAG (pipeline of parallel tasks)

Tasks are Docker container executions managed by the workflows system. Any docker image can be used as a base for a task.


### When do I need a workflow?
- *Use on demand resources*: when the workflow runs it requests the amount of resources (e.g. cpu and memory) in the cluster, and frees the resources as soon it stops. This is usually the case for heavy computations.
- *Specific technological stack*: a computational pipeline can require a specific technological stack and/or a specific (and possibly heavy) set of libraries. The base stack may be different from the one used on the main service (usually a Python Flask application). Even if the base stack is the same adding all the libraries in the main service may not be the best solution
- Make asynchronous long operations

### How to run workflows?
Cloudharness allows to run workflows through [Argo workflows](https://github.com/argoproj/argo-workflows) providing the Argo installation and a Python library to run workflows programmatically.

## High level Operations API

The cloudharness Operations api allows to run a workflow from Python.
The steps to run a workflow are:
1. Create the Tasks
1. Add the Tasks to an Operation object
1. Execute the Operation

Simple example of a parallel operation running Python code:

```Python
from cloudharness.workflows import operations, tasks

def f():
    import time
    time.sleep(2)
    print('whatever')

op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)))
```

### Operation types
- _SyncOperation_ - returns the result directly with the execute method
  - _DirectOperation_ - runs inside the service container (not on Argo). Does not have practical use other than testing
    - **ResourceQueryOperation**
    - **DataQueryOperation**
  - **DistributedSyncOperation** - waits for the workflow to finish before returning
  - **DistributedSyncOperationWithResults** - returns the result from the workflow. Uses a shared volume and a queue

- _AsyncOperation_ - is made asynchronously in an Argo workflow. The workflow can be monitored during the execution
  - **SingleTaskOperation**
  - _CompositeOperation_
    - **PipelineOperation** - takes a list of tasks running sequentially
    - **ParallelOperation** - takes a list of tasks running in parallel
    - **SimpleDagOperation** - simple Direct-Acyclic-Graph made from pipeline of parallel tasks

### Task Types
- _InlinedTask_ - runs a script in a default image. No specific container configuration
  - **PythonTask** - runs a Python function
  - **BashTask** - runs a bash script
- **ContainerizedTask** - runs in a Docker container. Any accessible Docker image can be used
  - **CustomTask** - allows to specify a custom image. The image can be defined inside one of the applications
  - **CommandBasedTask** - Run a single command in the default cloudharness container 
  

## Using CustomTask

Custom tasks are specified inside an application as Dockerfiles.

For example a task named "myapp-mytask" comes from:
- applications
  - myapp
    - tasks
      - mytask
        Dockerfile

The task can the be used as

```Python
my_task = tasks.CustomTask('print-file', 'myapp-mytask')
op = operations.SingleTaskOperation('my-op-', my_task)
op.execute()
```

### Execute a custom command

By default the container will execute the default command specified in the Docker image within a `CustomTask` runtime. 

To execute a custom command use the `command` parameter.

```Python
my_task = tasks.CustomTask('print-file', 'myapp-mytask', command=["ls", "-la"])
op = operations.SingleTaskOperation('my-op-', my_task)
op.execute()
```

## Passing parameters as env variables to tasks
All additional named parameters added to a ContainerizedTask are converted into env variables in the container

For example
```Python
my_task = tasks.CustomTask('print-file', 'myapp-mytask', env_variable1="my variable", env_variable2=1)
op = operations.SingleTaskOperation('my-op-', my_task)
op.execute()
```

## Use shared/external volumes
Shared volumes are useful if we want to share data within a pipeline or to write data inside another existing volume within the cluster.
The shared volume must be indicated both in the Operation and it is propagated to all tasks.

The `shared_directory` parameter is a quick way to specify a shared directory, and, optionally,
the name of a volume claim. 

The syntax is `[CLAIM_NAME:]MOUNT_PATH[:MODE]`.
- The `CLAIM_NAME` can be an existing or new volume claim name. In the case a claim already exists with that name it will be used.
Otherwise a new ephemeral volume is created: that volume will exist during the life of the workflow and deleted after completion
- The `MOUNT_PATH` is the path where we want the volume to be mounted inside our pod
- The appendix `:MODE` indicated the read/write mode. If `ro`, the
volume is mounted as read-only. Read only volumes are useful to overcome
scheduling limitations (ReadWriteOnce is usually available) when 
writing is not required, and it's generally recommended whenever writing
is not required.

```Python
shared_directory="myclaim:/opt/shared"
my_task = tasks.CustomTask('print-file', 'myapp-mytask')
op = operations.SingleTaskOperation('my-op-', my_task, shared_directory=shared_directory)
op.execute()
```

More than one directory/volume can be shared by passing a list/tuple:

```Python
shared_directory=["myclaim:/opt/shared:ro", "myclaim2:/opt/shared2"]
my_task = tasks.CustomTask('print-file', 'myapp-mytask')
op = operations.SingleTaskOperation('my-op-', my_task, shared_directory=shared_directory)
op.execute()
```



## Pod execution context / affinity

Affinity is set through the 

```Python
def f():
  print('whatever')

op = operations.ParallelOperation('test-parallel-op-', (tasks.PythonTask('p1', f), tasks.PythonTask('p2', f)),
                                      pod_context=operations.PodExecutionContext(key='a', value='b', required=True))
```

The execution context is set allows to group pods in the same node (see [here](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)).
This is important in particular when pods are sharing node resources like ReadWriteOnce volumes within a parallel execution or with other deployments in the cluster.
The execution context sets the affinity and the metadata attributes so that all pods with the same context
run in the same node 

## TTL (Time-To-Live) strategy

By default, workflows are removed some time after the completion.

Default value:
```Python
{
    'secondsAfterCompletion': 60 * 60,
     'secondsAfterSuccess': 60 * 20,
     'secondsAfterFailure': 60 * 120
}
```

To set the TTL strategy, set the value on the operation with the `ttl_strategy` parameter.
To disable any automatic removal, set `ttl_strategy=None`


```Python
ttl_strategy={
    'secondsAfterCompletion': 60 * 60 * 24,
    'secondsAfterSuccess': 60 * 20,
    'secondsAfterFailure': 60 * 120
}
op = operations.ParallelOperation(..., ttl_strategy=ttl_strategy)
```

## Notify on exit

The parameter `on_exit_notify` adds an additional task to the workflow that notifies its completion in the events queue.
It communicates the outcome of the operation (i.e. Success, Error), allows you to define the message queue topic and the payload to send in the message

```Python
import json
on_exit_notify={
    'queue': 'my_queue',
    'payload': json.dumps({'insert': 1})
}
op = operations.ParallelOperation(..., on_exit_notify=on_exit_notify)
```

Synchronous operation types use this mechanism to wait for the result and get the value.

# How to monitor and debug my workflows?
Workflows can be monitored through argo ui going to argo.[DOMAIN] or through command line with the [argo cli](https://argoproj.github.io/argo-workflows/cli/)

# More examples
See the [samples application controller](../../../applications/samples/backend/samples/controllers/workflows_controller.py) for a practical case of a service using asynchronous and synchronous workflows as part of the api.
Some examples are also available as unit tests.