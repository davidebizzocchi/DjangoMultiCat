from django.contrib import admin
from file.models import File, FileLibraryAssociation

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('title', 'file_id', 'user', 'ingested')
    list_filter = ('ingested', 'user')
    search_fields = ('title', 'file_id', 'user__username')
    readonly_fields = ('file_id', 'hash')

@admin.register(FileLibraryAssociation)
class FileLibraryAssociationAdmin(admin.ModelAdmin):
    list_display = ('file', 'library')
    list_filter = ('library',)
    search_fields = ('file__title', 'library__name')
