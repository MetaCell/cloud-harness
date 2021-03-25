import os
import inspect

import flask
import connexion
from connexion.apps.flask_app import FlaskJSONEncoder
import six

from cloudharness import log as logging

app = None

class JSONEncoder(FlaskJSONEncoder):
    include_nulls = False

    def default(self, o):
        if hasattr(o, 'openapi_types'):
            dikt = {}
            for attr, _ in six.iteritems(o.openapi_types):
                value = getattr(o, attr)
                if value is None and not self.include_nulls:
                    continue
                attr = o.attribute_map[attr]
                dikt[attr] = value
            return dikt
        return FlaskJSONEncoder.default(self, o)


def init_webapp_routes(app: flask.Flask, www_path):

    @app.route('/test', methods=['GET'])
    def test():
        return 'routing ok'

    @app.route('/', methods=['GET'])
    def index():
        return flask.send_from_directory(www_path, 'index.html')

    @app.route('/<path:path>', methods=['GET'])
    def send_webapp(path):
        return flask.send_from_directory(www_path, path)

    @app.errorhandler(404)
    def page_not_found(error):
        # when a 404 is thrown send the "main" index page
        # unless the first segment of the path is in the exception list
        first_segment_path = flask.request.full_path.split('/')[1]
        if first_segment_path in ['api','static','test']:  # exception list
            return error
        return index()

    @app.route('/static/<path:path>', methods=['GET'])
    def send_static(path):
        return flask.send_from_directory(os.path.join(www_path, 'static'), path)

class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True

def init_flask(title='CH service API', init_app_fn=None, webapp=False, json_encoder=JSONEncoder, resolver=None, config=Config):
    """

    """
    global app

    # Some magic inspection to get the caller's absolute path
    import inspect, os
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    caller_path = os.path.dirname(os.path.realpath(mod.__file__))

    connexion_app = connexion.App(__name__)
    app = connexion_app.app
    obj_config = os.environ.get('APP_SETTINGS', config)
    if obj_config:
        app.config.from_object(obj_config)
    app.json_encoder = json_encoder

    with app.app_context():
        # setup logging
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

        if webapp:
            init_webapp_routes(app, www_path=os.path.join(os.path.dirname(caller_path), 'www'))
        connexion_app.add_api(os.path.join(caller_path, 'openapi/openapi.yaml'),
                              arguments={'title': title},
                              pythonic_params=True, resolver=resolver)

        if init_app_fn:
            init_app_fn(app)

    return app

def main():
    app.run( host='0.0.0.0', port=os.getenv('PORT', 5001))