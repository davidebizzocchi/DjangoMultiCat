from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from cheshire_cat.client import create_user, delete_user, get_user_id
from django.core.exceptions import RequestAborted
from cheshire_cat.client import connect_user


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cheschire_id = models.CharField(unique=True, null=True, blank=True)

    def __str__(self):
        """UserProfile name"""
        return str(self.username)

    def set_as_superuser(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()

    @property
    def set_id(self):
        self.cheschire_id = get_user_id(self.username)
        self.save()
        return self.cheschire_id

    def set_manual_id(self, id):
        self.cheschire_id = id
        self.save()

    @property
    def client(self):
        return connect_user(self.cheschire_id)

    @property
    def is_active(self):
        return self.user.is_active

    @property
    def username(self):
        return self.user.username
    
    @property
    def password(self):
        return self.user.password
    
    @staticmethod
    def get_admin() -> "UserProfile":
        return UserProfile.objects.get(user__username="admin")
    
    def delete(self):
        self.user.delete()

    def __str__(self):
        return self.user.username
    
@receiver(post_save, sender=UserProfile)
def create_user_cheshire_cat(sender, instance: UserProfile, created: bool, **kwargs):
    if created:
        create_user(instance)


@receiver(pre_delete, sender=UserProfile)
def delete_user_chesshire_cat(sender, instance: UserProfile, **kwargs):
    if delete_user(instance) == False:
        raise RequestAborted(f"CHESHIRE_CAT: User with ID {instance.cheschire_id} could not be deleted")