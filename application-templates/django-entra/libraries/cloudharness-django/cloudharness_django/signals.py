from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from cloudharness_django.middleware import invalidate_user_cache
from cloudharness_django.models import Member


@receiver(post_save, sender=User)
def drop_cached_bearer_user(sender, instance: User, **kwargs):
    """A changed user (e.g. deactivated) is not served from the bearer token cache."""
    member = Member.objects.filter(user=instance).first()
    if member:
        invalidate_user_cache(member.oid)
