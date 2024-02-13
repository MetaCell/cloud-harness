import os
import requests

from cloudharness import applications, log
from cloudharness.utils.env import get_sentry_service_cluster_address
from common.repository.sentry import get_token, get_dsn, SentryProjectNotFound


try:
    global_dsn = os.environ.get("SENTRY_DSN", "")
    if len(global_dsn) < 1:
        global_dsn = None
except:
    global_dsn = None

def getdsn(appname):  # noqa: E501
    """
    Gets the Sentry DSN for a given application or returns the global dsn when set
    global dsn can be set using the kubectl command
        kubectl create secret generic -n mnp mnp-sentry --from-literal=dsn=<dsn>
    :param appname:
    :type appname: str
    :rtype: str
    """
    try:
        ch_app = applications.get_configuration(appname)
    except applications.ConfigurationCallException as e:
        return {"error": f"Application `{appname}` does not exist"}, 400
    if ch_app.is_sentry_enabled():
        if global_dsn:
            # if a global dsn env var is set and not empty then use this
            dsn = global_dsn
        else:
            try:
                dsn = get_dsn(appname)
            except SentryProjectNotFound as e:
                # if project not found, create one
                try:
                    sentry_api_token = get_token()
                    headers = {'Authorization': 'Bearer ' + sentry_api_token}
                    url = get_sentry_service_cluster_address() + f'/api/0/teams/sentry/sentry/projects/'
                    data = {'name': appname}
                    response = requests.post(
                        url, data, headers=headers, verify=False)
                    dsn = get_dsn(appname)
                except:
                    log.error("Error on Sentry initialization", exc_info=True)
                    # FIXME temporary fix
                    return {"error": "Sentry not initialized"}, 400
    else:
        dsn = ''
    return {'dsn': dsn}
