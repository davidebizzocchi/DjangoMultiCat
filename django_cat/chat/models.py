import uuid

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.db.models import QuerySet

from common.utils import BaseUserModel
from cheshire_cat.types.cat_types import UserMessage
from cheshire_cat.types.new_types import CatMessage
from library.models import Library
from agent.models import Agent
from file.models import File

from icecream import ic


class Chat(BaseUserModel):
    messages: QuerySet["Message"]

    agent = models.ForeignKey(Agent, on_delete=models.SET(Agent.get_default), related_name='chats', null=True, blank=True, default=None)

    title = models.CharField(max_length=255, default="New Chat")
    chat_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    libraries = models.ManyToManyField(Library, related_name='chats', blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    @property
    def files(self):
        from file.models import File

        """Returns all files associated with this chat with optimized query"""
        return File.objects.filter(
            associations__library__chats=self  # Naviga la relazione
        ).distinct()

    def send_message(self, message):
        """Send message to cat"""

        if isinstance(message, Message):
            message = message.text

        return self.client.send(message, chat_id=self.chat_id, agent_id=self.agent.agent_id)

    def stream(self):
        """Stream messages from this specific chat"""
        yield from self.client.stream(chat_id=self.chat_id)
    
    def wait_message_content(self):
        """Wait and return last message content for this specific chat"""
        return self.client.wait_message_content(chat_id=self.chat_id)

    def wipe(self):
        """Wipe all messages from chat"""
        return self.client.wipe_chat(self.chat_id)

    def get_history(self):
        """Get chat history"""
        return self.client.get_chat_history(self.chat_id)

    def __str__(self):
        return f"Chat with {self.user.username}, id: {self.chat_id}"

    def save(self, *args, **kwargs):
        """Save chat and create chat on cat"""

        first_save = False
    
        if not self.pk:
            first_save = True

        if self.agent is None:
            self.agent = Agent.get_default()
    
        super().save(*args, **kwargs)

    
        if first_save and self.libraries:
            for library in self.libraries.all():
                ic("chat create", library)
                library.add_new_chat(str(self.chat_id))

        return None

    def delete(self, *args, **kwargs):
        """Delete chat and all related messages"""

        files = self.files
    
        result = self.client.delete_chat(self.chat_id)
    
        for file in files:
            ic("chat delete", file.file_id)
            self.client.remove_file_to_chats(file, str(self.chat_id))

        super().delete(*args, **kwargs)

        return result

    @property
    def timedelta(self):
        """
        Transform a Django DateTimeField value into a human-readable string
        based on the number of days from the current date.

        Args:
            datetime_value (datetime): The datetime value to transform.

        Returns:
            str: A human-readable string like "today", "yesterday", "Monday", "1 week ago", "2 weeks ago", "1 month ago", etc.
        """
        # Get the current date and time
        now = timezone.now()

        # Calculate the difference between the current date and the given datetime
        delta = now - self.created_at

        # Handle "today" and "yesterday"
        if delta.days == 0:
            return "Today"
        elif delta.days == 1:
            return "Yesterday"

        # Handle weekdays (up to 6 days ago)
        elif delta.days < 7:
            return self.created_at.strftime("%A")  # Returns the day of the week (e.g., "Monday")

        # Handle weeks (up to 3 weeks ago)
        elif delta.days < 28:
            weeks = delta.days // 7
            if weeks == 1:
                return "Last week"
            else:
                return f"{weeks} weeks ago"

        # Handle months
        else:
            months = delta.days // 30
            if months == 1:
                return "Last month"
            elif months < 3:
                return f"{months} month ago"
            elif delta.days < 365:
                return self.created_at.strftime("%B")  # Returns "January"
            else:
                return self.created_at.strftime("%B %Y")  # Returns "January 2024"

    @property
    def name(self):
        """Return the chat name"""

        if self.title == "New Chat":
            if self.messages.count() > 0:
                self.title = self.messages.first().text
                self.save()
   
        return self.title

    class Meta:
        verbose_name = "chat"
        verbose_name_plural = "chats"

        ordering = ['-created_at']

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

    annotations = models.JSONField(default=list, blank=True)

    @classmethod
    def get_last_assistant_message(self, user):
        """Get last assistant message for a specific user"""
        return self.objects.select_related('user').filter(
            user=user,
            sender=self.Sender.ASSISTANT
        ).order_by('-timestamp').first()

    def build_single_file_annotation(self, info: tuple | str | File, save=False):
        """Build annotations for a single file"""

        score = 0.0
        if hasattr(info, "original"):
            info = info.original

        if isinstance(info, tuple):
            file = info[0]
            score = round(info[1], 4) * 100

        if isinstance(file, str):
            file = File.objects.only("id", "title", "file_id").get(file_id=file)

        if not isinstance(file, File):
            raise ValueError("Invalid file type")

        annotations = {
            "file_id": file.file_id,
            "filename": file.title,
            "link": reverse("file:assoc", kwargs={"file_id": file.file_id}),
            "preview": file.link,
            "score": score,
        }

        if save:
            self.annotations.append(annotations)
            self.save()

        return annotations

    def build_multiple_files_annotation(self, files: list[str | File], save=False):
        """Build annotations for multiple files"""
        annotations = []
        for file in files:
            annotations.append(
                self.build_single_file_annotation(file, save=False)
            )

    def cat_model(self):
        """Return the message as a cat model"""

        if self.sender == self.Sender.USER:
            return UserMessage(text=self.text, chat_id=self.chat.chat_id, user_id=self.chat.userprofile.cheshire_id, when=self.timestamp.timestamp())
        else:
            return CatMessage(text=self.text, chat_id=self.chat.chat_id, user_id=self.chat.userprofile.cheshire_id, when=self.timestamp.timestamp())


    def send(self):
        """Send message to cat"""
        return self.chat.send_message(self.text)

    def __str__(self):
        return f"{self.sender} at {self.timestamp}: {self.text[:50]}..."

    class Meta:
        ordering = ['timestamp']

