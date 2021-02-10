from cloudharness.utils.config import CloudharnessConfig, ConfigObject

class ConfigurationCallException(Exception): pass

class ApplicationConfiguration:

    def __init__(self, conf_dict_or_config_object):
        if isinstance(conf_dict_or_config_object, dict):
            self.conf = ConfigObject(conf_dict_or_config_object)
        else:
            self.conf = conf_dict_or_config_object


    @property
    def name(self):
        return self.conf.name

    @property
    def harness(self):
        return self.conf.harness

    def __getitem__(self, key_or_path):
        item = self.conf[key_or_path]
        if (isinstance(item, ConfigObject) or isinstance(item, dict)) and 'harness' in item and item['harness']:
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

    @property
    def service_name(self):
        name = self['harness.service.name']
        if not name:
            raise ConfigurationCallException(f"Cannot get service address for {self.name}: auto service is not enabled")
        return name

    @property
    def service_port(self):
        port = self['harness.service.port']
        if not port:
            raise ConfigurationCallException(f"Cannot get service port for {self.name}: auto service is not enabled")
        return port

    def get_service_address(self):
        return f"http://{self.service_name}.{CloudharnessConfig.get_namespace()}:{self.service_port}"

    def get_public_address(self):

        if not self['harness.subdomain']:
            raise ConfigurationCallException(f"Cannot get public address for {self.name}: no subdomain is specified for this appplication.")
        return f"http{'s' if CloudharnessConfig.is_secured() else ''}://{self['harness.subdomain']}.{CloudharnessConfig.get_domain()}"

def get_configurations(**kwargs):
    return [ApplicationConfiguration(conf) for conf in CloudharnessConfig.get_application_by_filter(**kwargs)]


def get_configuration(app_name) -> ApplicationConfiguration:
    conf = CloudharnessConfig.get_application_by_filter(harness__name=app_name)
    if len(conf) > 1:
        raise ConfigurationCallException(f'Application {app_name} is not unique inside the current deployment.')
    if not conf:
        raise ConfigurationCallException(f'Application {app_name} is not part of the current deployment.')
    return ApplicationConfiguration(conf[0])

