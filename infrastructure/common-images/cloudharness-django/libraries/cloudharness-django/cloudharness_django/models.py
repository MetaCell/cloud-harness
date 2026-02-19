from django.db import models
from django.contrib.auth.models import Group, User

# Create your models here.


class Team(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    kc_id = models.CharField(max_length=100)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.group.name}"


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    kc_id = models.CharField(max_length=100, db_index=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"


class Organization(models.Model):
    """
    Represents a Keycloak organization synced to Django.
    This is the base organization model - applications can extend it with
    additional fields by creating a OneToOne relationship.
    Organizations can be created without kc_id and will be synced by name
    when a matching Keycloak organization is found.
    """
    name = models.CharField(max_length=256, unique=True)
    kc_id = models.CharField(max_length=100, db_index=True, null=True, blank=True, unique=True)

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"

    def __str__(self):
        return self.name


class OrganizationMember(models.Model):
    """
    Represents membership of a User in a Keycloak Organization.
    A user can belong to multiple organizations.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='members')

    class Meta:
        verbose_name = "Organization Member"
        verbose_name_plural = "Organization Members"
        unique_together = ('user', 'organization')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name}"
