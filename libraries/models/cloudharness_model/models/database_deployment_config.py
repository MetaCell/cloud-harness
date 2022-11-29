# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.deployment_resources_conf import DeploymentResourcesConf
import re
from cloudharness_model import util

from cloudharness_model.models.deployment_resources_conf import DeploymentResourcesConf  # noqa: E501
import re  # noqa: E501

class DatabaseDeploymentConfig(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, type=None, size=None, user=None, _pass=None, image_ref=None, mongo=None, postgres=None, neo4j=None, resources=None, auto=None, name=None):  # noqa: E501
        """DatabaseDeploymentConfig - a model defined in OpenAPI

        :param type: The type of this DatabaseDeploymentConfig.  # noqa: E501
        :type type: str
        :param size: The size of this DatabaseDeploymentConfig.  # noqa: E501
        :type size: str
        :param user: The user of this DatabaseDeploymentConfig.  # noqa: E501
        :type user: str
        :param _pass: The _pass of this DatabaseDeploymentConfig.  # noqa: E501
        :type _pass: str
        :param image_ref: The image_ref of this DatabaseDeploymentConfig.  # noqa: E501
        :type image_ref: str
        :param mongo: The mongo of this DatabaseDeploymentConfig.  # noqa: E501
        :type mongo: Dict[str, object]
        :param postgres: The postgres of this DatabaseDeploymentConfig.  # noqa: E501
        :type postgres: Dict[str, object]
        :param neo4j: The neo4j of this DatabaseDeploymentConfig.  # noqa: E501
        :type neo4j: object
        :param resources: The resources of this DatabaseDeploymentConfig.  # noqa: E501
        :type resources: DeploymentResourcesConf
        :param auto: The auto of this DatabaseDeploymentConfig.  # noqa: E501
        :type auto: bool
        :param name: The name of this DatabaseDeploymentConfig.  # noqa: E501
        :type name: str
        """
        self.openapi_types = {
            'type': str,
            'size': str,
            'user': str,
            '_pass': str,
            'image_ref': str,
            'mongo': Dict[str, object],
            'postgres': Dict[str, object],
            'neo4j': object,
            'resources': DeploymentResourcesConf,
            'auto': bool,
            'name': str
        }

        self.attribute_map = {
            'type': 'type',
            'size': 'size',
            'user': 'user',
            '_pass': 'pass',
            'image_ref': 'image_ref',
            'mongo': 'mongo',
            'postgres': 'postgres',
            'neo4j': 'neo4j',
            'resources': 'resources',
            'auto': 'auto',
            'name': 'name'
        }

        self._type = type
        self._size = size
        self._user = user
        self.__pass = _pass
        self._image_ref = image_ref
        self._mongo = mongo
        self._postgres = postgres
        self._neo4j = neo4j
        self._resources = resources
        self._auto = auto
        self._name = name

    @classmethod
    def from_dict(cls, dikt) -> 'DatabaseDeploymentConfig':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The DatabaseDeploymentConfig of this DatabaseDeploymentConfig.  # noqa: E501
        :rtype: DatabaseDeploymentConfig
        """
        return util.deserialize_model(dikt, cls)

    @property
    def type(self):
        """Gets the type of this DatabaseDeploymentConfig.

        Define the database type.  One of (mongo, postgres, neo4j, sqlite3)  # noqa: E501

        :return: The type of this DatabaseDeploymentConfig.
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this DatabaseDeploymentConfig.

        Define the database type.  One of (mongo, postgres, neo4j, sqlite3)  # noqa: E501

        :param type: The type of this DatabaseDeploymentConfig.
        :type type: str
        """
        if type is not None and not re.search(r'^(mongo|postgres|neo4j|sqlite3)$', type):  # noqa: E501
            raise ValueError("Invalid value for `type`, must be a follow pattern or equal to `/^(mongo|postgres|neo4j|sqlite3)$/`")  # noqa: E501

        self._type = type

    @property
    def size(self):
        """Gets the size of this DatabaseDeploymentConfig.

        Specify database disk size  # noqa: E501

        :return: The size of this DatabaseDeploymentConfig.
        :rtype: str
        """
        return self._size

    @size.setter
    def size(self, size):
        """Sets the size of this DatabaseDeploymentConfig.

        Specify database disk size  # noqa: E501

        :param size: The size of this DatabaseDeploymentConfig.
        :type size: str
        """

        self._size = size

    @property
    def user(self):
        """Gets the user of this DatabaseDeploymentConfig.

        database username  # noqa: E501

        :return: The user of this DatabaseDeploymentConfig.
        :rtype: str
        """
        return self._user

    @user.setter
    def user(self, user):
        """Sets the user of this DatabaseDeploymentConfig.

        database username  # noqa: E501

        :param user: The user of this DatabaseDeploymentConfig.
        :type user: str
        """

        self._user = user

    @property
    def _pass(self):
        """Gets the _pass of this DatabaseDeploymentConfig.

        Database password  # noqa: E501

        :return: The _pass of this DatabaseDeploymentConfig.
        :rtype: str
        """
        return self.__pass

    @_pass.setter
    def _pass(self, _pass):
        """Sets the _pass of this DatabaseDeploymentConfig.

        Database password  # noqa: E501

        :param _pass: The _pass of this DatabaseDeploymentConfig.
        :type _pass: str
        """

        self.__pass = _pass

    @property
    def image_ref(self):
        """Gets the image_ref of this DatabaseDeploymentConfig.

        Used for referencing images from the build  # noqa: E501

        :return: The image_ref of this DatabaseDeploymentConfig.
        :rtype: str
        """
        return self._image_ref

    @image_ref.setter
    def image_ref(self, image_ref):
        """Sets the image_ref of this DatabaseDeploymentConfig.

        Used for referencing images from the build  # noqa: E501

        :param image_ref: The image_ref of this DatabaseDeploymentConfig.
        :type image_ref: str
        """

        self._image_ref = image_ref

    @property
    def mongo(self):
        """Gets the mongo of this DatabaseDeploymentConfig.

          # noqa: E501

        :return: The mongo of this DatabaseDeploymentConfig.
        :rtype: Dict[str, object]
        """
        return self._mongo

    @mongo.setter
    def mongo(self, mongo):
        """Sets the mongo of this DatabaseDeploymentConfig.

          # noqa: E501

        :param mongo: The mongo of this DatabaseDeploymentConfig.
        :type mongo: Dict[str, object]
        """

        self._mongo = mongo

    @property
    def postgres(self):
        """Gets the postgres of this DatabaseDeploymentConfig.

          # noqa: E501

        :return: The postgres of this DatabaseDeploymentConfig.
        :rtype: Dict[str, object]
        """
        return self._postgres

    @postgres.setter
    def postgres(self, postgres):
        """Sets the postgres of this DatabaseDeploymentConfig.

          # noqa: E501

        :param postgres: The postgres of this DatabaseDeploymentConfig.
        :type postgres: Dict[str, object]
        """

        self._postgres = postgres

    @property
    def neo4j(self):
        """Gets the neo4j of this DatabaseDeploymentConfig.

        Neo4j database specific configuration  # noqa: E501

        :return: The neo4j of this DatabaseDeploymentConfig.
        :rtype: object
        """
        return self._neo4j

    @neo4j.setter
    def neo4j(self, neo4j):
        """Sets the neo4j of this DatabaseDeploymentConfig.

        Neo4j database specific configuration  # noqa: E501

        :param neo4j: The neo4j of this DatabaseDeploymentConfig.
        :type neo4j: object
        """

        self._neo4j = neo4j

    @property
    def resources(self):
        """Gets the resources of this DatabaseDeploymentConfig.


        :return: The resources of this DatabaseDeploymentConfig.
        :rtype: DeploymentResourcesConf
        """
        return self._resources

    @resources.setter
    def resources(self, resources):
        """Sets the resources of this DatabaseDeploymentConfig.


        :param resources: The resources of this DatabaseDeploymentConfig.
        :type resources: DeploymentResourcesConf
        """

        self._resources = resources

    @property
    def auto(self):
        """Gets the auto of this DatabaseDeploymentConfig.

        When true, enables automatic template  # noqa: E501

        :return: The auto of this DatabaseDeploymentConfig.
        :rtype: bool
        """
        return self._auto

    @auto.setter
    def auto(self, auto):
        """Sets the auto of this DatabaseDeploymentConfig.

        When true, enables automatic template  # noqa: E501

        :param auto: The auto of this DatabaseDeploymentConfig.
        :type auto: bool
        """
        if auto is None:
            raise ValueError("Invalid value for `auto`, must not be `None`")  # noqa: E501

        self._auto = auto

    @property
    def name(self):
        """Gets the name of this DatabaseDeploymentConfig.

          # noqa: E501

        :return: The name of this DatabaseDeploymentConfig.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this DatabaseDeploymentConfig.

          # noqa: E501

        :param name: The name of this DatabaseDeploymentConfig.
        :type name: str
        """

        self._name = name
