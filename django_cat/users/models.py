from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser, BaseUserManager
from allauth.socialaccount.models import SocialAccount
from cheshire_cat.client import get_user_id, connect_user


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("L'email è obbligatoria"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

    def save(self, *args, **kwargs):
        self.username = self.email
        return super().save(*args, **kwargs)

class User(AbstractUser):
    email = models.EmailField(_("email address"), unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    # Add unique related_name attributes to avoid clashes
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to. A user will get all permissions granted to each of their groups.'),
        related_name="custom_user_set",  # Unique related_name
        related_query_name="user",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name="custom_user_set",  # Unique related_name
        related_query_name="user",
    )

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def set_as_superuser(self):
        self.is_staff = True
        self.is_superuser = True
        self.save()

    def save(self, *args, **kwargs):
        self.username = self.email
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cheshire_id = models.CharField(unique=True, null=True, blank=True)
    configured = models.BooleanField(default=False, blank=True)

    name = models.CharField(max_length=100, blank=True, null=True)
    is_approved = models.BooleanField(default=False)

    avatar_url = models.URLField(blank=True, null=True)

    @property
    def configured(self):
        return self.name is not None

    def __str__(self):
        """UserProfile name"""
        return str(self.email)

    def set_as_superuser(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()

    def set_id(self):
        self.cheshire_id = get_user_id(self.email)
        self.save()
        return self.cheshire_id

    def set_manual_id(self, id):
        self.cheshire_id = id
        self.save()

    @property
    def client(self):
        return connect_user(self.cheshire_id)

    @property
    def is_active(self):
        return self.user.is_active

    @property
    def username(self):
        return self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def password(self):
        return self.user.password

    @property
    def is_staff(self):
        return self.user.is_staff

    @property
    def is_superuser(self):
        return self.user.is_superuser

    @staticmethod
    def get_admin() -> "UserProfile":
        return UserProfile.objects.get(pk=1)

    def delete(self):
        self.user.delete()

    def __str__(self):
        return self.user.email

    def update_instance(self):
        """Inizializza i valori del modello, quelli che richiedono una query solitamente."""
        self._update_allauth()

    def _update_allauth(self):
        """Inizializza il modello con eventuali valori da allauth."""
        if (
            account := SocialAccount.objects.filter(user=self.user, provider="google")
        ).exists():
            data = account.values("extra_data").first()
            self.avatar_url = data["picture"]
            self.save()

    def initialize(self):
        """Initialize the user profile."""

        self.avatar_url = settings.DEFAULT_AVATAR_URL
        self.save(update_fields=["avatar_url"])

    def approve(self, is_approved: bool = True):
        """Approve user (or revoke approval)"""

        self.is_approved = is_approved
        self.save(update_fields=["is_approved"])
