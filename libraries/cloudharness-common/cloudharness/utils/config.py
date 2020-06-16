import yaml

ALLVALUES_PATH = '/opt/cloudharness/resources/allvalues.yaml'

class _ConfigObject(object):
    def __init__(self, dictionary):
        for key, val in dictionary.items():
            if isinstance(val, (list, tuple)):
               setattr(self, key, [_ConfigObject(x) if isinstance(x, dict) else x for x in val])
            else:
               setattr(self, key, _ConfigObject(val) if isinstance(val, dict) else val)

class CloudharnessConfig:
    @classmethod
    def _get_all_values(cls):
        if not hasattr(cls, 'allvalues'):
            with open(ALLVALUES_PATH) as f:
                cls.allvalues = yaml.safe_load(f)
        return cls.allvalues

    
    @classmethod
    def _get_apps(cls):
        if not hasattr(cls, 'apps'):
            cls.apps = _ConfigObject(cls._get_all_values()['apps'])
        return cls.apps
        

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
        apps=[]
        filter_keys = next(iter(filter)).split('__')
        filter_value = next(iter(filter.values()))
        all_apps = cls._get_apps()
        for app_key in cls.get_applications():
            app = getattr(all_apps, app_key)
            tmp_obj = app
            for key in (key for key in filter_keys if hasattr(tmp_obj, key)):
                tmp_obj = getattr(tmp_obj, key)
                if tmp_obj == filter_value:
                    apps.append(app)
                    break
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
