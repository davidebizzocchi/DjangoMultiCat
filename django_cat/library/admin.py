from django.contrib import admin
from .models import Library

@admin.register(Library)
class LibraryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'library_id')
    search_fields = ('name', 'user__username', 'library_id')
    list_filter = ('user',)
