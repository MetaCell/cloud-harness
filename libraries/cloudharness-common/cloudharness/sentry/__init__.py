import os
import requests

from cloudharness.utils.env import get_common_service_cluster_address
from cloudharness.applications import get_current_configuration

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
        dsn = get_dsn('notifications')
    """
    url = get_common_service_cluster_address() + f'/api/sentry/getdsn/{appname}'
    response = requests.get(url, verify=False).json()
    dsn = response['dsn']
    if dsn and len(dsn) > 0:
        return dsn
    else:
        return None


def init(appname=None, traces_sample_rate=0, integrations=None, **kwargs):
    """
    Init cloudharness Sentry functionality for the current app

    Args:
        appname: the slug of the application
        others/kwargs: additional parameters for sentry_sdk.init


    Usage examples: 
        import cloudharness.sentry as sentry
        sentry.init('notifications')
    """
    if appname is None:
        appname = get_current_configuration().harness.name

    dsn = get_dsn(appname)

    if dsn:
        import sentry_sdk
        if not integrations:
            try:
                from flask import current_app as app
                from sentry_sdk.integrations.flask import FlaskIntegration
                integrations = [FlaskIntegration()]
            except:
                integrations = []
        sentry_sdk.init(
            dsn=dsn,
            environment=sentry_environment,
            integrations=integrations,
            traces_sample_rate=traces_sample_rate,
            **kwargs
        )


__all__ = ['get_dsn', 'init']
