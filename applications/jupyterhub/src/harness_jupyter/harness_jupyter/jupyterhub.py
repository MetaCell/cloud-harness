import logging
import sys

from kubespawner.spawner import KubeSpawner

def harness_hub():
    """Wraps the method to change spawner configuration"""
    KubeSpawner.get_pod_manifest_base = KubeSpawner.get_pod_manifest
    KubeSpawner.get_pod_manifest = spawner_pod_manifest

def spawner_pod_manifest(self: KubeSpawner):
    print("Cloudharness: changing pod manifest")
    change_pod_manifest(self)

    return KubeSpawner.get_pod_manifest_base(self)

def change_pod_manifest(self: KubeSpawner):
    subdomain = self.handler.request.host.split('.')[0]
    try:
        app_config = self.config['apps']
        for app in app_config.values():
            if 'harness' in app:

                harness = app['harness']
                if 'jupyterhub' in harness and harness['jupyterhub']\
                        and 'subdomain' in harness and harness['subdomain'] == subdomain:
                    print('Change image to %s', harness['deployment']['image'])
                    self.image = harness['deployment']['image']
                    if 'args' in harness['jupyterhub']:
                        self.args = harness['jupyterhub']['args']

                    # TODO add hook for application to override or add specific behaviours (like dynamic volumes)
                    # Use plugin name convention harness_jupyterhub_*, see also  https://packaging.python.org/guides/creating-and-discovering-plugins/
                    break
    except Exception as e:
        logging.error("Harness error changing manifest", exc_info=True)
