from django.contrib.auth.models import User, Group
from django.db import transaction

from cloudharness_django.models import Team, Member, Organization, OrganizationMember
from cloudharness_django.services.auth import AuthService, AuthorizationLevel
from cloudharness import models as ch_models


def get_user_by_kc_id(kc_id) -> User:
    try:
        return Member.objects.get(kc_id=kc_id).user
    except Member.DoesNotExist:
        return None


class UserService:
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        self.auth_client = auth_service.get_auth_client()

    def _get_kc_user(self, user):
        # get the kc user by user email
        all_users = self.auth_client.get_users()
        return [kc_user for kc_user in all_users if kc_user["email"] == user.email][0]

    def _map_kc_user(self, user: User, kc_user: ch_models.User = None, is_superuser=False, delete=False):
        # map a kc user to a django user
        if not kc_user:
            kc_user = self._get_kc_user(user)

        user_auth_level = self.auth_service.get_auth_level(kc_user)
        if user_auth_level == AuthorizationLevel.ADMIN:
            is_superuser = True
        # update the superuser and staff status of the user
        user.is_staff = is_superuser
        user.is_superuser = is_superuser

        user.username = kc_user.username or kc_user.email
        user.first_name = kc_user.first_name or ""
        user.last_name = kc_user.last_name or ""
        user.email = kc_user.email or ""

        user.is_active = kc_user.get("enabled", delete)
        return user

    def create_team(self, group_name):
        # create the team
        self.auth_client.create_group(name=group_name)
        kc_group = list(filter(lambda kc_group: kc_group["name"] == group_name, self.auth_client.get_groups()))[0]
        return kc_group

    def update_team(self, group):
        # sync the team name with the kc group name
        self.auth_client.update_group(group.team.kc_id, group.name)
        return group

    def add_user_to_team(self, user, team_name):
        # add a user from the group/team
        group = Group.objects.get(name=team_name)
        kc_group_id = group.team.kc_id
        kc_user_id = user.member.kc_id
        self.auth_client.group_user_add(kc_user_id, kc_group_id)

    def rm_user_from_team(self, user, team_name):
        # delete a user from the group/team
        group = Group.objects.get(name=team_name)
        kc_group_id = group.team.kc_id
        kc_user_id = user.member.kc_id
        self.auth_client.group_user_remove(kc_user_id, kc_group_id)

    def sync_kc_group(self, kc_group: ch_models.UserGroup):
        # sync the kc group with the django group
        try:
            team = Team.objects.get(kc_id=kc_group.id)
            group, created = Group.objects.get_or_create(team=team)
            group.name = kc_group.name
        except Team.DoesNotExist:
            group, created = Group.objects.get_or_create(name=kc_group.name)
            try:
                # check if group has a team
                team = group.team
            except Exception as e:
                # create the team
                superusers = User.objects.filter(is_superuser=True)
                if superusers and len(superusers) > 0:
                    team = Team.objects.create(
                        owner=superusers[0],  # one of the superusers will be the default team owner
                        kc_id=kc_group.id,
                        group=group)
                    team.save()
        group.save()

    def sync_kc_organization(self, kc_organization):
        # sync the kc organization to Organization model
        organization, _ = Organization.objects.get_or_create(kc_id=kc_organization["id"])
        organization.name = kc_organization["name"]
        organization.save()

    def sync_kc_organizations(self, kc_organizations=None):
        if not kc_organizations:
            kc_organizations = self.auth_client.get_organizations()

        kc_organization_ids = set()
        for kc_organization in kc_organizations:
            self.sync_kc_organization(kc_organization)
            kc_organization_ids.add(kc_organization["id"])

        # Delete organizations that no longer exist in Keycloak
        Organization.objects.exclude(kc_id__in=kc_organization_ids).delete()

    def sync_kc_groups(self, kc_groups=None):
        # sync all groups
        if not kc_groups:
            kc_groups = self.auth_client.get_groups()
        for kc_group in kc_groups:
            self.sync_kc_group(kc_group)

    @transaction.atomic
    def sync_kc_user(self, kc_user: ch_models.User, is_superuser=False, delete=False):
        """
        Sync the kc user with the django user using kc_id for reliable lookups.
        ALWAYS creates both User and Member atomically - never returns a User without a Member.
        """
        user = get_user_by_kc_id(kc_user.id)

        if user is None:
            # User doesn't exist, create new one WITH Member atomically
            username = kc_user.username or kc_user.email
            if not username:
                raise ValueError(f"Keycloak user {kc_user.id} has no username or email")

            # Create user and member atomically
            user, user_created = User.objects.get_or_create(username=username)

            # CRITICAL: Ensure Member exists before proceeding
            try:
                member = Member.objects.get(user=user)
                # Member exists but might have wrong kc_id
                if member.kc_id != kc_user.id:
                    member.kc_id = kc_user.id
                    member.save()
            except Member.DoesNotExist:
                # Create the member relationship
                Member.objects.create(kc_id=kc_user.id, user=user)

        # Update user attributes
        user = self._map_kc_user(user, kc_user, is_superuser, delete)
        self.sync_kc_user_groups(kc_user)
        user.save()

        # FINAL SAFETY CHECK: Verify Member exists before returning
        # This ensures we never return a user without a Member
        try:
            _ = user.member  # Access member to trigger DoesNotExist if missing
        except:
            # This should never happen, but if it does, create Member immediately
            Member.objects.create(kc_id=kc_user.id, user=user)

        return user

    def sync_kc_user_groups(self, kc_user: ch_models.User):
        # Sync the user usergroups and memberships using kc_id for reliable lookups
        user = get_user_by_kc_id(kc_user.id)

        if user is None:
            raise ValueError(f"Django user not found for Keycloak user {kc_user.id}")

        user_groups = []
        for kc_group in [*kc_user.user_groups, *kc_user.organizations]:
            group, _ = Group.objects.get_or_create(name=kc_group.name)
            user_groups.append(group)
        user.groups.set(user_groups)
        user.save()

        # Ensure the member relationship exists and is correct
        try:
            member = user.member
            if member.kc_id != kc_user.id:
                member.kc_id = kc_user.id
                member.save()
        except Member.DoesNotExist:
            member = Member(user=user, kc_id=kc_user.id)
            member.save()

    def sync_kc_user_organizations(self, kc_user):
        # Ensure OrganizationMember records reflect Keycloak userOrganizations
        try:
            member = Member.objects.get(user__email=kc_user["email"])
        except Member.DoesNotExist:
            # Member not available yet; nothing to sync
            return

        desired_org_ids = set()
        kc_user_organizations = self.auth_client.get_user_organizations(kc_user["id"])
        for kc_org in kc_user_organizations:
            try:
                org = Organization.objects.get(kc_id=kc_org["id"])
            except Organization.DoesNotExist:
                # Organizations should already be synced; skip if missing
                continue
            desired_org_ids.add(org.id)

        existing_qs = OrganizationMember.objects.filter(member=member)
        existing_org_ids = set(existing_qs.values_list("organization_id", flat=True))

        to_add = desired_org_ids - existing_org_ids
        to_remove = existing_org_ids - desired_org_ids

        for org_id in to_add:
            OrganizationMember.objects.get_or_create(member=member, organization_id=org_id)

        if to_remove:
            OrganizationMember.objects.filter(member=member, organization_id__in=to_remove).delete()

    def sync_kc_users_groups(self):
        # cache all admin users to minimize KC rest api calls
        all_admin_users = self.auth_client.get_client_role_members(
            self.auth_service.get_client_name(),
            self.auth_service.get_admin_role()
        )

        # sync the users
        users = self.auth_client.get_users()
        for kc_user in users:
            # check if user in all_admin_users
            is_superuser = any([admin_user for admin_user in all_admin_users if admin_user["id"] == kc_user["id"]])
            self.sync_kc_user(kc_user, is_superuser)

        # sync the groups
        self.sync_kc_groups()

        # sync the organizations
        self.sync_kc_organizations()

        # sync the user groups and memberships
        for kc_user in users:
            self.sync_kc_user_groups(kc_user)
            self.sync_kc_user_organizations(kc_user)
