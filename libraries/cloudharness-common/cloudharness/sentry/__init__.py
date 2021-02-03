import json
import os
import requests

from cloudharness.utils.env import get_common_service_cluster_address

sentry_environment = os.environ.get("DOMAIN", "Production")

def get_dsn(appname):
    """
    Helper function for getting the Sentry DSN of the project of the application
    If the application has no project in Sentry, the project will be created and
    linked to the default organisation Sentry and team Sentry

    Args:
        appname: the slug of the application

    Returns:
        Sentry DSN

    Usage examples: 
        from cloudharness.sentry import get_dsn
        dsn = get_dsn('workspaces')
    """ 
    url = get_common_service_cluster_address() + f'/api/sentry/getdsn/{appname}'
    response = requests.get(url, verify=False).json()
    dsn = response['dsn']
    if dsn and len(dsn)>0:
        return dsn
    else:
        return None

def init(appname):
    """
    Init cloudharness Sentry functionality for the current app

    Args:
        appname: the slug of the application

    Usage examples: 
        import cloudharness.sentry as sentry
        sentry.init('workspaces')
    """
    dsn = get_dsn(appname)
    if dsn:
        import sentry_sdk
        try:
            from flask import current_app as app
            from sentry_sdk.integrations.flask import FlaskIntegration
            integrations = [FlaskIntegration]
        except:
            integrations = []
        sentry_sdk.init(
            dsn=dsn,
            environment=sentry_environment,
            integrations=[FlaskIntegration()]
        )

__all__ = ['get_dsn', 'init']
