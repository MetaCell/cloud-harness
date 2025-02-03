from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from samples.models.base_model import Model
from samples import util


class InlineResponse202Task(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, href=None, name=None):  # noqa: E501
        """InlineResponse202Task - a model defined in OpenAPI

        :param href: The href of this InlineResponse202Task.  # noqa: E501
        :type href: str
        :param name: The name of this InlineResponse202Task.  # noqa: E501
        :type name: str
        """
        self.openapi_types = {
            'href': str,
            'name': str
        }

        self.attribute_map = {
            'href': 'href',
            'name': 'name'
        }

        self._href = href
        self._name = name

    @classmethod
    def from_dict(cls, dikt) -> 'InlineResponse202Task':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The inline_response_202_task of this InlineResponse202Task.  # noqa: E501
        :rtype: InlineResponse202Task
        """
        return util.deserialize_model(dikt, cls)

    @property
    def href(self) -> str:
        """Gets the href of this InlineResponse202Task.

        the url where to check the operation status  # noqa: E501

        :return: The href of this InlineResponse202Task.
        :rtype: str
        """
        return self._href

    @href.setter
    def href(self, href: str):
        """Sets the href of this InlineResponse202Task.

        the url where to check the operation status  # noqa: E501

        :param href: The href of this InlineResponse202Task.
        :type href: str
        """

        self._href = href

    @property
    def name(self) -> str:
        """Gets the name of this InlineResponse202Task.


        :return: The name of this InlineResponse202Task.
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: str):
        """Sets the name of this InlineResponse202Task.


        :param name: The name of this InlineResponse202Task.
        :type name: str
        """

        self._name = name
