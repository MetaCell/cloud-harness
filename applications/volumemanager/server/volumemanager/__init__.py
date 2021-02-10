from flask import Flask, send_from_directory


def init_app(app: Flask):
    @app.route('/', methods=['GET'])
    def index():
        return send_from_directory('../www', 'index.html')

    @app.route('/<path:path>')
    def send_webapp(path):
        return send_from_directory('../www', path)

    @app.route('/assets/<path:path>')
    def send_static(path):
        return send_from_directory('../www/assets', path)
