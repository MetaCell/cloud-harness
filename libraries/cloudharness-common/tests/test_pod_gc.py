"""Keep existing CloudHarness inputs compatible with Argo duration fields."""

from cloudharness.workflows import operations, tasks
from cloudharness import set_debug
from .test_env import set_test_environment

set_test_environment()
set_debug()

def test_integer_ttl_keeps_public_inputs_and_serializes_argo_duration():
    ttl = {'secondsAfterSuccess': 86400, 'secondsAfterFailure': 3600}
    operation = operations.PipelineOperation(
        'integer-ttl', [tasks.CustomTask('run', 'busybox')], ttl_strategy=ttl,
    )
    spec = operation.to_workflow()['spec']
    assert spec['ttlStrategy'] == ttl
    assert spec['podGC']['deleteDelayDuration'] == '86400s'
    assert ttl['secondsAfterSuccess'] == 86400


def test_explicit_integer_pod_gc_delay_does_not_mutate_caller():
    pod_gc = {'strategy': 'OnWorkflowSuccess', 'deleteDelayDuration': 0}
    operation = operations.PipelineOperation(
        'explicit-gc', [tasks.CustomTask('run', 'busybox')], pod_gc=pod_gc,
    )
    assert operation.to_workflow()['spec']['podGC']['deleteDelayDuration'] == '0s'
    assert pod_gc['deleteDelayDuration'] == 0


def test_string_pod_gc_duration_and_missing_ttl_defaults_are_preserved():
    for gc, expected in (
        ({'strategy': 'OnWorkflowSuccess', 'deleteDelayDuration': '2m'}, '2m'),
        (None, '600s'),
    ):
        operation = operations.PipelineOperation(
            'gc-defaults', [tasks.CustomTask('run', 'busybox')],
            ttl_strategy=None, pod_gc=gc,
        )
        assert operation.to_workflow()['spec']['podGC']['deleteDelayDuration'] == expected


def test_existing_sdk_pod_gc_input_is_preserved():
    from argo.workflows.client import V1alpha1PodGC
    pod_gc = V1alpha1PodGC(strategy='OnWorkflowSuccess')
    operation = operations.PipelineOperation(
        'sdk-gc', [tasks.CustomTask('run', 'busybox')], pod_gc=pod_gc,
    )
    assert operation.to_workflow()['spec']['podGC'] is pod_gc
