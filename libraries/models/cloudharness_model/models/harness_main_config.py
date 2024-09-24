from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.application_config import ApplicationConfig
from cloudharness_model.models.backup_config import BackupConfig
from cloudharness_model.models.name_value import NameValue
from cloudharness_model.models.registry_config import RegistryConfig
from cloudharness_model import util

from cloudharness_model.models.application_config import ApplicationConfig  # noqa: E501
from cloudharness_model.models.backup_config import BackupConfig  # noqa: E501
from cloudharness_model.models.name_value import NameValue  # noqa: E501
from cloudharness_model.models.registry_config import RegistryConfig  # noqa: E501

class HarnessMainConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, local=None, secured_gatekeepers=None, domain=None, namespace=None, mainapp=None, registry=None, tag=None, apps=None, env=None, privenv=None, backup=None, name=None, task_images=None, build_hash=None):  # noqa: E501
        """HarnessMainConfig - a model defined in OpenAPI

        :param local: The local of this HarnessMainConfig.  # noqa: E501
        :type local: bool
        :param secured_gatekeepers: The secured_gatekeepers of this HarnessMainConfig.  # noqa: E501
        :type secured_gatekeepers: bool
        :param domain: The domain of this HarnessMainConfig.  # noqa: E501
        :type domain: str
        :param namespace: The namespace of this HarnessMainConfig.  # noqa: E501
        :type namespace: str
        :param mainapp: The mainapp of this HarnessMainConfig.  # noqa: E501
        :type mainapp: str
        :param registry: The registry of this HarnessMainConfig.  # noqa: E501
        :type registry: RegistryConfig
        :param tag: The tag of this HarnessMainConfig.  # noqa: E501
        :type tag: str
        :param apps: The apps of this HarnessMainConfig.  # noqa: E501
        :type apps: Dict[str, ApplicationConfig]
        :param env: The env of this HarnessMainConfig.  # noqa: E501
        :type env: List[NameValue]
        :param privenv: The privenv of this HarnessMainConfig.  # noqa: E501
        :type privenv: NameValue
        :param backup: The backup of this HarnessMainConfig.  # noqa: E501
        :type backup: BackupConfig
        :param name: The name of this HarnessMainConfig.  # noqa: E501
        :type name: str
        :param task_images: The task_images of this HarnessMainConfig.  # noqa: E501
        :type task_images: Dict[str, object]
        :param build_hash: The build_hash of this HarnessMainConfig.  # noqa: E501
        :type build_hash: str
        """
        self.openapi_types = {
            'local': bool,
            'secured_gatekeepers': bool,
            'domain': str,
            'namespace': str,
            'mainapp': str,
            'registry': RegistryConfig,
            'tag': str,
            'apps': Dict[str, ApplicationConfig],
            'env': List[NameValue],
            'privenv': NameValue,
            'backup': BackupConfig,
            'name': str,
            'task_images': Dict[str, object],
            'build_hash': str
        }

        self.attribute_map = {
            'local': 'local',
            'secured_gatekeepers': 'secured_gatekeepers',
            'domain': 'domain',
            'namespace': 'namespace',
            'mainapp': 'mainapp',
            'registry': 'registry',
            'tag': 'tag',
            'apps': 'apps',
            'env': 'env',
            'privenv': 'privenv',
            'backup': 'backup',
            'name': 'name',
            'task_images': 'task-images',
            'build_hash': 'build_hash'
        }

        self._local = local
        self._secured_gatekeepers = secured_gatekeepers
        self._domain = domain
        self._namespace = namespace
        self._mainapp = mainapp
        self._registry = registry
        self._tag = tag
        self._apps = apps
        self._env = env
        self._privenv = privenv
        self._backup = backup
        self._name = name
        self._task_images = task_images
        self._build_hash = build_hash

    @classmethod
    def from_dict(cls, dikt) -> 'HarnessMainConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The HarnessMainConfig of this HarnessMainConfig.  # noqa: E501
        :rtype: HarnessMainConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def local(self) -> bool:
        """Gets the local of this HarnessMainConfig.

        If set to true, local DNS mapping is added to pods.  # noqa: E501

        :return: The local of this HarnessMainConfig.
        :rtype: bool
        """
        return self._local

    @local.setter
    def local(self, local: bool):
        """Sets the local of this HarnessMainConfig.

        If set to true, local DNS mapping is added to pods.  # noqa: E501

        :param local: The local of this HarnessMainConfig.
        :type local: bool
        """
        if local is None:
            raise ValueError("Invalid value for `local`, must not be `None`")  # noqa: E501

        self._local = local

    @property
    def secured_gatekeepers(self) -> bool:
        """Gets the secured_gatekeepers of this HarnessMainConfig.

        Enables/disables Gatekeepers on secured applications. Set to false for testing/development  # noqa: E501

        :return: The secured_gatekeepers of this HarnessMainConfig.
        :rtype: bool
        """
        return self._secured_gatekeepers

    @secured_gatekeepers.setter
    def secured_gatekeepers(self, secured_gatekeepers: bool):
        """Sets the secured_gatekeepers of this HarnessMainConfig.

        Enables/disables Gatekeepers on secured applications. Set to false for testing/development  # noqa: E501

        :param secured_gatekeepers: The secured_gatekeepers of this HarnessMainConfig.
        :type secured_gatekeepers: bool
        """
        if secured_gatekeepers is None:
            raise ValueError("Invalid value for `secured_gatekeepers`, must not be `None`")  # noqa: E501

        self._secured_gatekeepers = secured_gatekeepers

    @property
    def domain(self) -> str:
        """Gets the domain of this HarnessMainConfig.

        The root domain  # noqa: E501

        :return: The domain of this HarnessMainConfig.
        :rtype: str
        """
        return self._domain

    @domain.setter
    def domain(self, domain: str):
        """Sets the domain of this HarnessMainConfig.

        The root domain  # noqa: E501

        :param domain: The domain of this HarnessMainConfig.
        :type domain: str
        """
        if domain is None:
            raise ValueError("Invalid value for `domain`, must not be `None`")  # noqa: E501

        self._domain = domain

    @property
    def namespace(self) -> str:
        """Gets the namespace of this HarnessMainConfig.

        The K8s namespace.  # noqa: E501

        :return: The namespace of this HarnessMainConfig.
        :rtype: str
        """
        return self._namespace

    @namespace.setter
    def namespace(self, namespace: str):
        """Sets the namespace of this HarnessMainConfig.

        The K8s namespace.  # noqa: E501

        :param namespace: The namespace of this HarnessMainConfig.
        :type namespace: str
        """
        if namespace is None:
            raise ValueError("Invalid value for `namespace`, must not be `None`")  # noqa: E501

        self._namespace = namespace

    @property
    def mainapp(self) -> str:
        """Gets the mainapp of this HarnessMainConfig.

        Defines the app to map to the root domain  # noqa: E501

        :return: The mainapp of this HarnessMainConfig.
        :rtype: str
        """
        return self._mainapp

    @mainapp.setter
    def mainapp(self, mainapp: str):
        """Sets the mainapp of this HarnessMainConfig.

        Defines the app to map to the root domain  # noqa: E501

        :param mainapp: The mainapp of this HarnessMainConfig.
        :type mainapp: str
        """
        if mainapp is None:
            raise ValueError("Invalid value for `mainapp`, must not be `None`")  # noqa: E501

        self._mainapp = mainapp

    @property
    def registry(self) -> RegistryConfig:
        """Gets the registry of this HarnessMainConfig.


        :return: The registry of this HarnessMainConfig.
        :rtype: RegistryConfig
        """
        return self._registry

    @registry.setter
    def registry(self, registry: RegistryConfig):
        """Sets the registry of this HarnessMainConfig.


        :param registry: The registry of this HarnessMainConfig.
        :type registry: RegistryConfig
        """

        self._registry = registry

    @property
    def tag(self) -> str:
        """Gets the tag of this HarnessMainConfig.

        Docker tag used to push/pull the built images.  # noqa: E501

        :return: The tag of this HarnessMainConfig.
        :rtype: str
        """
        return self._tag

    @tag.setter
    def tag(self, tag: str):
        """Sets the tag of this HarnessMainConfig.

        Docker tag used to push/pull the built images.  # noqa: E501

        :param tag: The tag of this HarnessMainConfig.
        :type tag: str
        """

        self._tag = tag

    @property
    def apps(self) -> Dict[str, ApplicationConfig]:
        """Gets the apps of this HarnessMainConfig.

          # noqa: E501

        :return: The apps of this HarnessMainConfig.
        :rtype: Dict[str, ApplicationConfig]
        """
        return self._apps

    @apps.setter
    def apps(self, apps: Dict[str, ApplicationConfig]):
        """Sets the apps of this HarnessMainConfig.

          # noqa: E501

        :param apps: The apps of this HarnessMainConfig.
        :type apps: Dict[str, ApplicationConfig]
        """
        if apps is None:
            raise ValueError("Invalid value for `apps`, must not be `None`")  # noqa: E501

        self._apps = apps

    @property
    def env(self) -> List[NameValue]:
        """Gets the env of this HarnessMainConfig.

        Environmental variables added to all pods  # noqa: E501

        :return: The env of this HarnessMainConfig.
        :rtype: List[NameValue]
        """
        return self._env

    @env.setter
    def env(self, env: List[NameValue]):
        """Sets the env of this HarnessMainConfig.

        Environmental variables added to all pods  # noqa: E501

        :param env: The env of this HarnessMainConfig.
        :type env: List[NameValue]
        """

        self._env = env

    @property
    def privenv(self) -> NameValue:
        """Gets the privenv of this HarnessMainConfig.


        :return: The privenv of this HarnessMainConfig.
        :rtype: NameValue
        """
        return self._privenv

    @privenv.setter
    def privenv(self, privenv: NameValue):
        """Sets the privenv of this HarnessMainConfig.


        :param privenv: The privenv of this HarnessMainConfig.
        :type privenv: NameValue
        """

        self._privenv = privenv

    @property
    def backup(self) -> BackupConfig:
        """Gets the backup of this HarnessMainConfig.


        :return: The backup of this HarnessMainConfig.
        :rtype: BackupConfig
        """
        return self._backup

    @backup.setter
    def backup(self, backup: BackupConfig):
        """Sets the backup of this HarnessMainConfig.


        :param backup: The backup of this HarnessMainConfig.
        :type backup: BackupConfig
        """

        self._backup = backup

    @property
    def name(self) -> str:
        """Gets the name of this HarnessMainConfig.

        Base name  # noqa: E501

        :return: The name of this HarnessMainConfig.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this HarnessMainConfig.

        Base name  # noqa: E501

        :param name: The name of this HarnessMainConfig.
        :type name: str
        """

        self._name = name

    @property
    def task_images(self) -> Dict[str, object]:
        """Gets the task_images of this HarnessMainConfig.

          # noqa: E501

        :return: The task_images of this HarnessMainConfig.
        :rtype: Dict[str, object]
        """
        return self._task_images

    @task_images.setter
    def task_images(self, task_images: Dict[str, object]):
        """Sets the task_images of this HarnessMainConfig.

          # noqa: E501

        :param task_images: The task_images of this HarnessMainConfig.
        :type task_images: Dict[str, object]
        """

        self._task_images = task_images

    @property
    def build_hash(self) -> str:
        """Gets the build_hash of this HarnessMainConfig.

          # noqa: E501

        :return: The build_hash of this HarnessMainConfig.
        :rtype: str
        """
        return self._build_hash

    @build_hash.setter
    def build_hash(self, build_hash: str):
        """Sets the build_hash of this HarnessMainConfig.

          # noqa: E501

        :param build_hash: The build_hash of this HarnessMainConfig.
        :type build_hash: str
        """

        self._build_hash = build_hash
