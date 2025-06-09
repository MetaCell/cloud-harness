from flask import jsonify


def hello():
    """Simple hello world endpoint"""
    return jsonify("Hello world"), 200
