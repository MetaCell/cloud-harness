import yaml

ALLVALUES_PATH = '/opt/cloudharness/resources/allvalues.yaml'

class _ConfigObject(object):
    def __init__(self, dictionary):
        for key, val in dictionary.items():
            if isinstance(val, (list, tuple)):
               setattr(self, key, [_ConfigObject(x) if isinstance(x, dict) else x for x in val])
            else:
               setattr(self, key, _ConfigObject(val) if isinstance(val, dict) else val)

class _CloudharnessConfig:
    def __init__(self):
        with open(ALLVALUES_PATH) as f:
            self.allvalues = yaml.safe_load(f)
        self.apps = _ConfigObject(self.allvalues['apps'])


    def get_application_by_filter(self,**filter):
        """
        Helper function for filtering CH app objects

        Args:
            filter: the filter e.g. harness__deployment__auto=True

        Returns:
            list of app objects (see values.yaml for a detailed description)

        Usage examples: 
            from cloudharness.utils.config import conf
            conf.get_application_by_filter(harness__deployment__auto=True)
            conf.get_application_by_filter(name='workflows')
        """
        apps=[]
        filter_keys = next(iter(filter)).split('__')
        filter_value = next(iter(filter.values()))
        for app_key in self.get_applications():
            app = getattr(self.apps, app_key)
            tmp_obj = app
            for key in (key for key in filter_keys if hasattr(tmp_obj, key)):
                tmp_obj = getattr(tmp_obj, key)
                if tmp_obj == filter_value:
                    apps.append(app)
                    break
        return apps

    
    def get_configuration(self):
        """
        Helper function for getting all CH config values

        Args:
            -

        Returns:
            dictionary of allvalues.yaml (see values.yaml for a detailed description)

        Usage examples: 
            from cloudharness.utils.config import conf
            ch_conf = conf.get_configuration()
            workflows = ch_conf['apps']['workflows']
        """
        return self.allvalues


    def get_applications(self):
        """
        Helper function for getting all CH apps from allvalues.yaml

        Args:
            -

        Returns:
            dictionary of apps from allvalues.yaml (see values.yaml for a detailed description)

        Usage examples: 
            from cloudharness.utils.config import conf
            ch_apps = conf.get_applications()
            workflows = ch_apps['worksflows']
        """
        return self.allvalues['apps']

conf = _CloudharnessConfig()
