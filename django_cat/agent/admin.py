from django.contrib import admin

from agent.models import Agent

@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ('name', 'agent_id', 'user', 'is_default', 'instructions_preview', 'created_at', 'updated_at')
    list_filter = ('agent_id', 'created_at', 'updated_at', 'user')
    search_fields = ('name', 'agent_id', 'instructions', 'user__username')
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)
    readonly_fields = ('agent_id',)

    def instructions_preview(self, obj):
        """Returns a preview of the instructions limited to 50 characters"""
        return obj.instructions[:50] + '...' if len(obj.instructions) > 50 else obj.instructions
    instructions_preview.short_description = 'Instructions Preview'
