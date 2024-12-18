import uuid
from django.db import models
from users.models import User, UserProfile


class Library(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='libraries')
    name = models.CharField(max_length=255)
    library_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)

    @property
    def userprofile(self) -> UserProfile:
        return self.user.userprofile
    
    @property
    def client(self):
        return self.userprofile.client
    
    def __str__(self):
        return f"Library {self.name} of {self.user.username}, id: {self.library_id}"
    
    class Meta:
        ordering = ['user']