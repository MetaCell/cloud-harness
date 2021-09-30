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

def change_pod_manifest(self: KubeSpawner):

    try:
        subdomain = self.handler.request.host.split('.')[0]
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

                    # Check for app specific config, cpu_limit, cpu_guarantee etc...
                    # e.g.
                    # harness:
                    #   jupyterhub:
                    #     spawnerExtraConfig:
                    #       cpu_guarantee: 1.6
                    #       cpu_limit: 3
                    #       mem_guarantee: 4G
                    #       mem_limit: 8G
                    #       node_selector:             # optional node pool for these pods
                    #         - key: ch/nodepool
                    #           operator: In           # In, NotIn, Exists, DoesNotExist. Gt, and Lt.
                    #           values: pool-jupyter
                    #           matchPurpose: require  # require | prefer | ignore
                    spawnerExtraConfig = getattr(harness['jupyterhub'], 'spawnerExtraConfig', None)
                    if spawnerExtraConfig:
                        for k, v in spawnerExtraConfig.items():
                            setattr(self, k, v)
                        node_selectors = getattr(self, 'node_selector', None)  
                        if node_selectors:
                            for node_selector in node_selectors:
                                labels[node_selector.key] = node_selector.values
                                node_selector = dict(
                                    matchExpressions=[
                                        dict(
                                            key=node_selector.key,
                                            operator=node_selector.operator,
                                            values=[node_selector.values],
                                        )
                                    ],
                                )
                                if node_selector.matchPurpose == 'prefer':
                                    self.node_affinity_preferred.append(
                                        dict(
                                            weight=100,
                                            preference=node_selector,
                                        ),
                                    )
                                elif match_node_purpose == 'require':
                                    self.node_affinity_required.append(node_selector)
                                elif match_node_purpose == 'ignore':
                                    pass
                                else:
                                    raise ValueError("Unrecognized value for matchNodePurpose: %r" % match_node_purpose)

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
