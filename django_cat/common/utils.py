from django.db import models
from users.models import User, UserProfile


class BaseUserModel(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name="%(class)s_set"
    )

    @property
    def related_name(self):
        return self._meta.verbose_name_plural

    @property
    def userprofile(self) -> UserProfile:
        return self.user.userprofile
    
    @property
    def client(self):
        return self.userprofile.client
    

    class Meta:
        ordering = ('user',)
        abstract = True