import uuid
from django.db import models
from users.models import User, UserProfile
from app.utils import BaseUserModel


class Library(BaseUserModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='libraries')
    name = models.CharField(max_length=255)
    library_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    
    def __str__(self):
        return f"Library {self.name} of {self.user.username}, id: {self.library_id}"
    
    class Meta:
        verbose_name = "library"
        verbose_name_plural = "libraries"