from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.cdc_event_meta import CDCEventMeta
from cloudharness_model import util

from cloudharness_model.models.cdc_event_meta import CDCEventMeta  # noqa: E501

class CDCEvent(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, operation=None, uid=None, message_type=None, resource=None, meta=None):  # noqa: E501
        """CDCEvent - a model defined in OpenAPI

        :param operation: The operation of this CDCEvent.  # noqa: E501
        :type operation: str
        :param uid: The uid of this CDCEvent.  # noqa: E501
        :type uid: str
        :param message_type: The message_type of this CDCEvent.  # noqa: E501
        :type message_type: str
        :param resource: The resource of this CDCEvent.  # noqa: E501
        :type resource: Dict[str, object]
        :param meta: The meta of this CDCEvent.  # noqa: E501
        :type meta: CDCEventMeta
        """
        self.openapi_types = {
            'operation': str,
            'uid': str,
            'message_type': str,
            'resource': Dict[str, object],
            'meta': CDCEventMeta
        }

        self.attribute_map = {
            'operation': 'operation',
            'uid': 'uid',
            'message_type': 'message_type',
            'resource': 'resource',
            'meta': 'meta'
        }

        self._operation = operation
        self._uid = uid
        self._message_type = message_type
        self._resource = resource
        self._meta = meta

    @classmethod
    def from_dict(cls, dikt) -> 'CDCEvent':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The CDCEvent of this CDCEvent.  # noqa: E501
        :rtype: CDCEvent
        """
        return util.deserialize_model(dikt, cls)

    @property
    def operation(self) -> str:
        """Gets the operation of this CDCEvent.

        the operation on the object e.g. create / update / delete  # noqa: E501

        :return: The operation of this CDCEvent.
        :rtype: str
        """
        return self._operation

    @operation.setter
    def operation(self, operation: str):
        """Sets the operation of this CDCEvent.

        the operation on the object e.g. create / update / delete  # noqa: E501

        :param operation: The operation of this CDCEvent.
        :type operation: str
        """
        allowed_values = ["create", "update", "delete", "other"]  # noqa: E501
        if operation not in allowed_values:
            raise ValueError(
                "Invalid value for `operation` ({0}), must be one of {1}"
                .format(operation, allowed_values)
            )

        self._operation = operation

    @property
    def uid(self) -> str:
        """Gets the uid of this CDCEvent.

        the unique identifier attribute of the object  # noqa: E501

        :return: The uid of this CDCEvent.
        :rtype: str
        """
        return self._uid

    @uid.setter
    def uid(self, uid: str):
        """Sets the uid of this CDCEvent.

        the unique identifier attribute of the object  # noqa: E501

        :param uid: The uid of this CDCEvent.
        :type uid: str
        """
        if uid is None:
            raise ValueError("Invalid value for `uid`, must not be `None`")  # noqa: E501

        self._uid = uid

    @property
    def message_type(self) -> str:
        """Gets the message_type of this CDCEvent.

        the type of the message (relates to the object type) e.g. jobs  # noqa: E501

        :return: The message_type of this CDCEvent.
        :rtype: str
        """
        return self._message_type

    @message_type.setter
    def message_type(self, message_type: str):
        """Sets the message_type of this CDCEvent.

        the type of the message (relates to the object type) e.g. jobs  # noqa: E501

        :param message_type: The message_type of this CDCEvent.
        :type message_type: str
        """
        if message_type is None:
            raise ValueError("Invalid value for `message_type`, must not be `None`")  # noqa: E501

        self._message_type = message_type

    @property
    def resource(self) -> Dict[str, object]:
        """Gets the resource of this CDCEvent.

          # noqa: E501

        :return: The resource of this CDCEvent.
        :rtype: Dict[str, object]
        """
        return self._resource

    @resource.setter
    def resource(self, resource: Dict[str, object]):
        """Sets the resource of this CDCEvent.

          # noqa: E501

        :param resource: The resource of this CDCEvent.
        :type resource: Dict[str, object]
        """

        self._resource = resource

    @property
    def meta(self) -> CDCEventMeta:
        """Gets the meta of this CDCEvent.


        :return: The meta of this CDCEvent.
        :rtype: CDCEventMeta
        """
        return self._meta

    @meta.setter
    def meta(self, meta: CDCEventMeta):
        """Sets the meta of this CDCEvent.


        :param meta: The meta of this CDCEvent.
        :type meta: CDCEventMeta
        """
        if meta is None:
            raise ValueError("Invalid value for `meta`, must not be `None`")  # noqa: E501

        self._meta = meta
