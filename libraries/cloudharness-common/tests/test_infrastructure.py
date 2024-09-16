from cloudharness.infrastructure import k8s
from .test_env import set_test_environment

set_test_environment()


kubectl_enabled = False


def test_get_pods():
    if not kubectl_enabled:
        return
    return k8s.get_pods(namespace='kube_system')
