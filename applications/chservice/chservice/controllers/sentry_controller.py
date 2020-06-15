import connexion
import six
import requests
import urllib

from chservice import util

from chservice.repository.sentry import get_token, get_dsn, SentryProjectNotFound

from cloudharness.utils.env import get_sentry_service_cluster_address


def getdsn(appname):  # noqa: E501
    """Gets the Sentry DSN for a given application

    Gets the Sentry DSN for a given application # noqa: E501

    :param appname: 
    :type appname: str

    :rtype: str
    """
    try:
        dsn =  get_dsn(appname)
    except SentryProjectNotFound as e:
        # if project not found, create one
        sentry_api_token = get_token()
        headers = {'Authorization': 'Bearer ' + sentry_api_token}
        url = get_sentry_service_cluster_address() + f'/api/0/teams/sentry/sentry/projects/'
        data = {'name' : appname}
        response = requests.post(url, data, headers=headers, verify=False)
        dsn =  get_dsn(appname)

    return {'dsn': dsn}
