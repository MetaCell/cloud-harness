from .test_env import set_test_environment
set_test_environment()

from cloudharness.infrastructure import k8s

def test_get_pods():
    return k8s.get_pods(namespace='kube_system')