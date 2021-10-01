import logging
import sys
import imp

from kubespawner.spawner import KubeSpawner
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)
def harness_hub():
    """Wraps the method to change spawner configuration"""
    KubeSpawner.get_pod_manifest_base = KubeSpawner.get_pod_manifest
    KubeSpawner.get_pod_manifest = spawner_pod_manifest

def spawner_pod_manifest(self: KubeSpawner):
    print("Cloudharness: changing pod manifest")
    change_pod_manifest(self)

    return KubeSpawner.get_pod_manifest_base(self)

def affinity_spec(key, value):
    return {

        'labelSelector':
            {
                'matchExpressions': [
                    {
                        'key': str(key),
                        'operator': 'In',
                        'values': [str(value)]
                    },
                ]
            },
        'topologyKey': 'kubernetes.io/hostname'
    }

def set_user_volume_affinity(self: KubeSpawner):
    # Add labels to use for affinity
    labels = {
        'user': urllib.parse.quote(self.user.name, safe='').replace('%', ''),
    }

    self.common_labels = labels
    self.extra_labels = labels

    for key, value in labels.items():
        self.pod_affinity_required.append(affinity_spec(key, value))

def change_pod_manifest(self: KubeSpawner):

    try:




        subdomain = self.handler.request.host.split(str(self.config['domain']))[0][0:-1]
        app_config = self.config['apps']
        registry = self.config['registry']
        for app in app_config.values():
            if 'harness' in app:
                harness = app['harness']
                if 'jupyterhub' in harness and harness['jupyterhub']\
                        and 'subdomain' in harness and harness['subdomain'] == subdomain:
                    print('Change image to %s', harness['deployment']['image'])
                    self.image = harness['deployment']['image']
                    if registry['name'] in self.image and registry['secret']:
                        self.image_pull_secrets = registry['secret']
                    if 'args' in harness['jupyterhub']:
                        self.args = harness['jupyterhub']['args']

                    if harness['jupyterhub'].get('mountUserVolume', True):
                        set_user_volume_affinity(self)
                    else:
                        self.volume_mounts = []
                        self.volumes = []

                    if 'spawnerExtraConfig' in harness['jupyterhub']:
                        for k, v in harness['jupyterhub']['spawnerExtraConfig'].items():
                            setattr(self, k, v)

                    # check if there is an applicationHook defined in the values.yaml
                    # if so then execute the applicationHook function with "self" as parameter
                    #
                    # e.g.
                    #   jupyterhub:
                    #       applicationHook: "jupyter.change_pod_manifest"
                    #
                    # this will execute jupyter.change_pod_manifest(self=self)
                    if 'applicationHook' in harness['jupyterhub']:
                        func_name = harness['jupyterhub']['applicationHook'].split('.')
                        module = __import__('.'.join(func_name[:-1]))
                        f = getattr(module, func_name[-1])
                        f(self=self)
                    break
    except Exception as e:
        logging.error("Harness error changing manifest", exc_info=True)
