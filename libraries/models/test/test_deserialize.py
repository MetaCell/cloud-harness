import pytest
from os.path import join, dirname as dn, realpath
import yaml

from cloudharness_model import HarnessMainConfig, ApplicationConfig, User, ApplicationHarnessConfig, CDCEvent

HERE = dn(realpath(__file__))


def test_helm_values_deserialize():
    with open(join(HERE, "resources/values.yaml")) as f:
        values = yaml.safe_load(f)
    v = HarnessMainConfig.from_dict(values)

    assert v.domain

    assert v.apps.accounts
    assert v.apps["accounts"].harness.deployment.name == "accounts"

    app = ApplicationConfig.from_dict(values["apps"]["accounts"])
    assert app.harness.deployment.name == "accounts"

    assert v.apps["accounts"].webclient.get('id')

    u = User(last_name="a")
    assert u.last_name == "a"
    assert u["last_name"] == "a"

    u = User().from_dict(dict(lastName="a"))
    assert u.last_name == "a"
    assert u["lastName"] == "a"


def test_robustness():
    d = {'aliases': [], 'database': {'auto': True, 'mongo': {'image': 'mongo:5', 'ports': [{'name': 'http', 'port': 27017}]}, 'name': 'keycloak-postgres', 'neo4j': {'dbms_security_auth_enabled': 'false', 'image': 'neo4j:4.1.9', 'memory': {'heap': {'initial': '64M', 'max': '128M'}, 'pagecache': {'size': '64M'}, 'size': '256M'}, 'ports': [{'name': 'http', 'port': 7474}, {'name': 'bolt', 'port': 7687}]}, 'pass': 'password', 'postgres': {'image': 'postgres:10.4', 'initialdb': 'auth_db', 'ports': [{'name': 'http', 'port': 5432}]}, 'resources': {'limits': {'cpu': '1000m', 'memory': '2Gi'}, 'requests': {'cpu': '100m', 'memory': '512Mi'}}, 'size': '2Gi', 'type': 'postgres', 'user': 'user'}, 'dependencies': {'build': [], 'hard': [], 'soft': []}, 'deployment': {'auto': True, 'image': 'osb/accounts:3e02a15477b4696ed554e08cedf4109c67908cbe6b03331072b5b73e83b4fc2b', 'name': 'accounts', 'port': 8080, 'replicas': 1, 'resources': {'limits': {'cpu': '500m', 'memory': '1024Mi'}, 'requests': {'cpu': '10m', 'memory': '512Mi'}}}, 'domain': None, 'env': [{'name': 'KEYCLOAK_IMPORT', 'value': '/tmp/realm.json'},
            {'name': 'KEYCLOAK_USER', 'value': 'admin'}, {'name': 'KEYCLOAK_PASSWORD', 'value': 'metacell'}, {'name': 'PROXY_ADDRESS_FORWARDING', 'value': 'true'}, {'name': 'DB_VENDOR', 'value': 'POSTGRES'}, {'name': 'DB_ADDR', 'value': 'keycloak-postgres'}, {'name': 'DB_DATABASE', 'value': 'auth_db'}, {'name': 'DB_USER', 'value': 'user'}, {'name': 'DB_PASSWORD', 'value': 'password'}, {'name': 'JAVA_OPTS', 'value': '-server -Xms64m -Xmx896m -XX:MetaspaceSize=96M -XX:MaxMetaspaceSize=256m -Djava.net.preferIPv4Stack=true -Djboss.modules.system.pkgs=org.jboss.byteman -Djava.awt.headless=true  --add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED --add-exports=jdk.unsupported/sun.reflect=ALL-UNNAMED'}], 'name': 'accounts', 'readinessProbe': {'path': '/auth/realms/master'}, 'resources': [{'dst': '/tmp/realm.json', 'name': 'realm-config', 'src': 'realm.json'}], 'secrets': '', 'secured': False, 'service': {'auto': True, 'name': 'accounts', 'port': 8080}, 'subdomain': 'accounts', 'uri_role_mapping': [{'roles': ['administrator'], 'uri': '/*'}], 'use_services': []}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
    
    app = ApplicationHarnessConfig.from_dict(d)
    assert app.database.auto == True

    cdc = {'meta': {'app_name': 'workspaces', 'user': {'access': {'impersonate': True,          'manage': True,          'manageGroupMembership': True,          'mapRoles': True,          'view': True},
 'additional_properties': None,
 'attributes': None,
 'client_roles': None,
 'created_timestamp': None,
 'credentials': None,
 'disableable_credential_types': None,
 'email': 'a@aa.it',
 'email_verified': None,
 'enabled': True,
 'federation_link': None,
 'first_name': None,
 'groups': None,
 'id': '61a2cc58-d98c-4318-8828-fbdae85041ac',
 'last_name': None,
 'realm_roles': None,
 'required_actions': None,
 'service_account_client_id': None,
 'username': 'a'}, 'func': '<function WorkspaceService.post at 0x7fecdda2ee60>', 'args': [{'name': 'weerewerw', 'description': 'weerewerw', 'resources': [{'name': 'notebook', 'status': 'p', 'resource_type': 'g', 'workspace_id': -1, 'origin': '{"path": "http://www.osb.local/workspace-data/notebook.ipynb"}'}], 'user_id': '61a2cc58-d98c-4318-8828-fbdae85041ac'}], 'kwargs': [], 'description': 'workspace - 10'}, 'message_type': 'workspace', 'operation': 'create', 'uid': 10, 'resource': {'id': 10, 'name': 'weerewerw', 'description': 'weerewerw', 'timestamp_created': '2022-03-04T17:51:36.267012', 'timestamp_updated': '2022-03-04T17:51:36.267012', 'last_opened_resource_id': None, 'thumbnail': None, 'gallery': [], 'user_id': '61a2cc58-d98c-4318-8828-fbdae85041ac', 'publicable': False, 'featured': False, 'license': None, 'collaborators': [], 'storage': None, 'tags': [], 'resources': [{'id': 11, 'name': 'notebook', 'folder': 'notebook', 'status': 'p', 'timestamp_created': None, 'timestamp_updated': None, 'timestamp_last_opened': None, 'resource_type': 'g', 'origin': '{"path": "http://www.osb.local/workspace-data/notebook.ipynb"}', 'workspace_id': 10}]}}

    e = CDCEvent.from_dict(cdc)


    app = {'admin': {'pass': 'metacell', 'role': 'administrator', 'user': 'admin'}, 'client': {'id': 'rest-client', 'secret': '5678eb6e-9e2c-4ee5-bd54-34e7411339e8'}, 'enabled': True, 'harness': {'aliases': [], 'database': {'auto': True, 'mongo': {'image': 'mongo:5', 'ports': [{'name': 'http', 'port': 27017}]}, 'name': 'keycloak-postgres', 'neo4j': {'dbms_security_auth_enabled': 'false', 'image': 'neo4j:4.1.9', 'memory': {'heap': {'initial': '64M', 'max': '128M'}, 'pagecache': {'size': '64M'}, 'size': '256M'}, 'ports': [{'name': 'http', 'port': 7474}, {'name': 'bolt', 'port': 7687}]}, 'pass': 'password', 'postgres': {'image': 'postgres:10.4', 'initialdb': 'auth_db', 'ports': [{'name': 'http', 'port': 5432}]}, 'resources': {'limits': {'cpu': '1000m', 'memory': '2Gi'}, 'requests': {'cpu': '100m', 'memory': '512Mi'}}, 'size': '2Gi', 'type': 'postgres', 'user': 'user'}, 'dependencies': {'build': [], 'hard': [], 'soft': []}, 'deployment': {'auto': True, 'image': 'osb/accounts:3e02a15477b4696ed554e08cedf4109c67908cbe6b03331072b5b73e83b4fc2b', 'name': 'accounts', 'port': 8080, 'replicas': 1, 'resources': {'limits': {'cpu': '500m', 'memory': '1024Mi'}, 'requests': {'cpu': '10m', 'memory': '512Mi'}}}, 'domain': None, 'env': [{'name': 'KEYCLOAK_IMPORT', 'value': '/tmp/realm.json'}, {'name': 'KEYCLOAK_USER', 'value': 'admin'}, {'name': 'KEYCLOAK_PASSWORD', 'value': 'metacell'}, {'name': 'PROXY_ADDRESS_FORWARDING', 'value': 'true'}, {'name': 'DB_VENDOR', 'value': 'POSTGRES'}, {'name': 'DB_ADDR', 'value': 'keycloak-postgres'}, {'name': 'DB_DATABASE', 'value': 'auth_db'}, {'name': 'DB_USER', 'value': 'user'}, {'name': 'DB_PASSWORD', 'value': 'password'}, {'name': 'JAVA_OPTS', 'value': '-server -Xms64m -Xmx896m -XX:MetaspaceSize=96M -XX:MaxMetaspaceSize=256m -Djava.net.preferIPv4Stack=true -Djboss.modules.system.pkgs=org.jboss.byteman -Djava.awt.headless=true  --add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED --add-exports=jdk.unsupported/sun.reflect=ALL-UNNAMED'}], 'name': 'accounts', 'readinessProbe': {'path': '/auth/realms/master'}, 'resources': [{'dst': '/tmp/realm.json', 'name': 'realm-config', 'src': 'realm.json'}], 'secrets': '', 'secured': False, 'service': {'auto': True, 'name': 'accounts', 'port': 8080}, 'subdomain': 'accounts', 'uri_role_mapping': [{'roles': ['administrator'], 'uri': '/*'}], 'use_services': []}, 'harvest': True, 'image': 'osb/accounts:latest', 'name': 'accounts', 'port': 8080, 'resources': {'limits': {'cpu': '500m', 'memory': '1024Mi'}, 'requests': {'cpu': '10m', 'memory': '512Mi'}}, 'task-images': {}, 'webclient': {'id': 'web-client', 'secret': '452952ae-922c-4766-b912-7b106271e34b'}}

    ApplicationConfig.from_dict(app)