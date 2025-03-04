from django.contrib import admin
from users.models import UserProfile

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'cheshire_id', 'is_active')
    search_fields = ('user__username', 'cheshire_id')