import datetime
import json
import uuid

import flask

from cloudharness.utils.flask_server import JSONEncoder


class ConnexionStyleModel:
    """Mimics an openapi-generator/connexion model: `to_dict()` returns the
    Python attribute names, while `attribute_map` holds the JSON names."""

    openapi_types = {'first_name': str, 'last_name': str, 'email': str}
    attribute_map = {'first_name': 'firstName', 'last_name': 'lastName', 'email': 'email'}

    def __init__(self, first_name=None, last_name=None, email=None):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email

    def to_dict(self):
        return {'first_name': self.first_name, 'last_name': self.last_name, 'email': self.email}


class PydanticStyleModel:
    """Mimics a cloudharness_model pydantic model: `to_dict()` already
    serializes by alias and there is no `openapi_types`."""

    def to_dict(self):
        return {'firstName': 'Jane', 'lastName': None}


def encoder():
    return JSONEncoder(flask.Flask(__name__))


def test_connexion_model_is_serialized_with_json_names():
    encoded = json.loads(encoder().dumps(ConnexionStyleModel(first_name='John', last_name='Doe')))
    assert encoded == {'firstName': 'John', 'lastName': 'Doe'}


def test_pydantic_model_keeps_its_aliased_keys():
    assert json.loads(encoder().dumps(PydanticStyleModel())) == {'firstName': 'Jane'}


def test_unknown_types_fall_back_to_the_default_provider():
    value = uuid.uuid4()
    assert json.loads(encoder().dumps({'id': value})) == {'id': str(value)}


def test_aware_datetime_is_serialized_as_rfc3339():
    value = datetime.datetime(2026, 8, 31, 16, 44, 54, tzinfo=datetime.timezone.utc)
    encoded = json.loads(encoder().dumps({'createTime': value}))
    assert encoded == {'createTime': '2026-08-31T16:44:54+00:00'}


def test_naive_datetime_is_serialized_as_utc():
    """RFC 3339 makes the offset mandatory, so a naive datetime is assumed UTC."""
    value = datetime.datetime(2026, 8, 31, 16, 44, 54)
    encoded = json.loads(encoder().dumps({'createTime': value}))
    assert encoded == {'createTime': '2026-08-31T16:44:54Z'}


def test_date_is_serialized_as_iso_date():
    encoded = json.loads(encoder().dumps({'day': datetime.date(2026, 7, 29)}))
    assert encoded == {'day': '2026-07-29'}
