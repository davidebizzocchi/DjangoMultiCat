from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import EmailMultiAlternatives  # Changed from send_mail
from django.conf import settings
from django.urls import reverse
from django.template.loader import render_to_string
from users.models import User, UserProfile

ENV_TYPE = settings.ENVIRONMENT_TYPE.upper()

def _send_html_email(subject, context, template_name, recipient_list):
    """Helper function to send HTML emails with plain text fallback"""
    text_body = render_to_string(f'emails/{template_name}.txt', context)
    html_body = render_to_string(f'emails/{template_name}.html', context)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list,
    )
    email.attach_alternative(html_body, "text/html")
    email.send(fail_silently=False)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        profile = UserProfile.objects.create(user=instance)

        if settings.SEND_NEW_USER_MAIL:
            context = {
                'title': 'New User Registration',
                'environment': ENV_TYPE,
                'username': instance.username,
                'user_id': instance.pk,
                'email': instance.email or 'Not provided',
                'approve_url': f"{settings.SITE_URL}{reverse('users:manage:approve', kwargs={'pk': profile.pk})}",
                'admin_url': f"{settings.SITE_URL}/admin/users/user/{instance.pk}/change/",
            }
            
            _send_html_email(
                subject=f"[{ENV_TYPE}] - New User: {instance.username}",
                context=context,
                template_name='new_user_notification',
                recipient_list=settings.ADMIN_EMAILS,
            )

@receiver(pre_delete, sender=User)
def deleted_user(sender, instance: User, **kwargs):
    if settings.SEND_DELETED_USER_MAIL:
        context = {
            'title': 'User Account Deleted',
            'environment': ENV_TYPE,
            'username': instance.username,
            'user_id': instance.pk,
            'email': instance.email or 'Not provided',
            'last_login': instance.last_login.strftime('%Y-%m-%d %H:%M') if instance.last_login else 'Never',
        }
        
        _send_html_email(
            subject=f"[{ENV_TYPE}] - User Deleted: {instance.username}",
            context=context,
            template_name='user_deleted_notification',
            recipient_list=settings.ADMIN_EMAILS,
        )