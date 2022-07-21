from cloudharness.applications import ConfigurationCallException

from django.conf import settings
from kafka.errors import TopicAlreadyExistsError

from cloudharness import log
from cloudharness.events.client import EventClient

from cloudharness_django.exceptions import KeycloakOIDCNoProjectError
from cloudharness_django.services import init_services, get_user_service, get_auth_service


class KeycloakMessageService:

    def __init__(self, kafka_group_id):
        self._topic = "keycloak.fct.admin"
        self.kafka_group_id = kafka_group_id

    @staticmethod
    def event_handler(app, event_client, message):
        resource = message["resource-type"]
        operation = message["operation-type"]
        resource_path = message["resource-path"].split("/")

        log.error(f"{event_client} {message}")
        if resource in ["CLIENT_ROLE_MAPPING","GROUP","USER","GROUP_MEMBERSHIP"]:
            try:
                init_services()
                user_service = get_user_service()
                auth_client = get_auth_service().get_auth_client()

                if resource == "GROUP":
                    kc_group = auth_client.get_group(resource_path[1])
                    user_service.sync_kc_group(kc_group)
                if resource == "USER":
                    kc_user = auth_client.get_user(resource_path[1])
                    user_service.sync_kc_user(kc_user, delete=operation == "DELETE")
                if resource == "CLIENT_ROLE_MAPPING":
                    # adding/deleting user client roles
                    # set/user user is_superuser
                    kc_user = auth_client.get_user(resource_path[1])
                    user_service.sync_kc_user(kc_user)
                if resource == "GROUP_MEMBERSHIP":
                    # adding / deleting users from groups, update the user
                    # updating the user will also update the user groups
                    kc_user = auth_client.get_user(resource_path[1])
                    user_service.sync_kc_user(kc_user)
            except Exception as e:
                log.error(e)
                raise e

    def init_topics(self):
        log.info("Starting Kafka consumer threads")
        try:
            event_client = EventClient(self._topic)
            try:
                # try to create the topic, if it exists it will throw an exception
                event_client.create_topic()
            except TopicAlreadyExistsError as e:
                pass
            event_client.async_consume(app={}, group_id=self.kafka_group_id, handler=KeycloakMessageService.event_handler)
        except Exception as e:
            log.error(f"Error creating topic {self._topic}", exc_info=e)

    @classmethod
    def test_kafka_running(cls):
        EventClient("keycloak-dummy-client")._get_consumer()

    def setup_event_service(self):
        try:
            from cloudharness.applications import get_current_configuration
            current_app = get_current_configuration()

            self.test_kafka_running() # if the test fails (raises an exception) then k8s will restart the application
            # init the topics
            self.init_topics()
        except ConfigurationCallException as e:
            # configuration not found, continue without Kafka listener(s)
            pass


# start services
if not hasattr(settings, "PROJECT_NAME"):
    raise KeycloakOIDCNoProjectError("Project name not found, please set PROJECT_NAME in your settings module")

KeycloakMessageService(settings.PROJECT_NAME).setup_event_service()
