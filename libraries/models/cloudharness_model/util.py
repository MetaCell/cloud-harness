import datetime
import logging
import humps

import six
import typing
from cloudharness_model import typing_utils


def _deserialize(data, klass):
    """Deserializes dict, list, str into an object.
    :param data: dict, list or str.
    :param klass: class literal, or string of class name.
    :return: object.
    """
    if data is None:
        return None

    if klass in six.integer_types or klass in (float, str, bool, bytearray):
        return _deserialize_primitive(data, klass)
    elif klass == object:
        return _deserialize_object(data)
    elif klass == datetime.date:
        return deserialize_date(data)
    elif klass == datetime.datetime:
        return deserialize_datetime(data)
    elif typing_utils.is_generic(klass):
        if typing_utils.is_list(klass):
            if isinstance(klass.__args__[0], typing.TypeVar):
                return data
            return _deserialize_list(data, klass.__args__[0])
        if typing_utils.is_dict(klass):
            if isinstance(klass.__args__[1], typing.TypeVar):
                return data
            return _deserialize_dict(data, klass.__args__[1])
    else:
        return deserialize_model(data, klass)


def _deserialize_primitive(data, klass):
    """Deserializes to primitive type.
    :param data: data to deserialize.
    :param klass: class literal.
    :return: int, long, float, str, bool.
    :rtype: int | long | float | str | bool
    """
    try:
        value = klass(data)
    except UnicodeEncodeError:
        value = six.u(data)
    except TypeError:
        value = data
    return value


def _deserialize_object(value):
    """Return an original value.
    :return: object.
    """
    return value


def deserialize_date(string):
    """Deserializes string to date.
    :param string: str.
    :type string: str
    :return: date.
    :rtype: date
    """
    if string is None:
        return None

    try:
        from dateutil.parser import parse
        return parse(string).date()
    except ImportError:
        return string


def deserialize_datetime(string):
    """Deserializes string to datetime.
    The string should be in iso8601 datetime format.
    :param string: str.
    :type string: str
    :return: datetime.
    :rtype: datetime
    """
    if string is None:
        return None

    try:
        from dateutil.parser import parse
        return parse(string)
    except ImportError:
        return string


class DeserializationException(Exception):
    pass


def deserialize_model(data, klass):
    """Deserializes list or dict to model.
    :param data: dict, list.
    :type data: dict | list
    :param klass: class literal.
    :return: model object.
    """

    if isinstance(data, klass) or not klass or not hasattr(klass, "__call__"):
        return data
    try:
        instance = klass()
    except:
        raise
    if isinstance(data, dict):
        instance._raw_dict = data

    if not hasattr(instance, "openapi_types") or isinstance(data, klass):
        return data
    if data is None:
        return instance
    try:
        if isinstance(data, list):
            for attr, attr_type in six.iteritems(instance.openapi_types):
                if instance.attribute_map[attr] in data:
                    value = data[instance.attribute_map[attr]]
                    setattr(instance, attr, _deserialize(value, attr_type))

        elif hasattr(data, "__getitem__"):

            for attr in data:
                value = data[attr]
                attr = humps.decamelize(attr)
                if attr in instance.attribute_map:
                    try:
                        setattr(instance, attr, _deserialize(value, instance.openapi_types[attr]))
                    except Exception as e:
                        logging.warning(
                            "Deserialization error: could not set attribute `%s` to value `%s` in class `%s`.", attr, value, klass.__name__, exc_info=True)
                        from .models.base_model_ import Model
                        setattr(instance, attr, Model.from_dict(value))
                        logging.debug("Instance is %s", instance, exc_info=True)

    except Exception as e:
        logging.error("Deserialize error", exc_info=True)
        raise DeserializationException(
            f"Cannot convert data to class {klass.__name__}. Data is\n{repr(data)}") from e

    return instance


def _deserialize_list(data, boxed_type):
    """Deserializes a list and its elements.
    :param data: list to deserialize.
    :type data: list
    :param boxed_type: class literal.
    :return: deserialized list.
    :rtype: list
    """
    return [_deserialize(sub_data, boxed_type)
            for sub_data in data]


def _deserialize_dict(data, boxed_type):
    """Deserializes a dict and its elements.
    :param data: dict to deserialize.
    :type data: dict
    :param boxed_type: class literal.
    :return: deserialized dict.
    :rtype: dict
    """
    from cloudharness_model.models.base_model_ import Model
    return Model.from_dict({k: _deserialize(v, boxed_type)
                            for k, v in six.iteritems(data)})
