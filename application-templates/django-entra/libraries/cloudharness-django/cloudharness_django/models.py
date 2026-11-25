from django.db import models
from django.contrib.auth.models import User


class Member(models.Model):
    """Links a Django user to its Microsoft Entra identity (the `oid` claim)."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    oid = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name}"
