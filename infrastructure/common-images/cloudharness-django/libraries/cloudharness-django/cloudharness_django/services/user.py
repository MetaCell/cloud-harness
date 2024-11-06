from django.contrib.auth.models import User, Group

from cloudharness_django.models import Team, Member
from cloudharness_django.services.auth import AuthorizationLevel


def get_user_by_kc_id(kc_id) -> User:
    try:
        return Member.objects.get(kc_id=kc_id).user
    except Member.DoesNotExist:
        return None


class UserService:
    def __init__(self, auth_service):
        self.auth_service = auth_service
        self.auth_client = auth_service.get_auth_client()

    def _get_kc_user(self, user):
        # get the kc user by user email
        all_users = self.auth_client.get_users()
        return [kc_user for kc_user in all_users if kc_user["email"] == user.email][0]

    def _map_kc_user(self, user, kc_user=None, is_superuser=False, delete=False):
        # map a kc user to a django user
        if not kc_user:
            kc_user = self._get_kc_user(user)

        user_auth_level = self.auth_service.get_auth_level(kc_user)
        if user_auth_level == AuthorizationLevel.ADMIN:
            is_superuser = True
        # update the superuser and staff status of the user
        user.is_staff = is_superuser
        user.is_superuser = is_superuser

        user.username = kc_user.get("username", kc_user["email"])
        user.first_name = kc_user.get("firstName", "")
        user.last_name = kc_user.get("lastName", "")
        user.email = kc_user.get("email", "")

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

    def sync_kc_group(self, kc_group):
        # sync the kc group with the django group
        try:
            team = Team.objects.get(kc_id=kc_group["id"])
            group, created = Group.objects.get_or_create(team=team)
            group.name = kc_group["name"]
        except Team.DoesNotExist:
            group, created = Group.objects.get_or_create(name=kc_group["name"])
            try:
                # check if group has a team
                team = group.team
            except Exception as e:
                # create the team
                superusers = User.objects.filter(is_superuser=True)
                if superusers and len(superusers) > 0:
                    team = Team.objects.create(
                        owner=superusers[0],  # one of the superusers will be the default team owner
                        kc_id=kc_group["id"],
                        group=group)
                    team.save()
        group.save()

    def sync_kc_groups(self, kc_groups=None):
        # sync all groups
        if not kc_groups:
            kc_groups = self.auth_client.get_groups()
        for kc_group in kc_groups:
            self.sync_kc_group(kc_group)

    def sync_kc_user(self, kc_user, is_superuser=False, delete=False):
        # sync the kc user with the django user

        user, created = User.objects.get_or_create(username=kc_user["username"])

        member, created = Member.objects.get_or_create(user=user)
        member.kc_id = kc_user["id"]
        member.save()
        user = self._map_kc_user(user, kc_user, is_superuser, delete)
        user.save()
        return user

    def sync_kc_user_groups(self, kc_user):
        # Sync the user usergroups and memberships
        user = User.objects.get(username=kc_user["email"])
        user_groups = []
        for kc_group in kc_user["userGroups"]:
            user_groups += [Group.objects.get(name=kc_group["name"])]
        user.groups.set(user_groups)
        user.save()

        try:
            if user.member.kc_id != kc_user["id"]:
                user.member.kc_id = kc_user["id"]
        except Member.DoesNotExist:
            member = Member(user=user, kc_id=kc_user["id"])
            member.save()

    def sync_kc_users_groups(self):
        # cache all admin users to minimize KC rest api calls
        all_admin_users = self.auth_client.get_client_role_members(
            self.auth_service.get_client_name(),
            self.auth_service.get_admin_role()
        )

        # sync the users
        for kc_user in self.auth_client.get_users():
            # check if user in all_admin_users
            is_superuser = any([admin_user for admin_user in all_admin_users if admin_user["email"] == kc_user["email"]])
            self.sync_kc_user(kc_user, is_superuser)

        # sync the groups
        self.sync_kc_groups()

        # sync the user groups and memberships
        for kc_user in self.auth_client.get_users():
            self.sync_kc_user_groups(kc_user)
