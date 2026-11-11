from django.conf import settings
from django.contrib import admin
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.urls import reverse

from .models import Member
from .views import logout_form, safe_next


# Users and groups are managed in Microsoft Entra: read-only unless DEBUG or USER_CHANGE_ENABLED.
# Superusers can always (de)activate a user, which the Entra login does not override.

admin.site.unregister(User)
admin.site.unregister(Group)

_password_login = admin.site.login


def _admin_login(request, extra_context=None):
    """Django admin login: through Entra, unless PASSWORD_LOGIN_ENABLED (local users)."""
    if settings.PASSWORD_LOGIN_ENABLED:
        return _password_login(request, extra_context)
    next_url = request.GET.get(REDIRECT_FIELD_NAME) or reverse("admin:index")
    if not request.user.is_authenticated:
        # the Entra login checks the next url
        return redirect_to_login(next_url, settings.LOGIN_URL)
    if request.user.is_active and request.user.is_staff:
        return HttpResponseRedirect(safe_next(request, next_url))
    # logged in without the administrator role: a new Entra login would come back here
    return HttpResponseForbidden(
        "<h1>403 Permission Denied</h1><p>The Django admin requires the administrator role.</p>"
        f'{logout_form(request, "Log in as a different user")}')


admin.site.login = _admin_login


def _users_editable():
    return settings.DEBUG or settings.USER_CHANGE_ENABLED


class MemberAdmin(admin.StackedInline):
    model = Member
    readonly_fields = ['oid']

    def has_add_permission(self, request, obj=None):
        return _users_editable()

    def has_change_permission(self, request, obj=None):
        return _users_editable()

    def has_delete_permission(self, request, obj=None):
        return _users_editable()


class CHUserAdmin(UserAdmin):

    inlines = [MemberAdmin]

    def has_add_permission(self, request):
        return _users_editable()

    def has_change_permission(self, request, obj=None):
        return _users_editable() or request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return _users_editable()

    def get_readonly_fields(self, request, obj=None):
        if _users_editable():
            return super().get_readonly_fields(request, obj)
        # only the active flag is editable
        return [field.name for field in User._meta.fields if field.name != "is_active"] + \
            ["groups", "user_permissions"]


class CHGroupAdmin(GroupAdmin):
    def has_add_permission(self, request):
        return settings.DEBUG

    def has_change_permission(self, request, obj=None):
        return settings.DEBUG

    def has_delete_permission(self, request, obj=None):
        return settings.DEBUG


admin.site.register(User, CHUserAdmin)
admin.site.register(Group, CHGroupAdmin)
