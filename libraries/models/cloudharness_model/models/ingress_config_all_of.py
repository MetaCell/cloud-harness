# coding: utf-8

from __future__ import absolute_import
from datetime import date, datetime  # noqa: F401

from typing import List, Dict  # noqa: F401

from cloudharness_model.models.base_model_ import Model
from cloudharness_model.models.ingress_config_all_of_letsencrypt import IngressConfigAllOfLetsencrypt
from cloudharness_model import util

from cloudharness_model.models.ingress_config_all_of_letsencrypt import IngressConfigAllOfLetsencrypt  # noqa: E501

class IngressConfigAllOf(Model):
    """NOTE: This class is auto generated by OpenAPI Generator (https://openapi-generator.tech).

    Do not edit the class manually.
    """

    def __init__(self, ssl_redirect=None, letsencrypt=None):  # noqa: E501
        """IngressConfigAllOf - a model defined in OpenAPI

        :param ssl_redirect: The ssl_redirect of this IngressConfigAllOf.  # noqa: E501
        :type ssl_redirect: bool
        :param letsencrypt: The letsencrypt of this IngressConfigAllOf.  # noqa: E501
        :type letsencrypt: IngressConfigAllOfLetsencrypt
        """
        self.openapi_types = {
            'ssl_redirect': bool,
            'letsencrypt': IngressConfigAllOfLetsencrypt
        }

        self.attribute_map = {
            'ssl_redirect': 'ssl_redirect',
            'letsencrypt': 'letsencrypt'
        }

        self._ssl_redirect = ssl_redirect
        self._letsencrypt = letsencrypt

    @classmethod
    def from_dict(cls, dikt) -> 'IngressConfigAllOf':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The IngressConfig_allOf of this IngressConfigAllOf.  # noqa: E501
        :rtype: IngressConfigAllOf
        """
        return util.deserialize_model(dikt, cls)

    @property
    def ssl_redirect(self):
        """Gets the ssl_redirect of this IngressConfigAllOf.


        :return: The ssl_redirect of this IngressConfigAllOf.
        :rtype: bool
        """
        return self._ssl_redirect

    @ssl_redirect.setter
    def ssl_redirect(self, ssl_redirect):
        """Sets the ssl_redirect of this IngressConfigAllOf.


        :param ssl_redirect: The ssl_redirect of this IngressConfigAllOf.
        :type ssl_redirect: bool
        """

        self._ssl_redirect = ssl_redirect

    @property
    def letsencrypt(self):
        """Gets the letsencrypt of this IngressConfigAllOf.


        :return: The letsencrypt of this IngressConfigAllOf.
        :rtype: IngressConfigAllOfLetsencrypt
        """
        return self._letsencrypt

    @letsencrypt.setter
    def letsencrypt(self, letsencrypt):
        """Sets the letsencrypt of this IngressConfigAllOf.


        :param letsencrypt: The letsencrypt of this IngressConfigAllOf.
        :type letsencrypt: IngressConfigAllOfLetsencrypt
        """

        self._letsencrypt = letsencrypt