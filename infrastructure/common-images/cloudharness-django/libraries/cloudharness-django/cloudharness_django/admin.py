from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

from admin_extra_buttons.api import ExtraButtonsMixin, button
from .models import Member


# Register your models here.

admin.site.unregister(User)
admin.site.unregister(Group)


class MemberAdmin(admin.StackedInline):
    model = Member


class CHUserAdmin(ExtraButtonsMixin, UserAdmin):

    inlines = [MemberAdmin]

    def has_add_permission(self, request):
        return settings.DEBUG or settings.USER_CHANGE_ENABLED

    def has_change_permission(self, request, obj=None):
        return settings.DEBUG or settings.USER_CHANGE_ENABLED

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG or settings.USER_CHANGE_ENABLED

    @button()
    def sync_keycloak(self, request):
        from cloudharness_django.services import get_user_service
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
        from cloudharness_django.services import get_user_service
        get_user_service().sync_kc_groups()
        self.message_user(request, 'Keycloak users & groups synced.')


class CHOrganizationAdmin(ExtraButtonsMixin, admin.ModelAdmin):

    def has_add_permission(self, request):
        return settings.DEBUG

    def has_change_permission(self, request, obj=None):
        return settings.DEBUG

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG

    @button()
    def sync_keycloak(self, request):
        from cloudharness_django.services import get_user_service
        get_user_service().sync_kc_organizations()
        self.message_user(request, 'Keycloak organizations synced.')


admin.site.register(User, CHUserAdmin)
admin.site.register(Group, CHGroupAdmin)
