import logging
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_welcome_email(self, user_id: str, token: str):
    """Send password setup email to new subscriber."""
    from apps.accounts.models import User
    try:
        user = User.objects.get(id=user_id)
        setup_url = f"{settings.SITE_URL}/accounts/setup/{token}/"

        subject = f'Welcome to NexaFlow — Set up your password'
        html_message = render_to_string('emails/welcome.html', {
            'user': user,
            'setup_url': setup_url,
        })
        plain_message = (
            f'Welcome to NexaFlow, {user.username}!\n\n'
            f'Click the link below to set your password and access your dashboard:\n'
            f'{setup_url}\n\n'
            f'This link expires in 48 hours.\n\n'
            f'— The NexaFlow Team'
        )

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f'Welcome email sent to {user.email}')

    except Exception as exc:
        logger.error(f'Failed to send welcome email to user {user_id}: {exc}')
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_subscription_cancelled_email(self, user_id: str):
    from apps.accounts.models import User
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject='Your NexaFlow subscription has been cancelled',
            message=(
                f'Hi {user.username},\n\n'
                f'Your NexaFlow subscription has been cancelled.\n'
                f'You can re-subscribe at any time from our website.\n\n'
                f'— The NexaFlow Team'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception as exc:
        raise self.retry(exc=exc)
