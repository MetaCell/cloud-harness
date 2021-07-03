import yaml

import os

ALLVALUES_PATH = os.getenv("CH_VALUES_PATH", '/opt/cloudharness/resources/allvalues.yaml')


class ConfigObject(object):
    def __init__(self, dictionary):
        self.conf = dictionary
        for key, val in dictionary.items():
            if isinstance(val, (list, tuple)):
                setattr(self, key, [ConfigObject(x) if isinstance(x, dict) else x for x in val])
            else:
                setattr(self, key, ConfigObject(val) if isinstance(val, dict) else val)

    def __getitem__(self, key_or_path):
        obj = self.conf
        for k in key_or_path.split('.'):
            if not k in obj:
                return None
            obj = obj[k]
        return obj

class CloudharnessConfig:
    """
    Helper class for the Cloud Harness configuration

    The CH configuration will be loaded from the values.yaml generated by helm
    via the harness-deployment script
    
    """
    allvalues={}

    @classmethod
    def _get_all_values(cls):
        if not cls.allvalues and os.path.exists(ALLVALUES_PATH):
            with open(ALLVALUES_PATH) as f:
                cls.allvalues = yaml.safe_load(f)
        return cls.allvalues

    @classmethod
    def _get_apps(cls):
        if not hasattr(cls, 'apps'):
            cls.apps = ConfigObject(cls._get_all_values()['apps'])
        return cls.apps

    @classmethod
    def get_namespace(cls):
        return cls.get_configuration()['namespace']

    @classmethod
    def get_current_app(cls):
        return cls.get_application_by_filter(name=cls.get_current_app_name())[0]

    @classmethod
    def get_current_app_name(cls):
        return os.getenv("CH_CURRENT_APP_NAME")

    @classmethod
    def get_domain(cls):
        return cls.get_configuration()['domain']


    @classmethod
    def get_registry_name(cls):
        return cls.get_configuration()['registry']['name']

    @classmethod
    def get_registry_secret(cls):
        return cls.get_configuration()['registry']['secret']

    @classmethod
    def is_secured(cls):
        try:
            return bool(cls.get_configuration()['tls'])
        except KeyError:
            return False

    @classmethod
    def is_test(cls):
        return 'test' in cls.get_configuration() and cls.get_configuration()['test']

    @classmethod
    def get_image_tag(cls, base_name):
        if base_name in cls.get_applications():
            from cloudharness.applications import get_configuration
            return get_configuration(base_name).image_name
        else:
            if not base_name in cls.get_configuration()['task-images']:
                # External image
                return base_name
            return cls.get_configuration()['task-images'][base_name]

    @classmethod
    def get_application_by_filter(cls, **filter):
        """
        Helper function for filtering CH app objects

        Args:
            filter: the filter e.g. harness__deployment__auto=True

        Returns:
            list of app objects (see values.yaml for a detailed description)

        Usage examples: 
            from cloudharness.utils.config import CloudharnessConfig as conf
            conf.get_application_by_filter(harness__deployment__auto=True)
            conf.get_application_by_filter(name='workflows')
        """
        apps = []
        filter_keys = next(iter(filter)).split('__')
        filter_value = next(iter(filter.values()))
        all_apps = cls._get_apps()
        for app_key in cls.get_applications():
            app = getattr(all_apps, app_key)
            tmp_obj = app
            try:
                for key in filter_keys:
                    tmp_obj = getattr(tmp_obj, key)
                if (tmp_obj == filter_value) or \
                    (filter_value == False and tmp_obj is None) or \
                    (filter_value == True and tmp_obj is not None):
                    apps.append(app)
            except AttributeError:
                pass
        return apps

    @classmethod
    def get_configuration(cls):
        """
        Helper function for getting all CH config values

        Args:
            -

        Returns:
            dictionary of allvalues.yaml (see values.yaml for a detailed description)

        Usage examples: 
            from cloudharness.utils.config import CloudharnessConfig as conf
            ch_conf = conf.get_configuration()
            workflows = ch_conf['apps']['workflows']
        """
        return cls._get_all_values()

    @classmethod
    def get_applications(cls):
        """
        Helper function for getting all CH apps from allvalues.yaml

        Args:
            -

        Returns:
            dictionary of apps from allvalues.yaml (see values.yaml for a detailed description)

        Usage examples: 
            from cloudharness.utils.config import CloudharnessConfig as conf
            ch_apps = conf.get_applications()
            workflows = ch_apps['worksflows']
        """
        return cls.get_configuration()['apps']
