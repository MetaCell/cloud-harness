from urllib.parse import urljoin

from cloudharness import applications
from cloudharness.utils.config import CloudharnessConfig

def get_config():  # noqa: E501
    """
    Gets the config for logging in into accounts

    :rtype: json
        {
            'url': '',
            'realm': '',
            'clientId': ''
        }
    """
    accounts_app = applications.get_configuration('accounts')
    return {
        'url': urljoin(accounts_app.get_public_address(), 'auth'),
        'realm': CloudharnessConfig.get_namespace(),
        'clientId': accounts_app['webclient']['id']
    }
