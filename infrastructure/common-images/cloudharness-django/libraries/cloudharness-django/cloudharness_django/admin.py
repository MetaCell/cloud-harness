from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group

from admin_extra_buttons.api import ExtraButtonsMixin, button
from .models import Member, Organization, OrganizationMember


# Register your models here.

admin.site.unregister(User)
admin.site.unregister(Group)


class OrganizationMemberInline(admin.TabularInline):
    model = OrganizationMember
    extra = 0
    autocomplete_fields = ['user']
    readonly_fields = []


@admin.register(Organization)
class OrganizationAdmin(ExtraButtonsMixin, admin.ModelAdmin):
    list_display = ['name', 'kc_id', 'members_count']
    search_fields = ['name', 'kc_id']
    list_filter = [('kc_id', admin.EmptyFieldListFilter)]
    readonly_fields = ['kc_id']
    inlines = [OrganizationMemberInline]

    def get_readonly_fields(self, request, obj=None):
        """Make kc_id readonly only for existing objects."""
        if obj:
            return ['kc_id']
        return []

    @admin.display(description='Members')
    def members_count(self, obj):
        return obj.members.count()

    @button()
    def sync_keycloak(self, request):
        from cloudharness_django.services import get_user_service
        get_user_service().sync_kc_users_groups()
        self.message_user(request, 'Keycloak organizations synced.')


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization']
    search_fields = ['user__username', 'user__email', 'organization__name']
    list_filter = ['organization']
    autocomplete_fields = ['user', 'organization']


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
        get_user_service().sync_kc_users_groups()
        self.message_user(request, 'Keycloak users & groups synced.')


admin.site.register(User, CHUserAdmin)
admin.site.register(Group, CHGroupAdmin)
