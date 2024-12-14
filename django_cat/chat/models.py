from django.db import models
from django.contrib.auth.models import User

class Message(models.Model):
    class Sender(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages')
    text = models.TextField()
    sender = models.CharField(
        max_length=10,
        choices=Sender.choices,
        default=Sender.USER
    )
    timestamp = models.DateTimeField(auto_now_add=True)

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