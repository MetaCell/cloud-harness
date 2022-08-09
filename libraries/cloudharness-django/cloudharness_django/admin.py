from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

from admin_extra_buttons.api import ExtraButtonsMixin, button

from cloudharness_django.services import get_user_service

# Register your models here.

admin.site.unregister(User)
admin.site.unregister(Group)

class CHUserAdmin(ExtraButtonsMixin, UserAdmin):

    def has_add_permission(self, request):
        return settings.DEBUG

    def has_change_permission(self, request, obj=None):
        return settings.DEBUG

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG

    @button()
    def sync_keycloak(self, request):
        get_user_service().sync_kc_users_groups()
        self.message_user(request, 'Keycloak users & groups synced.')


class CHGroupAdmin(ExtraButtonsMixin, GroupAdmin):

    def has_add_permission(self, request):
        return settings.DEBUG

    def has_change_permission(self, request, obj=None):
        return settings.DEBUG

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG

    @button()
    def sync_keycloak(self, request):
        get_user_service().sync_kc_users_groups()
        self.message_user(request, 'Keycloak users & groups synced.')

admin.site.register(User, CHUserAdmin)
admin.site.register(Group, CHGroupAdmin)
