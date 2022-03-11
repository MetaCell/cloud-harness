import pprint

import six
import typing
import json

from cloudharness_model import util

T = typing.TypeVar('T')

import humps

class Model(object):
    # openapiTypes: The key is attribute name and the
    # value is attribute type.
    openapi_types = {}

    # attributeMap: The key is attribute name and the
    # value is json key in definition.
    attribute_map = {}


    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._raw_dict = {}
        return obj

    @classmethod
    def from_dict(cls: typing.Type[T], dikt) -> T:
        """Returns the dict as a model"""
        obj = util.deserialize_model(dikt, cls)
        return obj

    def toJSON(self):
        return json.dumps(self.to_dict())

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        return self._raw_dict[key]
    
    def __setitem__(self, key, value):
        if hasattr(self, key):
            setattr(self, key, value)

        self._raw_dict[key] = value


    def __setattr__(self, key: str, value) -> None:
        if humps.is_camelcase(key):
            object.__setattr__(self, humps.decamelize(key), value)
        elif humps.is_snakecase(key):
            object.__setattr__(self, humps.camelize(key), value)
        object.__setattr__(self, key, value)

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
            if humps.is_camelcase(attr):
                result[humps.decamelize(attr)] = result[attr]
            elif humps.is_snakecase(attr):
                result[humps.camelize(attr)] = result[attr]


        if hasattr(self, "_raw_dict"):
            merged = dict(self._raw_dict)
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