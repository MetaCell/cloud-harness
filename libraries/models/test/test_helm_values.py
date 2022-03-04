import pytest
from os.path import join, dirname as dn, realpath
import yaml

from cloudharness_model import HarnessMainConfig, ApplicationConfig, User, ApplicationHarnessConfig

HERE = dn(realpath(__file__))


def test_helm_values_deserialize():
    with open(join(HERE, "resources/values.yaml")) as f:
        values = yaml.load(f)
    v = HarnessMainConfig.from_dict(values)

    assert v.domain
    assert v.apps["accounts"].harness.deployment.name == "accounts"

    app = ApplicationConfig.from_dict(values["apps"]["accounts"])
    assert app.harness.deployment.name == "accounts"

    assert v.apps["accounts"].webclient.get('id')

    u = User(last_name="a")
    assert u.last_name == "a"
    assert u["last_name"] == "a"


def test_robustness():
    d = {'aliases': [], 'database': {'auto': True, 'mongo': {'image': 'mongo:5', 'ports': [{'name': 'http', 'port': 27017}]}, 'name': 'keycloak-postgres', 'neo4j': {'dbms_security_auth_enabled': 'false', 'image': 'neo4j:4.1.9', 'memory': {'heap': {'initial': '64M', 'max': '128M'}, 'pagecache': {'size': '64M'}, 'size': '256M'}, 'ports': [{'name': 'http', 'port': 7474}, {'name': 'bolt', 'port': 7687}]}, 'pass': 'password', 'postgres': {'image': 'postgres:10.4', 'initialdb': 'auth_db', 'ports': [{'name': 'http', 'port': 5432}]}, 'resources': {'limits': {'cpu': '1000m', 'memory': '2Gi'}, 'requests': {'cpu': '100m', 'memory': '512Mi'}}, 'size': '2Gi', 'type': 'postgres', 'user': 'user'}, 'dependencies': {'build': [], 'hard': [], 'soft': []}, 'deployment': {'auto': True, 'image': 'osb/accounts:3e02a15477b4696ed554e08cedf4109c67908cbe6b03331072b5b73e83b4fc2b', 'name': 'accounts', 'port': 8080, 'replicas': 1, 'resources': {'limits': {'cpu': '500m', 'memory': '1024Mi'}, 'requests': {'cpu': '10m', 'memory': '512Mi'}}}, 'domain': None, 'env': [{'name': 'KEYCLOAK_IMPORT', 'value': '/tmp/realm.json'},
            {'name': 'KEYCLOAK_USER', 'value': 'admin'}, {'name': 'KEYCLOAK_PASSWORD', 'value': 'metacell'}, {'name': 'PROXY_ADDRESS_FORWARDING', 'value': 'true'}, {'name': 'DB_VENDOR', 'value': 'POSTGRES'}, {'name': 'DB_ADDR', 'value': 'keycloak-postgres'}, {'name': 'DB_DATABASE', 'value': 'auth_db'}, {'name': 'DB_USER', 'value': 'user'}, {'name': 'DB_PASSWORD', 'value': 'password'}, {'name': 'JAVA_OPTS', 'value': '-server -Xms64m -Xmx896m -XX:MetaspaceSize=96M -XX:MaxMetaspaceSize=256m -Djava.net.preferIPv4Stack=true -Djboss.modules.system.pkgs=org.jboss.byteman -Djava.awt.headless=true  --add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED --add-exports=jdk.unsupported/sun.reflect=ALL-UNNAMED'}], 'name': 'accounts', 'readinessProbe': {'path': '/auth/realms/master'}, 'resources': [{'dst': '/tmp/realm.json', 'name': 'realm-config', 'src': 'realm.json'}], 'secrets': '', 'secured': False, 'service': {'auto': True, 'name': 'accounts', 'port': 8080}, 'subdomain': 'accounts', 'uri_role_mapping': [{'roles': ['administrator'], 'uri': '/*'}], 'use_services': []}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         
    
    app = ApplicationHarnessConfig.from_dict(d)
    assert app.database.auto == True