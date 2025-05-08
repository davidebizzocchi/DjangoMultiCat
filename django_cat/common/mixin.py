from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import AnonymousUser

class LoginRequiredMixin(LoginRequiredMixin):
    def __init__(self, *args, **kwargs):
        # Normalizza gli attributi di classe
        self.is_superuser_required: bool = getattr(self, 'is_superuser_required', False)
        self.is_staff_required: bool = getattr(self, 'is_staff_required', False)

        super().__init__(*args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        from users.models import UserProfile, User


        if request.user.is_authenticated:
            self.usr: User = request.user
            self.user: UserProfile = self.usr.userprofile

            if (
                result := self.check_user()
            ) is not None:
                return result
            
            if (
                result := self.pre_dispatch_login(request, *args, **kwargs)
            ) is not None:
                return result

        return super().dispatch(request, *args, **kwargs)
    
    def check_user(self):
        if self.is_superuser_required and not self.usr.is_superuser:
            return self.handle_no_permission()
    
        if self.is_staff_required and not self.usr.is_staff:
            raise self.handle_no_permission()
        
        return None

    def pre_dispatch_login(self, request, *args, **kwargs):
        # This let to recall also pre_dispatch_login method from super class
        if hasattr(super(), "pre_dispatch_login"):
            return super().pre_dispatch_login(request, *args, **kwargs)
        return None