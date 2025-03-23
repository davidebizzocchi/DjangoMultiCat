from django.db import models
from django.contrib.auth.models import User
from cheshire_cat.client import get_user_id
from cheshire_cat.client import connect_user


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cheshire_id = models.CharField(unique=True, null=True, blank=True)

    def __str__(self):
        """UserProfile name"""
        return str(self.username)

    def set_as_superuser(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()

    def set_id(self):
        self.cheshire_id = get_user_id(self.username)
        self.save()
        return self.cheshire_id

    def set_manual_id(self, id):
        self.cheshire_id = id
        self.save()

    @property
    def client(self):
        return connect_user(self.cheshire_id)

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
    