from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from cloudharness.auth.exceptions import UserNotFound
from cloudharness_django.models import Member
from cloudharness_django.services.events import KeycloakMessageService
from cloudharness_django.services.user import UserService

EVENTS = "cloudharness_django.services.events"
KC_ID = "aa9fa0bb-572e-4467-8b13-746606981626"


class UserEventHandlerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="kc-user@example.com", email="kc-user@example.com", is_active=True)
        Member.objects.create(user=self.user, kc_id=KC_ID)

        self.auth_client = MagicMock()
        auth_service = MagicMock()
        auth_service.get_auth_client.return_value = self.auth_client
        self.user_service = UserService(auth_service)

        self.invalidate_user_cache = self._patch(f"{EVENTS}.invalidate_user_cache")
        self._patch(f"{EVENTS}.time.sleep")
        self._patch(f"{EVENTS}.init_services")
        self._patch(f"{EVENTS}.get_user_service", return_value=self.user_service)
        self._patch(f"{EVENTS}.get_auth_service", return_value=auth_service)

    def _patch(self, target, **kwargs):
        patcher = patch(target, **kwargs)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def _send_user_event(self, operation):
        message = {
            "resource-type": "USER",
            "operation-type": operation,
            "resource-path": f"users/{KC_ID}",
        }
        KeycloakMessageService.event_handler(app={}, event_client=None, message=message)

    def test_delete_deactivates_django_user_without_fetching_keycloak_user(self):
        # Keycloak has already removed the user when its DELETE admin event arrives
        self.auth_client.get_user.side_effect = UserNotFound(KC_ID)

        self._send_user_event("DELETE")

        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.auth_client.get_user.assert_not_called()
        self.invalidate_user_cache.assert_called_once_with(KC_ID)

    def test_delete_of_user_unknown_to_django_is_ignored(self):
        Member.objects.all().delete()
        self.auth_client.get_user.side_effect = UserNotFound(KC_ID)

        self._send_user_event("DELETE")

        self.auth_client.get_user.assert_not_called()

    def test_update_still_syncs_the_keycloak_user(self):
        kc_user = MagicMock(id=KC_ID)
        self.auth_client.get_user.return_value = kc_user

        with patch.object(self.user_service, "sync_kc_user") as sync_kc_user:
            self._send_user_event("UPDATE")

        self.auth_client.get_user.assert_called_once_with(KC_ID)
        sync_kc_user.assert_called_once()
        self.assertIs(sync_kc_user.call_args.args[0], kc_user)
        self.invalidate_user_cache.assert_called_once_with(KC_ID)
