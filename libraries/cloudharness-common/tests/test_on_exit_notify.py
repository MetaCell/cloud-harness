"""Test on_exit_notify functionality with optional queue and payload parameters"""

from cloudharness.workflows import operations, tasks
from cloudharness import set_debug
from .test_env import set_test_environment

# Set up test environment
set_test_environment()
set_debug()


def test_on_exit_notify_custom_image_only():
    """Test that on_exit_notify works with just a custom image, no queue/payload"""
    print("Testing on_exit_notify with custom image only...")

    def test_function():
        return "test"

    task = tasks.PythonTask('test-task', test_function)

    # Test with custom image only (no queue/payload)
    on_exit_notify = {
        'image': 'my-custom-exit-handler'
    }

    op = operations.PipelineOperation('test-custom-exit', [task], on_exit_notify=on_exit_notify)
    wf = op.to_workflow()

    # Verify the exit handler was added
    assert 'onExit' in wf['spec'], "onExit should be present in spec"
    assert wf['spec']['onExit'] == 'exit-handler', "onExit should reference exit-handler template"

    # Find the exit-handler template
    exit_template = None
    for template in wf['spec']['templates']:
        if template['name'] == 'exit-handler':
            exit_template = template
            break

    assert exit_template is not None, "exit-handler template should exist"
    assert 'my-custom-exit-handler' in exit_template['container']['image'], f"Image should contain my-custom-exit-handler, got {exit_template['container']['image']}"

    # Check environment variables - should only have workflow_result
    env_vars = {}
    for env in exit_template['container']['env']:
        if 'value' in env:
            env_vars[env['name']] = env['value']
        elif 'valueFrom' in env:
            env_vars[env['name']] = env['valueFrom']

    assert 'workflow_result' in env_vars, "workflow_result should be present"
    assert env_vars['workflow_result'] == '{{workflow.status}}', "workflow_result should have correct value"

    # queue_name and payload should NOT be present since they weren't specified
    assert 'queue_name' not in env_vars, "queue_name should not be present when not specified"
    assert 'payload' not in env_vars, "payload should not be present when not specified"

    print("✓ Test passed: Custom image without queue/payload works correctly")


def test_on_exit_notify_with_queue_and_payload():
    """Test that the traditional usage still works (backward compatibility)"""
    print("Testing on_exit_notify with queue and payload (backward compatibility)...")

    def test_function():
        return "test"

    task = tasks.PythonTask('test-task', test_function)

    # Traditional usage with queue and payload
    on_exit_notify = {
        'queue': 'my_queue',
        'payload': '{"test": true}',
        'image': 'custom-image'
    }

    op = operations.PipelineOperation('test-traditional-exit', [task], on_exit_notify=on_exit_notify)
    wf = op.to_workflow()

    # Find the exit-handler template
    exit_template = None
    for template in wf['spec']['templates']:
        if template['name'] == 'exit-handler':
            exit_template = template
            break

    assert exit_template is not None, "exit-handler template should exist"

    # Check environment variables - should have all three
    env_vars = {}
    for env in exit_template['container']['env']:
        if 'value' in env:
            env_vars[env['name']] = env['value']
        elif 'valueFrom' in env:
            env_vars[env['name']] = env['valueFrom']

    assert 'workflow_result' in env_vars, "workflow_result should be present"
    assert 'queue_name' in env_vars, "queue_name should be present"
    assert 'payload' in env_vars, "payload should be present"

    assert env_vars['queue_name'] == 'my_queue', f"queue_name should be 'my_queue', got {env_vars['queue_name']}"
    assert env_vars['payload'] == '{"test": true}', f"payload should be correct, got {env_vars['payload']}"

    print("✓ Test passed: Backward compatibility works correctly")


def test_on_exit_notify_mixed_usage():
    """Test mixed usage with some optional parameters"""
    print("Testing on_exit_notify with mixed usage (queue but no payload)...")

    def test_function():
        return "test"

    task = tasks.PythonTask('test-task', test_function)

    # Mixed usage - queue but no payload
    on_exit_notify = {
        'image': 'my-custom-image',
        'queue': 'my_queue'
        # No payload specified
    }

    op = operations.PipelineOperation('test-mixed-exit', [task], on_exit_notify=on_exit_notify)
    wf = op.to_workflow()

    # Find the exit-handler template
    exit_template = None
    for template in wf['spec']['templates']:
        if template['name'] == 'exit-handler':
            exit_template = template
            break

    assert exit_template is not None, "exit-handler template should exist"

    # Check environment variables
    env_vars = {}
    for env in exit_template['container']['env']:
        if 'value' in env:
            env_vars[env['name']] = env['value']
        elif 'valueFrom' in env:
            env_vars[env['name']] = env['valueFrom']

    assert 'workflow_result' in env_vars, "workflow_result should be present"
    assert 'queue_name' in env_vars, "queue_name should be present"
    assert 'payload' not in env_vars, "payload should not be present when not specified"

    assert env_vars['queue_name'] == 'my_queue', f"queue_name should be 'my_queue', got {env_vars['queue_name']}"

    print("✓ Test passed: Mixed usage works correctly")


def test_on_exit_notify_default_image():
    """Test that default image still works when no custom image is specified"""
    print("Testing on_exit_notify with default image...")

    def test_function():
        return "test"

    task = tasks.PythonTask('test-task', test_function)

    # Traditional usage without custom image
    on_exit_notify = {
        'queue': 'my_queue',
        'payload': '{"test": true}'
        # No image specified - should use default
    }

    op = operations.PipelineOperation('test-default-exit', [task], on_exit_notify=on_exit_notify)
    wf = op.to_workflow()

    # Find the exit-handler template
    exit_template = None
    for template in wf['spec']['templates']:
        if template['name'] == 'exit-handler':
            exit_template = template
            break

    assert exit_template is not None, "exit-handler template should exist"

    # Should use default image
    assert 'workflows-notify-queue' in exit_template['container']['image'], f"Should use default image, got {exit_template['container']['image']}"

    print("✓ Test passed: Default image works correctly")
