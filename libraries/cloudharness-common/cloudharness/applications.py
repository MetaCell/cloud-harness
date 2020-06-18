from cloudharness.utils.config import CloudharnessConfig, ConfigObject


class ApplicationConfiguration:

    def __init__(self, conf_dict_or_config_object):
        if isinstance(conf_dict_or_config_object, dict):
            self.conf = ConfigObject(conf_dict_or_config_object)
        else:
            self.conf = conf_dict_or_config_object
        self.name = self.conf.name
        self.harness = self.conf.harness

    def __getitem__(self, key_or_path):
        item = self.conf[key_or_path]
        if (isinstance(item, ConfigObject) or isinstance(item, dict)) and item['harness']:
            item = ApplicationConfiguration(item)
        return item

    def __getattr__(self, item):
        return self[item]

    def is_auto_service(self):
        return self['harness.service.auto']

    def is_auto_deployment(self):
        return self['harness.deployment.auto']

    def is_sentry_enabled(self):
        return self['harness.sentry']


def get_configurations(**kwargs):
    return [ApplicationConfiguration(conf) for conf in CloudharnessConfig.get_application_by_filter(**kwargs)]


def get_configuration(app_name):
    conf = CloudharnessConfig.get_application_by_filter(name=app_name)
    if conf:
        if len(conf) > 1:
            raise Exception(f'More than one app with the same name is not allowed. Found {len(conf)} applications with name {app_name}')
        return ApplicationConfiguration(conf[0])
