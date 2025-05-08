"""users/admin.py - Module providing admin functions"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import UserProfile, User


# Inline per UserProfile nel pannello di amministrazione di User
class UserProfileInline(admin.StackedInline):
    """inline edit"""

    model = UserProfile
    can_delete = False


class UserAdmin(BaseUserAdmin):
    """inline edit"""

    inlines = (UserProfileInline,)


# Registra il modello UserProfile e CustomUser nel pannello di amministrazione
admin.site.register(UserProfile)
admin.site.register(User)
