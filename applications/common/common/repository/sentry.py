from sqlalchemy.sql import text

from cloudharness.utils.env import get_service_public_address

from .db import get_db

class SentryProjectNotFound(Exception):
    pass

def _get_api_token():
    # ToDo: may be we can use here a dynamic token, but for now let's use a hard coded one
    api_token = 'afe75d802007405dbc0c2fb1db4cc8b06b981017f58944d0afac700f743ee06a'
    s = text('''
    select token from sentry_apitoken 
    where token=:api_token
    ''')
    token = get_db().engine.execute(s, 
        api_token=api_token
        ).fetchall()
    if len(token) == 0:
        # token is not present in the Sentry database, let's create it
        s = text('''
        insert into sentry_apitoken(user_id, token, scopes, date_added, scope_list)
        values (1, :api_token, 0, now(), :scope_list)
        ''')
        get_db().engine.execute(s, 
            api_token=api_token,
            scope_list='{event:admin,event:read,'
                        'member:read,member:admin,'
                        'project:read,project:releases,project:admin,project:write,'
                        'team:read,team:write,team:admin,'
                        'org:read,org:write,org:admin}'
            )
        return _get_api_token()
    else:
        # return the first column from the first row of the query result
        return token[0][0]

def get_token():
    return _get_api_token()

def get_dsn(appname):
    s = text('''
    select public_key, p.id
    from sentry_projectkey pkey 
    join sentry_project p on pkey.project_id=p.id 
    where p.slug=:project_slug
    ''')
    public_key = get_db().engine.execute(s, 
        project_slug=appname
        ).fetchall()
    if len(public_key) == 0:
        raise SentryProjectNotFound('Application not found!')
    else:
        dsn = public_key[0][0]
        app_id = public_key[0][1]
        sentry_host = get_service_public_address('sentry')
        dsn = f'https://{dsn}@{sentry_host}/{app_id}'

        # return the first column from the first row of the query result
        return dsn
