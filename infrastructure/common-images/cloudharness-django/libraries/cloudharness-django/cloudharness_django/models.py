from django.db import models
from django.contrib.auth.models import Group, User

# Create your models here.
class Team(models.Model):
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    kc_id = models.CharField(max_length = 100)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return f"{self.group.name}"


class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    kc_id = models.CharField(max_length = 100)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"

