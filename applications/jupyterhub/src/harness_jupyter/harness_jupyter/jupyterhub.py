import imp
import logging
import sys
import urllib.parse

from kubespawner.spawner import KubeSpawner

from cloudharness.applications import get_configuration
from cloudharness.auth.quota import get_user_quotas
from cloudharness.utils.config import CloudharnessConfig as conf


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
logging.getLogger().addHandler(handler)

def custom_options_form(spawner, abc):
    # let's skip the profile selection form for now
    # ToDo: for future we can remove this hook
    spawner.profile_list = []
    # ref: https://github.com/jupyterhub/kubespawner/blob/37a80abb0a6c826e5c118a068fa1cf2725738038/kubespawner/spawner.py#L1885-L1935
    return spawner._options_form_default()


class PodSpawnException(Exception):
    pass


def harness_hub():
    """Wraps the method to change spawner configuration"""
    KubeSpawner.get_pod_manifest_base = KubeSpawner.get_pod_manifest
    KubeSpawner.get_pod_manifest = spawner_pod_manifest
    # let's skip the profile selection form for now
    # TODO: for future we can remove this hook
    KubeSpawner.options_form = custom_options_form
    KubeSpawner.get_pvc_manifest_base = KubeSpawner.get_pvc_manifest
    KubeSpawner.get_pvc_manifest = spawner_pvc_manifest


def spawner_pod_manifest(self: KubeSpawner):
    print("Cloudharness: changing pod manifest")
    change_pod_manifest(self)
    return KubeSpawner.get_pod_manifest_base(self)


def spawner_pvc_manifest(self: KubeSpawner):
    print("Cloudharness: changing pvc manifest")
    change_pvc_manifest(self)
    return KubeSpawner.get_pvc_manifest_base(self)


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
        

def set_key_value(self, key, value, unit=None):
    if value:
        if unit:
            print(f"setting key {key} to {value}{unit}")
            setattr(self, key, f"{value}{unit}")
        else:
            print(f"setting key {key} to {value}")
            setattr(self, key, value)


def change_pvc_manifest(self: KubeSpawner):
    try:
        # check user quotas
        application_config = get_configuration("jupyterhub")
        user_quotas = get_user_quotas(
            application_config=application_config,
            user_id=self.user.name)
        set_key_value(self, key="storage_capacity", value=user_quotas.get("quota-storage-max"), unit="Gi")
    except Exception as e:
        logging.error("Harness error changing pvc manifest", exc_info=True)

def change_pod_manifest(self: KubeSpawner):
    # check user quotas
    application_config = get_configuration("jupyterhub")

    
    user_quotas = get_user_quotas(
        application_config=application_config,
        user_id=self.user.name)

    quota_ws_open = user_quotas.get("quota-ws-open")
    if quota_ws_open:
        # get user number of pods running
        num_of_pods = len(list(self.user.all_spawners(include_default=True)))
        if num_of_pods > int(quota_ws_open):
            raise PodSpawnException(
                                "User {} already has the maximum of {} servers."
                                "  One must be deleted before a new server can be started".format(
                                    self.user.name, quota_ws_open
                                ),
                            )
    try:
        subdomain = self.handler.request.host.split(str(self.config['domain']))[0][0:-1]
        app_config = self.config['apps']
        registry = self.config['registry']
        for app in app_config.values():
            if 'harness' in app:
                harness = app['harness']

                if 'subdomain' in harness and harness['subdomain'] == subdomain:
                    ws_image = getattr(self, "ws_image", None)
                    if ws_image:
                        # try getting the image + tag from values.yaml
                        ch_conf = conf.get_configuration()
                        task_images = ch_conf['task-images']
                        for task_image in task_images:
                            image_plus_tag = task_images[task_image]
                            if ws_image in image_plus_tag:
                                ws_image = image_plus_tag
                                logging.error(f'Found tag for image: {ws_image}')
                                break
                    else:
                        if app['name'] != 'jupyterhub': # Would use the hub image in that case, which we don't want.
                            ws_image = harness['deployment']['image']
                    if ws_image:
                        logging.info(f'Change image to {ws_image}')
                        self.image = ws_image
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

                        # set user quota cpu/mem usage if value has a "value" else don't change the value
                        set_key_value(self, key="cpu_guarantee", value=user_quotas.get("quota-ws-guaranteecpu"))
                        set_key_value(self, key="cpu_limit", value=user_quotas.get("quota-ws-maxcpu"))
                        set_key_value(self, key="mem_guarantee", value=user_quotas.get("quota-ws-guaranteemem"), unit="G")
                        set_key_value(self, key="mem_limit", value=user_quotas.get("quota-ws-maxmem"), unit="G")

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

    except PodSpawnException as e:
        raise e
    except Exception as e:
        logging.error("Harness error changing manifest", exc_info=True)
