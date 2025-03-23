from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail

from django.conf import settings
from django.contrib.auth.models import User
from users.models import UserProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        # Create the UserProfile object
        UserProfile.objects.create(user=instance)

        # Send email to admins
        send_mail(
                subject=f"New user: {instance.username}",
                message=f"""
Nuovo utente registrato:\n
username : {instance.username},
pk: {instance.pk},
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.ADMIN_EMAILS,
                fail_silently=False,
            )

@receiver(pre_delete, sender=User)
def deleted_user(sender, instance: User, **kwargs):
    # Send email to admins
        send_mail(
                subject=f"User deleted: {instance.username}",
                message=f"""
L'utente ha cancellato il suo account:\n
username : {instance.username},
pk: {instance.pk},
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.ADMIN_EMAILS,
                fail_silently=False,
            )