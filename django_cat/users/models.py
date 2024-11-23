from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from cheshire_cat.client import create_user, delete_user
from django.core.exceptions import RequestAborted

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_id = models.CharField(unique=True, null=True, blank=True)

    def __str__(self):
        """UserProfile name"""
        return str(self.username)

    def set_as_superuser(self):
        self.user.is_superuser = True
        self.user.is_staff = True

    @property
    def is_active(self):
        return self.user.is_active

    @property
    def username(self):
        return self.user.username
    
    @property
    def password(self):
        return self.user.password

    def __str__(self):
        return self.user.username
    
@receiver(post_save, sender=UserProfile)
def create_user_cheschire_cat(sender, instance: UserProfile, created: bool, **kwargs):
    if created:
        create_user(instance)


@receiver(pre_delete, sender=UserProfile)
def delete_user_chesshire_cat(sender, instance: UserProfile, **kwargs):
    if delete_user(instance) == False:
        raise RequestAborted(f"CHESCHIRE_CAT: User with id {instance.user_id} could not be deleted")