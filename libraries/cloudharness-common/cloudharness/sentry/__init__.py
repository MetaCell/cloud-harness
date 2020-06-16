import requests
import json
from cloudharness.utils.env import get_cloudharness_chservice_service_url

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
    url = get_cloudharness_chservice_service_url() + f'/api/sentry/getdsn/{appname}'
    response = requests.get(url, verify=False).json()
    return response['dsn']
