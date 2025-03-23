from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from cheshire_cat.client import create_user, delete_user
from django.core.exceptions import RequestAborted

from users.models import UserProfile


@receiver(post_save, sender=UserProfile)
def create_user_cheshire_cat(sender, instance: UserProfile, created: bool, **kwargs):
    if created:
        create_user(instance)


@receiver(pre_delete, sender=UserProfile)
def delete_user_chesshire_cat(sender, instance: UserProfile, **kwargs):
    delete_user(instance)