from django.contrib import admin

from chat.models import Chat, Message

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'sender', 'text_preview', 'timestamp')
    list_filter = ('sender', 'timestamp', 'user')
    search_fields = ('text', 'user__username', "sender", "chat__chat_id")
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)
    
    def text_preview(self, obj):
        """Restituisce un'anteprima del testo limitata a 50 caratteri"""
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text Preview'


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('user', 'chat_id')
    search_fields = ('chat_id', 'user__username')
    list_filter = ('user',)
