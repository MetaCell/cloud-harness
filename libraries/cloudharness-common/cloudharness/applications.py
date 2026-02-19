from typing import List

from cloudharness.utils.config import CloudharnessConfig, ConfigObject
from cloudharness.models import ApplicationConfig


class ConfigurationCallException(Exception):
    pass


class ApplicationConfiguration(ApplicationConfig):

    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and type(args[0]) == dict:
            return ApplicationConfiguration.from_dict(args[0])
        return super().__new__(cls)

    def __init__(self, *args, **kargs):
        if len(args) == 1 and type(args[0]) == dict:
            self.__conf = None
            return
        ApplicationConfig.__init__(self, *args, **kargs)
        # Set __conf after parent initialization to ensure it's not overwritten
        self.__conf = None

    def is_auto_service(self) -> bool:
        return self.harness.service.auto

    def is_auto_deployment(self) -> bool:
        return self.harness.deployment.auto

    def is_auto_db(self) -> bool:
        return self.harness.database.auto

    def is_sentry_enabled(self) -> bool:
        return self.harness.sentry

    def get_db_connection_string(self, **kwargs) -> str:
        if not self.is_auto_db():
            raise ConfigurationCallException(
                f"Cannot get configuration string: application {self.name} has no database enabled.")
        if self.db_type == 'mongo':
            return f"mongodb://{self.harness.database.user}:{self.harness.database['pass']}@{self.db_name}:{self.harness.database.mongo.ports[0]['port']}/"
        elif self.db_type == 'postgres':
            database_name = kwargs.get('database_name', self.harness.database.postgres['initialdb'])
            return f"postgres://{self.db_name}:{self.harness.database.postgres.ports[0]['port']}/" \
                f"{database_name}?user={self.harness.database.user}&password={self.harness.database['pass']}"
        elif self.db_type == 'neo4j':
            return f"{self.harness.database.neo4j.get('ports')[1]['name']}://{self.db_name}:" \
                f"{self.harness.database.neo4j.get('ports')[1]['port']}/"
        else:
            raise NotImplementedError(
                f'Database connection string discovery not yet supported for database type {self.db_type}')

    @property
    def db_name(self) -> str:
        return self.harness.database.name

    @property
    def conf(self):
        """
        Legacy object
        """
        if self.__conf is None:
            self.__conf = ConfigObject(self.to_dict())
        return self.__conf

    @property
    def image_name(self) -> str:
        return self.harness.deployment.image

    @property
    def db_type(self) -> str:
        return self.harness.database.type

    @property
    def service_name(self) -> str:
        name = self.harness.service.name
        if not name:
            raise ConfigurationCallException(
                f"Cannot get service address for {self.name}: auto service is not enabled")
        return name

    @property
    def service_port(self) -> int:
        port = self.harness.service.port
        if not port:
            raise ConfigurationCallException(
                f"Cannot get service port for {self.name}: auto service is not enabled")
        return port

    def get_service_address(self, prefix="http://") -> str:
        return f"{prefix}{self.service_name}.{CloudharnessConfig.get_namespace()}:{self.service_port}"

    def get_public_address(self) -> str:

        if not self.harness.subdomain:
            raise ConfigurationCallException(
                f"Cannot get public address for {self.name}: no subdomain is specified for this appplication.")
        return f"http{'s' if CloudharnessConfig.is_secured() else ''}://{self.harness.subdomain}.{CloudharnessConfig.get_domain()}"


def get_configurations(**kwargs) -> List[ApplicationConfiguration]:
    return [ApplicationConfiguration(conf) for conf in CloudharnessConfig.get_application_by_filter(**kwargs)]


def get_configuration(app_name) -> ApplicationConfiguration:
    conf = CloudharnessConfig.get_application_by_filter(harness__name=app_name)
    if len(conf) > 1:
        raise ConfigurationCallException(
            f'Application {app_name} is not unique inside the current deployment.')
    if not conf:
        raise ConfigurationCallException(
            f'Application {app_name} is not part of the current deployment.')
    return ApplicationConfiguration.from_dict(conf[0])


def get_current_configuration() -> ApplicationConfiguration:
    """
    Get the configuration for the "current" application

    Returns:
        ApplicationConfiguration
    """
    try:
        return get_configuration(CloudharnessConfig.get_current_app_name())
    except Exception as e:
        raise ConfigurationCallException(
            f'Configuration error: cannot find current app - check env variable CH_CURRENT_APP_NAME') from e
