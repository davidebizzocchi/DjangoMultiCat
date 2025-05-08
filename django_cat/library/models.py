import uuid
from django.db import models
from users.models import User, UserProfile
from common.utils import BaseUserModel
from icecream import ic


class Library(BaseUserModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='libraries')
    name = models.CharField(max_length=255)
    library_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    
    @property
    def files(self):
        """Returns all files associated with this library with optimized query"""
        
        from file.models import File  # Import here to avoid circular imports
        return File.objects.filter(
            associations__library=self
        ).values(
            'id',
            'title', 
            'file_id',
            'ingested',
            'user__username',
            'user__userprofile__cheshire_id',
        )
    
    @property
    def files_id(self):
        from file.models import File
        return File.objects.filter(
            associations__library=self
        ).values_list('file_id', flat=True)
    
    def add_new_chat(self, chat_id: str):
        """Add chat to client"""
        
        for file_id in self.files_id:
            ic("chat add", chat_id, file_id)
            self.client.add_file_to_chats(str(file_id), chat_id)

    def remove_chat(self, chat_id: str):
        """Remove chat from client"""
        
        for file_id in self.files_id:
            ic("chat delete", chat_id, file_id)
            self.client.remove_file_to_chats(str(file_id), chat_id)

    def add_file_to_existing_chats(self, file_id: str):
        """Called by FileLibraryAssociation"""
        for chat_id in self.chats.values_list("chat_id", flat=True):
            ic("file add", chat_id, file_id)
            self.client.add_file_to_chats(file_id, str(chat_id))

    def remove_file_from_existing_chats(self, file_id: str):
        """Called by FileLibraryAssociation"""
        for chat_id in self.chats.values_list("chat_id", flat=True):
            ic("file delete", chat_id, file_id)
            self.client.remove_file_to_chats(file_id, str(chat_id))

    def __str__(self):
        return f"Library {self.name}, files: {self.files_id.count()} id: {self.library_id}"
    
    class Meta:
        verbose_name = "library"
        verbose_name_plural = "libraries"