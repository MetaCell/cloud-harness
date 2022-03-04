import pprint

import six
import typing

from cloudharness_model import util

T = typing.TypeVar('T')


class Model(object):
    # openapiTypes: The key is attribute name and the
    # value is attribute type.
    openapi_types = {}

    # attributeMap: The key is attribute name and the
    # value is json key in definition.
    attribute_map = {}

    def __init__(self):
        self._raw_dict = {}

    @classmethod
    def from_dict(cls: typing.Type[T], dikt) -> T:
        """Returns the dict as a model"""
        obj = util.deserialize_model(dikt, cls)
        return obj

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        return self._raw_dict[key]

    def get(self, key, _default=None):
        if key in self:
            return self[key]
        return _default
    
    def __contains__(self, key):
        if key in self.attribute_map:
            return True
        elif hasattr(self, "_raw_dict"):
            return  key in self._raw_dict
        return False

    def to_dict(self):
        """Returns the model properties as a dict
        :rtype: dict
        """
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        if hasattr(self, "raw_dict"):
            merged = dict(self.raw_dict)
            merged.update(result)
            return merged
        return result

    def to_str(self):
        """Returns the string representation of the model
        :rtype: str
        """
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other