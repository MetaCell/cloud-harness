import sys
import urllib.parse
import asyncio
from functools import partial

from kubespawner.spawner import KubeSpawner
from jupyterhub.utils import exponential_backoff


from cloudharness.applications import get_configuration
from cloudharness.auth.quota import get_user_quotas
from cloudharness.utils.config import CloudharnessConfig as conf
from cloudharness import log as logging, set_debug

set_debug()


def custom_options_form(spawner, abc):
    # let's skip the profile selection form for now
    # ToDo: for future we can remove this hook
    # ref: https://github.com/jupyterhub/kubespawner/blob/37a80abb0a6c826e5c118a068fa1cf2725738038/kubespawner/spawner.py#L1885-L1935
    try:
        print("Cloudharness: start saving profile list in _ch_profile_list")
        spawner._ch_profile_list = spawner.profile_list
        # spawner.profile_list = []
        print("Cloudharness: saving profile list in _ch_profile_list")
    except Exception as e:
        print(f"Cloudharness: finish saving profile exception: {e}")
    return spawner._options_form_default()


class PodSpawnException(Exception):
    pass


def harness_hub():
    """Wraps the method to change spawner configuration"""
    print("Cloudharness: changing spawner configuration")
    KubeSpawner.get_pod_manifest_base = KubeSpawner.get_pod_manifest
    KubeSpawner.get_pod_manifest = spawner_pod_manifest
    # to skip the profile selection form enable the line below
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
        'user': str(self.user.id),
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
        set_key_value(self, key="storage_capacity",
                      value=user_quotas.get("quota-storage-max"), unit="Gi")
    except Exception as e:
        logging.error("Harness error changing pvc manifest", exc_info=True)


def apply_extra_config(self: KubeSpawner, extra_config: dict):
    for k, v in extra_config.items():
        if k != 'node_selectors':
            try:
                logging.info(f"Setting {k} to {v}")
                setattr(self, k, v)
            except Exception as e:
                logging.error(
                    f"Error setting {k} to {v}: {e}")

        # check if there are node selectors, if so apply them to the pod
        node_selectors = extra_config.get('node_selectors', None)
        if node_selectors:
            apply_node_selectors(self, node_selectors)


def apply_node_selectors(self: KubeSpawner, node_selectors):
    for node_selector in node_selectors:
        logging.info("Setting node selector", node_selector["key"])
        ns = dict(
            matchExpressions=[
                dict(
                    key=node_selector['key'],
                    operator=node_selector['operator'],
                    values=[
                        node_selector['values']],
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
            self.node_affinity_required.append(
                ns)
        elif match_node_purpose == 'ignore':
            pass
        else:
            raise ValueError(
                "Unrecognized value for matchNodePurpose: %r" % match_node_purpose)


def change_pod_manifest(self: KubeSpawner):
    # check user quotas
    application_config = get_configuration("jupyterhub")

    logging.info("Cloudharness: changing pod manifest")
    user_quotas = get_user_quotas(
        application_config=application_config,
        user_id=self.user.name)

    quota_ws_open = user_quotas.get("quota-ws-open")

    # set user quota cpu/mem usage if value has a "value" else don't change the value

    logging.info("Setting user quota cpu/mem usage")

    set_key_value(self, key="cpu_guarantee", value=float(user_quotas.get("quota-ws-guaranteecpu")))
    set_key_value(self, key="cpu_limit", value=float(user_quotas.get("quota-ws-maxcpu")))
    set_key_value(self, key="mem_guarantee", value=user_quotas.get("quota-ws-guaranteemem"), unit="G")
    set_key_value(self, key="mem_limit", value=user_quotas.get("quota-ws-maxmem"), unit="G")

    # Default value, might be overwritten by the app config
    self.storage_pvc_ensure = bool(self.pvc_name)

    if quota_ws_open:
        # get user number of pods running
        servers = [s for s in self.user.all_spawners(include_default=True)]
        num_of_pods = len([s for s in servers if s.active])
        if num_of_pods > int(quota_ws_open):
            raise PodSpawnException(
                "You reached your quota of {} concurrent servers."
                "  One must be deleted before a new server can be started".format(
                    quota_ws_open
                ),
            )
    # set http timeout higher to give the notebooks time to run their init scripts
    self.http_timeout = 60 * 5  # 5 minutes
    try:
        subdomain = self.handler.request.host.split(
            str(self.config['domain']))[0][0:-1]
        app_config = self.config['apps']
        registry = self.config['registry']

        
        logging.info("Subdomain is %s", subdomain)
        try:
            app = next(app for app in app_config.values() if 'harness' in app and 'subdomain' in app['harness'] and app['harness']['subdomain'] == subdomain)
        except StopIteration:
            logging.warning(f"No app found for subdomain {subdomain}, using default jupyterhub configuration")
            app = app_config['jupyterhub']

        logging.info(f"Using configuration for app {app['name']}")
        harness = app['harness']

        if 'jupyterhub' in harness and harness['jupyterhub']:
            logging.info("Setting JupyterHub configuration from harness.jupyterhub")
            if 'args' in harness['jupyterhub']:
                logging.info("Setting custom args")
                self.args = harness['jupyterhub']['args']

                if harness['jupyterhub'].get('mountUserVolume', True):
                    logging.info("Setting user volume affinity")
                    set_user_volume_affinity(self)
                else:
                    self.volume_mounts = []
                    self.volumes = []

            if 'spawnerExtraConfig' in harness['jupyterhub']:
                extra_config = harness['jupyterhub']['spawnerExtraConfig']
                logging.info("Setting custom spawner config")
                try:
                    apply_extra_config(self, extra_config)
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
                logging.info(f"Executing application hook {func_name}")
                module = __import__('.'.join(func_name[:-1]))
                f = getattr(module, func_name[-1])
                f(self=self)

        if registry['name'] in self.image and registry['secret']:
            self.image_pull_secrets = registry['secret']

        ws_image = getattr(self, "ws_image", None)
        if ws_image:
            logging.info(f'Found configured workspace image for profile: {ws_image}')
            try:
                self.image = conf.get_image_tag(ws_image)
                logging.info(f'Use image from profile: {self.image}')
            except Exception as e:
                logging.error(
                    f"Error getting image tag for {ws_image}: {e}")
                ws_image = None
        elif app['name'] != 'jupyterhub':
            # Use specific image for current application based on subdomain.
            self.image = harness['deployment']['image']
            logging.info(f'Use specific app image: {self.image}')
    except PodSpawnException as e:
        raise e
    except Exception as e:
        logging.error("Harness error changing manifest", exc_info=True)

    if self.storage_pvc_ensure and self.volumes:

        pvc = self.get_pvc_manifest()
        from pprint import pprint
        pprint(self.storage_class)

        # If there's a timeout, just let it propagate
        asyncio.ensure_future(exponential_backoff(
            partial(
                self._make_create_pvc_request, pvc, self.k8s_api_request_timeout
            ),
            f'Could not create PVC {self.pvc_name}',
            # Each req should be given k8s_api_request_timeout seconds.
            timeout=self.k8s_api_request_retry_timeout,
        ))
