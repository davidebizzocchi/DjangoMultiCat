from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail

from django.conf import settings
from users.models import User
from users.models import UserProfile

ENV_TYPE = settings.ENVIRONMENT_TYPE.upper()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        # Create the UserProfile object
        UserProfile.objects.create(user=instance)

        # Send email to admins
        if settings.SEND_NEW_USER_MAIL:
            send_mail(
                    subject=f"[{ENV_TYPE}] New user: {instance.username}",
                    message=f"""
New user signup:\n
Environment: {ENV_TYPE}
Username: {instance.username}
PK: {instance.pk}
                    """,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=settings.ADMIN_EMAILS,
                    fail_silently=False,
                )

@receiver(pre_delete, sender=User)
def deleted_user(sender, instance: User, **kwargs):
    # Send email to admins
    if settings.SEND_DELETED_USER_MAIL:
        send_mail(
                subject=f"[{ENV_TYPE}] User deleted: {instance.username}",
                message=f"""
User deleted their account:\n
Environment: {ENV_TYPE}
Username: {instance.username}
PK: {instance.pk}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=settings.ADMIN_EMAILS,
                fail_silently=False,
            )
