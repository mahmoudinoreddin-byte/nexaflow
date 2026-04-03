import json
import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from django.utils.crypto import constant_time_compare

from apps.accounts.models import User, ActivityLog
from apps.services.models import Service, UserService
from .models import WebhookLog
from .tasks import send_welcome_email

logger = logging.getLogger(__name__)


def _generate_username(email: str) -> str:
    base = email.split('@')[0].lower()
    base = ''.join(c for c in base if c.isalnum() or c in '_-')[:30]
    username = base
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f'{base}{counter}'
        counter += 1
    return username


@csrf_exempt
@require_POST
def gumroad_webhook(request):
    """
    Handles Gumroad ping webhooks.
    Configure in Gumroad → Settings → Advanced → Webhooks
    URL: https://yourdomain.com/webhooks/gumroad/
    """
    try:
        # Parse form data (Gumroad sends application/x-www-form-urlencoded)
        data = request.POST.dict()
        email = data.get('email', '').lower().strip()
        sale_id = data.get('sale_id', '')
        event_type = _detect_event(data)

        log = WebhookLog(
            event_type=event_type,
            gumroad_sale_id=sale_id,
            email=email,
            payload=data,
        )

        if not email:
            log.status = WebhookLog.STATUS_FAILED
            log.error_message = 'Missing email in payload'
            log.save()
            return HttpResponse('Missing email', status=400)

        if event_type == WebhookLog.EVENT_SALE:
            _handle_sale(data, email, sale_id, log)
        elif event_type == WebhookLog.EVENT_REFUND:
            _handle_refund(email, sale_id, log)
        elif event_type in (WebhookLog.EVENT_SUBSCRIPTION_ENDED, WebhookLog.EVENT_CANCELLATION):
            _handle_cancellation(email, log)
        elif event_type == WebhookLog.EVENT_SUBSCRIPTION_RESTARTED:
            _handle_reactivation(email, log)

        log.save()
        return HttpResponse('OK', status=200)

    except Exception as e:
        logger.exception('Webhook processing error')
        WebhookLog.objects.create(
            status=WebhookLog.STATUS_FAILED,
            error_message=str(e),
            payload=request.POST.dict(),
        )
        return HttpResponse('Error', status=500)


def _detect_event(data: dict) -> str:
    if data.get('refunded') == 'true':
        return WebhookLog.EVENT_REFUND
    if data.get('subscription_cancelled') == 'true':
        return WebhookLog.EVENT_CANCELLATION
    if data.get('subscription_ended') == 'true':
        return WebhookLog.EVENT_SUBSCRIPTION_ENDED
    if data.get('subscription_restarted') == 'true':
        return WebhookLog.EVENT_SUBSCRIPTION_RESTARTED
    if data.get('sale_id'):
        return WebhookLog.EVENT_SALE
    return WebhookLog.EVENT_UNKNOWN


def _handle_sale(data: dict, email: str, sale_id: str, log: WebhookLog):
    # Check duplicate
    if User.objects.filter(gumroad_sale_id=sale_id).exists():
        log.status = WebhookLog.STATUS_DUPLICATE
        log.error_message = f'Duplicate sale_id: {sale_id}'
        return

    # Determine plan from product name/price
    product_name = data.get('product_name', '').lower()
    if 'enterprise' in product_name:
        plan = User.PLAN_ENTERPRISE
    else:
        plan = User.PLAN_PRO

    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'username': _generate_username(email),
            'plan': plan,
            'status': User.STATUS_INACTIVE,  # inactive until password is set
            'gumroad_sale_id': sale_id,
            'gumroad_subscription_id': data.get('subscription_id', ''),
            'gumroad_product_id': data.get('product_id', ''),
            'subscription_start': timezone.now(),
            'subscription_end': timezone.now() + timezone.timedelta(days=30),
        }
    )

    if not created:
        # Existing user re-subscribed
        user.plan = plan
        user.status = User.STATUS_ACTIVE
        user.gumroad_sale_id = sale_id
        user.subscription_start = timezone.now()
        user.subscription_end = timezone.now() + timezone.timedelta(days=30)
        user.save()
        ActivityLog.objects.create(
            user=user, action='Resubscribed', description=f'New Gumroad sale: {sale_id}', icon='🔄'
        )
    else:
        # Assign all active services to new user
        active_services = Service.objects.filter(status=Service.STATUS_ACTIVE)
        UserService.objects.bulk_create([
            UserService(user=user, service=svc) for svc in active_services
        ], ignore_conflicts=True)

        # Generate password setup token and send email
        token = user.generate_setup_token()
        send_welcome_email.delay(str(user.id), str(token))

        ActivityLog.objects.create(
            user=user, action='Account Created', description='Account created via Gumroad webhook', icon='🎉'
        )

    log.status = WebhookLog.STATUS_SUCCESS


def _handle_refund(email: str, sale_id: str, log: WebhookLog):
    try:
        user = User.objects.get(email=email)
        user.status = User.STATUS_SUSPENDED
        user.save()
        ActivityLog.objects.create(
            user=user, action='Refund', description=f'Subscription refunded: {sale_id}', icon='💸'
        )
        log.status = WebhookLog.STATUS_SUCCESS
    except User.DoesNotExist:
        log.status = WebhookLog.STATUS_FAILED
        log.error_message = f'User not found: {email}'


def _handle_cancellation(email: str, log: WebhookLog):
    try:
        user = User.objects.get(email=email)
        user.status = User.STATUS_INACTIVE
        user.save()
        ActivityLog.objects.create(
            user=user, action='Cancelled', description='Subscription cancelled', icon='❌'
        )
        log.status = WebhookLog.STATUS_SUCCESS
    except User.DoesNotExist:
        log.status = WebhookLog.STATUS_FAILED
        log.error_message = f'User not found: {email}'


def _handle_reactivation(email: str, log: WebhookLog):
    try:
        user = User.objects.get(email=email)
        user.status = User.STATUS_ACTIVE
        user.subscription_end = timezone.now() + timezone.timedelta(days=30)
        user.save()
        ActivityLog.objects.create(
            user=user, action='Reactivated', description='Subscription restarted', icon='✅'
        )
        log.status = WebhookLog.STATUS_SUCCESS
    except User.DoesNotExist:
        log.status = WebhookLog.STATUS_FAILED
        log.error_message = f'User not found: {email}'
