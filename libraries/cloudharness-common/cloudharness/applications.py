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
        return self['harness.name']

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

    def is_auto_db(self):
        return self['harness.database.auto']

    def is_sentry_enabled(self):
        return self['harness.sentry']

    def get_db_connection_string(self):
        if not self.is_auto_db():
            raise ConfigurationCallException(f"Cannot get configuration string: application {self.name} has no database enabled.")
        if self.db_type == 'mongo':
            return f"mongodb://{self['harness.database.user']}:{self['harness.database.pass']}@{self.db_name}:{self['harness.database.mongo.ports'][0]['port']}/"
        else:
            raise NotImplementedError(f'Database connection string discovery not yet supported for databse type {self.db_type}')

    @property
    def db_name(self):
        return self['harness.database.name']

    @property
    def image_name(self):
        return self['harness.deployment.image']

    @property
    def db_type(self):
        return self['harness.database.type']
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

