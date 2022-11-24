import imp
import logging
import sys
import urllib.parse

from kubespawner.spawner import KubeSpawner
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)

class PodSpawnException(Exception):
    pass


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

                if 'subdomain' in harness and harness['subdomain'] == subdomain:
                    if app['name'] != 'jupyterhub': # Would use the hub image in that case, which we don't want.
                        print('Change image to', harness['deployment']['image'])
                        self.image = harness['deployment']['image']
                        if registry['name'] in self.image and registry['secret']:
                            self.image_pull_secrets = registry['secret']

                    if 'jupyterhub' in harness and harness['jupyterhub']:
                        if 'args' in harness['jupyterhub']:
                            self.args = harness['jupyterhub']['args']

                        if harness['jupyterhub'].get('mountUserVolume', True):
                            set_user_volume_affinity(self)
                        else:
                            self.volume_mounts = []
                            self.volumes = []

                        # set http timeout higher to give the notebooks time to run their init scripts
                        self.http_timeout = 60 * 5 # 5 minutes

                        if 'spawnerExtraConfig' in harness['jupyterhub']:
                            try:
                                for k, v in harness['jupyterhub']['spawnerExtraConfig'].items():
                                    if k != 'node_selectors':
                                        setattr(self, k, v)

                                # check if there are node selectors, if so apply them to the pod
                                node_selectors = harness['jupyterhub']['spawnerExtraConfig'].get('node_selectors')
                                if node_selectors:
                                    for node_selector in node_selectors:
                                        ns = dict(
                                            matchExpressions=[
                                                dict(
                                                    key=node_selector['key'],
                                                    operator=node_selector['operator'],
                                                    values=[node_selector['values']],
                                                )
                                            ],
                                        )
                                        match_node_purpose = node_selector['matchPurpose']
                                        if match_node_purpose == 'prefer':
                                            self.node_affinity_preferred.append(
                                                dict(
                                                    weight=100,
                                                    preference=ns,
                                                ),
                                            )
                                        elif match_node_purpose == 'require':
                                            self.node_affinity_required.append(ns)
                                        elif match_node_purpose == 'ignore':
                                            pass
                                        else:
                                            raise ValueError("Unrecognized value for matchNodePurpose: %r" % match_node_purpose)
                            except:
                                logging.error("Error loading Spawner extra configuration", exc_info=True)
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

    except TooManyPodsException as e:
        raise e
    except Exception as e:
        logging.error("Harness error changing manifest", exc_info=True)
