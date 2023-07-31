# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model import util


class ApplicationProbe(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, path=None, period_seconds=None, failure_threshold=None, initial_delay_seconds=None):  # noqa: E501
        """ApplicationProbe - a model defined in OpenAPI

        :param path: The path of this ApplicationProbe.  # noqa: E501
        :type path: str
        :param period_seconds: The period_seconds of this ApplicationProbe.  # noqa: E501
        :type period_seconds: float
        :param failure_threshold: The failure_threshold of this ApplicationProbe.  # noqa: E501
        :type failure_threshold: float
        :param initial_delay_seconds: The initial_delay_seconds of this ApplicationProbe.  # noqa: E501
        :type initial_delay_seconds: float
        """
        self.openapi_types = {
            'path': str,
            'period_seconds': float,
            'failure_threshold': float,
            'initial_delay_seconds': float
        }

        self.attribute_map = {
            'path': 'path',
            'period_seconds': 'periodSeconds',
            'failure_threshold': 'failureThreshold',
            'initial_delay_seconds': 'initialDelaySeconds'
        }

        self._path = path
        self._period_seconds = period_seconds
        self._failure_threshold = failure_threshold
        self._initial_delay_seconds = initial_delay_seconds

    @classmethod
    def from_dict(cls, dikt) -> 'ApplicationProbe':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The ApplicationProbe of this ApplicationProbe.  # noqa: E501
        :rtype: ApplicationProbe
        """
        return util.deserialize_model(dikt, cls)

    @property
    def path(self):
        """Gets the path of this ApplicationProbe.

          # noqa: E501

        :return: The path of this ApplicationProbe.
        :rtype: str
        """
        return self._path

    @path.setter
    def path(self, path):
        """Sets the path of this ApplicationProbe.

          # noqa: E501

        :param path: The path of this ApplicationProbe.
        :type path: str
        """
        if path is None:
            raise ValueError("Invalid value for `path`, must not be `None`")  # noqa: E501

        self._path = path

    @property
    def period_seconds(self):
        """Gets the period_seconds of this ApplicationProbe.

          # noqa: E501

        :return: The period_seconds of this ApplicationProbe.
        :rtype: float
        """
        return self._period_seconds

    @period_seconds.setter
    def period_seconds(self, period_seconds):
        """Sets the period_seconds of this ApplicationProbe.

          # noqa: E501

        :param period_seconds: The period_seconds of this ApplicationProbe.
        :type period_seconds: float
        """

        self._period_seconds = period_seconds

    @property
    def failure_threshold(self):
        """Gets the failure_threshold of this ApplicationProbe.

          # noqa: E501

        :return: The failure_threshold of this ApplicationProbe.
        :rtype: float
        """
        return self._failure_threshold

    @failure_threshold.setter
    def failure_threshold(self, failure_threshold):
        """Sets the failure_threshold of this ApplicationProbe.

          # noqa: E501

        :param failure_threshold: The failure_threshold of this ApplicationProbe.
        :type failure_threshold: float
        """

        self._failure_threshold = failure_threshold

    @property
    def initial_delay_seconds(self):
        """Gets the initial_delay_seconds of this ApplicationProbe.

          # noqa: E501

        :return: The initial_delay_seconds of this ApplicationProbe.
        :rtype: float
        """
        return self._initial_delay_seconds

    @initial_delay_seconds.setter
    def initial_delay_seconds(self, initial_delay_seconds):
        """Sets the initial_delay_seconds of this ApplicationProbe.

          # noqa: E501

        :param initial_delay_seconds: The initial_delay_seconds of this ApplicationProbe.
        :type initial_delay_seconds: float
        """

        self._initial_delay_seconds = initial_delay_seconds
