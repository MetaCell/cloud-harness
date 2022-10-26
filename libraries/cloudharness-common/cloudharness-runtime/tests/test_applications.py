from .test_env import set_default_environment

set_default_environment()

from cloudharness.applications import ApplicationConfiguration, get_configuration
from cloudharness.utils.config import CloudharnessConfig, ConfigObject



conf_1 = {
    'name': 'app1',
    
    'harness': {
        'name': 'app1',
        'subdomain': 'myapp',
        'service': {
            'name': 'app1',
            'auto': True,
            'port': 9000
        },
        'deployment': {
            'auto': True,
            'image': 'image1-name'
        },
        'sentry': True
    },
    "freefield": {
        "a": 1
    }
}

conf_2 = {
    'name': 'app2',
    'harness': {
        'name': 'app2',
        'service': {
            'auto': False
        },
        'deployment': {
            'auto': False
        },
        'sentry': True
    }
}

conf_2sub = {

    'harness': {
        'name': 'app2sub',
        'service': {
            'auto': True
        },
        'deployment': {
            'auto': False
        },
        'sentry': False
    }
}

conf_2['subapp'] = conf_2sub


def test_application_conf():
    uut = ApplicationConfiguration.from_dict(conf_1)
    assert uut.is_auto_service()
    assert uut.is_auto_deployment()
    assert uut.is_sentry_enabled()

    d2 = {'admin': {'pass': 'metacell', 'role': 'administrator', 'user': 'admin'}, 'client': {'id': 'rest-client', 'secret': '5678eb6e-9e2c-4ee5-bd54-34e7411339e8'}, 'enabled': True, 'harness': {'aliases': [], 'database': {'auto': True, 'mongo': {'image': 'mongo:5', 'ports': [{'name': 'http', 'port': 27017}]}, 'name': 'keycloak-postgres', 'neo4j': {'dbms_security_auth_enabled': 'false', 'image': 'neo4j:4.1.9', 'memory': {'heap': {'initial': '64M', 'max': '128M'}, 'pagecache': {'size': '64M'}, 'size': '256M'}, 'ports': [{'name': 'http', 'port': 7474}, {'name': 'bolt', 'port': 7687}]}, 'pass': 'password', 'postgres': {'image': 'postgres:10.4', 'initialdb': 'auth_db', 'ports': [{'name': 'http', 'port': 5432}]}, 'resources': {'limits': {'cpu': '1000m', 'memory': '2Gi'}, 'requests': {'cpu': '100m', 'memory': '512Mi'}}, 'size': '2Gi', 'type': 'postgres', 'user': 'user'}, 'dependencies': {'build': [], 'hard': [], 'soft': []}, 'deployment': {'auto': True, 'image': 'osb/accounts:3e02a15477b4696ed554e08cedf4109c67908cbe6b03331072b5b73e83b4fc2b', 'name': 'accounts', 'port': 8080, 'replicas': 1, 'resources': {'limits': {'cpu': '500m', 'memory': '1024Mi'}, 'requests': {'cpu': '10m', 'memory': '512Mi'}}}, 'domain': None, 'env': [{'name': 'KEYCLOAK_IMPORT', 'value': '/tmp/realm.json'}, {'name': 'KEYCLOAK_USER', 'value': 'admin'}, {'name': 'KEYCLOAK_PASSWORD', 'value': 'metacell'}, {'name': 'PROXY_ADDRESS_FORWARDING', 'value': 'true'}, {'name': 'DB_VENDOR', 'value': 'POSTGRES'}, {'name': 'DB_ADDR', 'value': 'keycloak-postgres'}, {'name': 'DB_DATABASE', 'value': 'auth_db'}, {'name': 'DB_USER', 'value': 'user'}, {'name': 'DB_PASSWORD', 'value': 'password'}, {'name': 'JAVA_OPTS', 'value': '-server -Xms64m -Xmx896m -XX:MetaspaceSize=96M -XX:MaxMetaspaceSize=256m -Djava.net.preferIPv4Stack=true -Djboss.modules.system.pkgs=org.jboss.byteman -Djava.awt.headless=true  --add-exports=java.base/sun.nio.ch=ALL-UNNAMED --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED --add-exports=jdk.unsupported/sun.reflect=ALL-UNNAMED'}], 'name': 'accounts', 'readinessProbe': {'path': '/auth/realms/master'}, 'resources': [{'dst': '/tmp/realm.json', 'name': 'realm-config', 'src': 'realm.json'}], 'secrets': '', 'secured': False, 'service': {'auto': True, 'name': 'accounts', 'port': 8080}, 'subdomain': 'accounts', 'uri_role_mapping': [{'roles': ['administrator'], 'uri': '/*'}], 'use_services': []}, 'harvest': True, 'image': 'osb/accounts:latest', 'name': 'accounts', 'port': 8080, 'resources': {'limits': {'cpu': '500m', 'memory': '1024Mi'}, 'requests': {'cpu': '10m', 'memory': '512Mi'}}, 'task-images': {}, 'webclient': {'id': 'web-client', 'secret': '452952ae-922c-4766-b912-7b106271e34b'}}
    uut = ApplicationConfiguration.from_dict(d2)
    assert uut.conf
    assert uut.conf.admin.role == 'administrator'
    assert uut.conf["admin.role"] == 'administrator'

def test_get_configuration():
    CloudharnessConfig.apps = {
        'a': conf_1,
        'b': conf_2
    }

    uut = get_configuration('app1')
    assert uut.harness.name == 'app1'
    assert uut.is_auto_service()
    assert uut.is_auto_deployment()
    assert uut.is_sentry_enabled()
    assert uut.image_name == 'image1-name'
    assert uut.get_public_address() == "https://myapp.cloudharness.metacell.us"
    assert uut.get_service_address() == "http://app1.ch:9000"
    assert uut["freefield"]["a"] == 1
    assert uut["freefield"].a == 1
    assert uut["freefield.a"] == 1
    
    
    assert uut.freefield.a == 1

    uut = get_configuration('app2')

    assert uut.name == 'app2'
    assert not uut.is_auto_service()
    assert not uut.is_auto_deployment()
    assert uut.is_sentry_enabled()


    

    # TODO subapp support
    # uut = get_configuration('app2sub')

    # assert uut.name == 'app2sub'
    # assert uut.is_auto_service()
    # assert not uut.is_auto_deployment()
    # assert not uut.is_sentry_enabled()
