import os
import json
import traceback

import flask
import connexion
from flask.json.provider import DefaultJSONProvider
import six

from cloudharness import log as logging
from cloudharness.applications import get_current_configuration
from cloudharness.middleware.flask import middleware

app = None


class JSONEncoder(DefaultJSONProvider):
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
        return DefaultJSONProvider.default(self, o)


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
        if first_segment_path in ['api', 'static', 'test']:  # exception list
            return error
        return index()

    @app.route('/static/<path:path>', methods=['GET'])
    def send_static(path):
        return flask.send_from_directory(os.path.join(www_path, 'static'), path)


def setup_cors(app: flask.Flask):
    """
    Setup CORS headers for Flask app to work with Connexion 3.x
    This replaces Flask-CORS which is no longer compatible
    """
    @app.after_request
    def after_request(response):
        # Allow CORS for API endpoints
        if flask.request.path.startswith('/api/'):
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    @app.before_request
    def handle_preflight():
        if flask.request.method == "OPTIONS" and flask.request.path.startswith('/api/'):
            response = flask.Response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add('Access-Control-Allow-Headers', "Content-Type,Authorization")
            response.headers.add('Access-Control-Allow-Methods', "GET,PUT,POST,DELETE,OPTIONS")
            return response


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True


def init_flask(title='CH service API', init_app_fn=None, webapp=False, json_encoder=JSONEncoder, resolver=None,
               config=Config, enable_cors=True):
    """

    """
    global app

    # Some magic inspection to get the caller's absolute path
    import inspect
    import os
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    caller_path = os.path.dirname(os.path.realpath(mod.__file__))

    connexion_app = connexion.FlaskApp(__name__)
    app = connexion_app.app
    obj_config = os.environ.get('APP_SETTINGS', config)
    if obj_config:
        app.config.from_object(obj_config)
    app.json = json_encoder(app)
    # activate the CH middleware
    app.wsgi_app = middleware(app.wsgi_app)

    with app.app_context():
        # setup logging
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)

        # Setup CORS if enabled (replacement for Flask-CORS)
        if enable_cors:
            setup_cors(app)

        if webapp:
            init_webapp_routes(app, www_path=os.path.join(
                os.path.dirname(caller_path), 'www'))
        connexion_app.add_api(os.path.join(caller_path, 'openapi/openapi.yaml'),
                              arguments={'title': title},
                              pythonic_params=True, resolver=resolver)

        if init_app_fn:
            init_app_fn(app)

        def handle_exception(request, exc: Exception):
            data = {
                "description": str(exc),
                "type": type(exc).__name__
            }

            try:
                # Try to check sentry configuration, but don't fail if config is not available
                try:
                    if not get_current_configuration().is_sentry_enabled():
                        data['trace'] = traceback.format_exc()
                except Exception as config_error:
                    # If configuration check fails, include trace anyway
                    logging.warning(f"Could not check sentry configuration: {config_error}")
                    data['trace'] = traceback.format_exc()
            except Exception as general_error:
                logging.error(f"Error in error handler: {general_error}", exc_info=True)
                data['trace'] = traceback.format_exc()
            
            logging.error(str(exc), exc_info=True)
            return json.dumps(data), 500
        
        # Register error handler with Flask app directly for better compatibility
        @app.errorhandler(Exception)
        def flask_handle_exception(exc: Exception):
            # For Flask error handlers, we don't get the request object, 
            # but we can access it via flask.request if needed
            try:
                import flask
                request = flask.request if flask.has_request_context() else None
            except:
                request = None
            return handle_exception(request, exc)

    return connexion_app


def main():
    # Get the global connexion app from init_flask and run it
    import inspect
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    
    # Get the connexion app variable from the calling module
    connexion_app = getattr(mod, 'app', None)
    if connexion_app and hasattr(connexion_app, 'run'):
        connexion_app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)))
    else:
        # Fallback to the global app variable (Flask app)
        if app:
            app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)))
