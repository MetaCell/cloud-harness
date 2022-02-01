# What are workflows?

Workflows can be seen as kind of structured batch operation running in the cluster using on-demand resources.
Workflows are composed by one on one tasks and can be of the following types depending how the tasks are arranged:
- Simple workflow with one task
- Workflow with parallel tasks
- Pipeline workflow with tasks running sequentially
- Simple DAG (pipeline of parallel tasks)

Tasks are Docker container executions managed by the workflows system. Any docker image can be used as a base for a task.


# When do I need a workflow?
- *Use on demand resources*: when the workflow runs it requests the amount of resources (e.g. cpu and memory) in the cluster, and frees the resources as soon it stops. This is usually the case for heavy computations.
- *Specific technological stack*: a computational pipeline can require a specific technological stack and/or a specific (and possibly heavy) set of libraries. The base stack may be different from the one used on the main service (usually a Python Flask application). Even if the base stack is the same adding all the libraries in the main service may not be the best solution
- Make asynchronous long operations

# How to run workflows?
Cloudharness allows to run workflows through [Argo workflows](https://github.com/argoproj/argo-workflows) providing the Argo installation and a Python library to run workflows programmatically.

## High level Operations API

The cloudharness Operations api allows to easily run a workflow from Python.
The pattern to run a workflow is the following:
1. create the tasks
1. Add the tasks to an operation object of the needed type
1. Execute the operation

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
  

## Create a custom task

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

## Passing parameters as env variables to tasks
All additional named parameters added to a ContainerizedTask are converted into env variables in the container

For example
```Python
my_task = tasks.CustomTask('print-file', 'myapp-mytask', env_variable1="my variable", env_variable2=1)
op = operations.SingleTaskOperation('my-op-', my_task)
op.execute()
```

## Use shared volumes
Shared volumes are useful if we want to share data within a pipeline or to write data inside another existing volume within the cluster

# How to monitor and debug my workflows?
Workflows can be monitored through argo ui going to argo.[DOMAIN] or through command line with the [argo cli](https://argoproj.github.io/argo-workflows/cli/)

# More examples
See the application samples controllers (application.samples.controllers.workflows_controller.py) for a practical case of a service using asynchronous and synchronous workflows as part of the api.
Some examples are also available as unit tests.