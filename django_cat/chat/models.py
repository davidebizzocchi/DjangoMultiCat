from django.db import models
from users.models import User, UserProfile
import uuid
from app.utils import BaseUserModel
from library.models import Library


class Chat(BaseUserModel):
    chat_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    libraries = models.ManyToManyField(Library, related_name='chats', blank=True)

    def send_message(self, message):
        """Send message to cat"""
        return self.client.send(message, chat_id=self.chat_id)

    def stream(self):
        """Stream messages from this specific chat"""
        return self.client.stream(chat_id=self.chat_id)

    def wait_message_content(self):
        """Wait and return last message content for this specific chat"""
        return self.client.wait_message_content(chat_id=self.chat_id)

    def __str__(self):
        return f"Chat with {self.user.username}, id: {self.chat_id}"
    
    def delete(self, *args, **kwargs):
        """Delete chat and all related messages"""
        
        result = self.client.delete_chat(self.chat_id)

        return super().delete(*args, **kwargs)
        
    def wipe(self):
        """Wipe all messages from chat"""
        return self.client.wipe_chat(self.chat_id)
    
    def get_history(self):
        """Get chat history"""
        return self.client.get_chat_history(self.chat_id)

    class Meta:
        verbose_name = "chat"
        verbose_name_plural = "chats"

class Message(models.Model):
    class Sender(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
    
    text = models.TextField()
    sender = models.CharField(
        max_length=10,
        choices=Sender.choices,
        default=Sender.USER
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')

    @classmethod
    def get_last_assistant_message(self, user):
        """Get last assistant message for a specific user"""
        return self.objects.select_related('user').filter(
            user=user,
            sender=self.Sender.ASSISTANT
        ).order_by('-timestamp').first()

    def __str__(self):
        return f"{self.sender} at {self.timestamp}: {self.text[:50]}..."

    class Meta:
        ordering = ['timestamp']

