from json import JSONEncoder


class CloudHarnessJSONEncoder(JSONEncoder):
    include_nulls = False
    def encode(self, o):
        if hasattr(o, "to_json"):
            return o.to_json()
        return super().encode(o)

    def default(self, o):
        
        if hasattr(o, "to_dict"):
            return o.to_dict()
        return JSONEncoder.default(self, o)