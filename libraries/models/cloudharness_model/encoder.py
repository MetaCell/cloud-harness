from json import JSONEncoder
import six

from cloudharness_model.models.base_model_ import Model


class CloudHarnessJSONEncoder(JSONEncoder):
    include_nulls = False

    def default(self, o):
        if isinstance(o, Model):
            JSONEncoder.default(self, o.to_dict())
        return JSONEncoder.default(self, o)
