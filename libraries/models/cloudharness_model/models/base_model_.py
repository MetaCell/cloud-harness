import pprint

import six
import typing
import json

import humps

from cloudharness_model import util

T = typing.TypeVar('T')


def clean_snake_cased(adict: dict):
    return {k:v for k, v in adict.items() if not (humps.is_snakecase(k) and not humps.is_camelcase(k) and humps.camelize(k) in adict)}

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

    def __getattr__(self, key: str) -> typing.Any:
        try:
            return self.get_from_raw(key)
        except KeyError:
            raise AttributeError(key)

    def __getitem__(self, key: str):
        if "." not in key:
            return getattr(self, key)
        keys = key.split(".")
        return self[keys[0]][key[len(keys[0]) + 1::]]
    
    def get_from_raw(self, key):
        item = self._raw_dict[key]
        if type(item) == dict:
            return Model.from_dict(item)
        elif type(item) in [list, tuple]:
            return [Model.from_dict(i) if type(i) == dict else i for i in item]
        return item

    
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
            return clean_snake_cased(merged)

        return clean_snake_cased(result)

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

    def __iter__(self):
        return iter(self._raw_dict)

    def __len__(self):
        return len(self._raw_dict)

    def values(self):
        return self._raw_dict.values()

    def keys(self):
        return self._raw_dict.keys()

    def items(self):
        return self._raw_dict.items()