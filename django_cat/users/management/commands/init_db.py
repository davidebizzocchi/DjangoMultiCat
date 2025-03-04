from django.core.management.base import BaseCommand
from users.models import User, UserProfile
from agent.utils import sync_agent_with_cat

class Command(BaseCommand):
    help = "Create an admin user and profile"

    def handle(self, *args, **kwargs):
        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={'password': 'admin'}
        )

        if created:
            self.stdout.write(self.style.SUCCESS("Admin user created successfully!"))
        else:
            self.stdout.write(self.style.WARNING("Admin user already exists."))

        # Create or get the admin profile
        user_profile, profile_created = UserProfile.objects.get_or_create(user=admin)

        if profile_created:
            user_profile.set_id()
            user_profile.set_as_superuser()
            user_profile.save()
            self.stdout.write(self.style.SUCCESS("Admin profile created and configured!"))
        else:
            self.stdout.write(self.style.WARNING("Admin profile already exists."))

        # SETUP
        
        # Sync agents with CAT
        sync_agent_with_cat()