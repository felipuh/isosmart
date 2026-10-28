import logging
from typing import Iterable, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError
from django.db import transaction
from django.utils import timezone

from authentication.models import UserProfile
from core.models import NotificationDelivery, Organization, OrganizationSettings

logger = logging.getLogger(__name__)


def resolve_notification_recipients(
    organization: Organization,
    *,
    extra_emails: Optional[Iterable[str]] = None,
    users: Optional[Iterable] = None,
) -> list[str]:
    recipients = set()

    if getattr(organization, 'email', None):
        recipients.add(organization.email)

    org_settings = OrganizationSettings.objects.filter(organization=organization).first()
    if org_settings and org_settings.notification_email:
        recipients.add(org_settings.notification_email)

    for email in extra_emails or []:
        if email:
            recipients.add(email)

    for user in users or []:
        if not user or not getattr(user, 'email', ''):
            continue

        profile = UserProfile.objects.filter(user=user, organization=organization, is_active=True).first()
        if profile and profile.notifications_enabled and profile.email_notifications:
            recipients.add(user.email)

    return sorted(email.strip().lower() for email in recipients if email)


def send_email_notification(
    *,
    organization: Organization,
    event_type: str,
    event_key: str,
    subject: str,
    message: str,
    metadata: Optional[dict] = None,
    extra_emails: Optional[Iterable[str]] = None,
    users: Optional[Iterable] = None,
    fail_silently: bool = True,
):
    delivery = NotificationDelivery(
        organization=organization,
        event_type=event_type,
        channel='email',
        event_key=event_key,
        subject=subject,
        body=message,
        metadata=metadata or {},
    )

    recipients = resolve_notification_recipients(
        organization,
        extra_emails=extra_emails,
        users=users,
    )
    delivery.recipients = recipients

    try:
        with transaction.atomic():
            delivery.save(force_insert=True)
    except IntegrityError:
        return NotificationDelivery.objects.get(event_key=event_key)

    if not recipients:
        delivery.status = 'skipped'
        delivery.error_message = 'No notification recipients configured.'
        delivery.save(update_fields=['recipients', 'status', 'error_message', 'updated_at'])
        return delivery

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@isosmart.local')

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipients,
            fail_silently=False,
        )
        delivery.status = 'sent'
        delivery.sent_at = timezone.now()
        delivery.save(update_fields=['recipients', 'status', 'sent_at', 'updated_at'])
        return delivery
    except Exception as exc:
        logger.exception('Notification email failed for event %s', event_key)
        delivery.status = 'failed'
        delivery.error_message = str(exc)
        delivery.save(update_fields=['recipients', 'status', 'error_message', 'updated_at'])
        if fail_silently:
            return delivery
        raise