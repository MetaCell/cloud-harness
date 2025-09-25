from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
import asyncio
from admin_extra_buttons.api import ExtraButtonsMixin, button
from .models import Member
from cloudharness_django.services import get_user_service

# Register your models here.

admin.site.unregister(User)
admin.site.unregister(Group)


class MemberAdmin(admin.StackedInline):
    model = Member


def run_coroutine(coroutine):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No running event loop
        loop = None

    if loop and loop.is_running():
        # If the event loop is already running, create a task
        return asyncio.create_task(coroutine)
    else:
        # If no event loop is running, run the coroutine using asyncio.run
        return asyncio.run(coroutine)


class CHUserAdmin(ExtraButtonsMixin, UserAdmin):

    inlines = [MemberAdmin]

    def has_add_permission(self, request):
        return settings.DEBUG or settings.USER_CHANGE_ENABLED

    def has_change_permission(self, request, obj=None):
        return settings.DEBUG or settings.USER_CHANGE_ENABLED

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG or settings.USER_CHANGE_ENABLED

    @button()
    async def sync_keycloak(self, request):
        run_coroutine(get_user_service().sync_kc_users_groups())
        self.message_user(request, 'Keycloak users & groups synced.')


class CHGroupAdmin(ExtraButtonsMixin, GroupAdmin):

    def has_add_permission(self, request):
        return settings.DEBUG

    def has_change_permission(self, request, obj=None):
        return settings.DEBUG

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG

    @button()
    async def sync_keycloak(self, request):
        run_coroutine(get_user_service().sync_kc_users_groups())
        self.message_user(request, 'Keycloak users & groups synced.')


admin.site.register(User, CHUserAdmin)
admin.site.register(Group, CHGroupAdmin)
