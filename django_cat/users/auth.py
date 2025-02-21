from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()

class UsernameAuthenticationBackend(BaseBackend):
    """
    Custom authentication backend that authenticates users using only their username.
    """
    def authenticate(self, request, username=None, **kwargs):
        try:
            # Find user with provided username
            user = User.objects.get(username=username)
            return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None