from django.core.management.base import BaseCommand
from users.models import User, UserProfile
from allauth.account.models import EmailAddress
from agent.utils import sync_agent_with_cat

class Command(BaseCommand):
    help = "Create an admin user and profile"

    def handle(self, *args, **kwargs):
        # Create admin user

        admin_kwargs = {
            'email': "admin@gmail.com",
            "password": "admin"
        }

        if User.objects.filter(**admin_kwargs).exists():
            admin = User.objects.get(**admin_kwargs)
            created = True
        else:
            admin = User.objects.create_user(**admin_kwargs)
            created = False

        EmailAddress.objects.get_or_create(
            email=admin.email,
            user=admin,
            primary=True,
            verified=True
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Admin user created successfully!"))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists."))

        # Create or get the admin profile
        user_profile, profile_created = UserProfile.objects.get_or_create(user=admin)

        if profile_created:
            user_profile.name = "Admin"
            user_profile.is_approved = True
            user_profile.set_id()
            user_profile.set_as_superuser()
            user_profile.save()
            self.stdout.write(self.style.SUCCESS("Admin profile created and configured!"))
        else:
            self.stdout.write(self.style.WARNING("Admin profile already exists."))

        # SETUP
        
        # Sync agents with CAT
        sync_agent_with_cat()