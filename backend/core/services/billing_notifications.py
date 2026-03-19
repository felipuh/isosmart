import logging
from typing import Optional

from core.models import AuditLog, OrganizationSettings
from core.services.notifications import send_email_notification

logger = logging.getLogger(__name__)


STATUS_LABELS = {
    'active': 'Activa',
    'past_due': 'Pendiente de pago',
    'suspended': 'Suspendida',
    'cancelled': 'Cancelada',
}


PAYMENT_STATUS_LABELS = {
    'pending': 'Pendiente',
    'confirmed': 'Confirmado',
    'rejected': 'Rechazado',
}


def _billing_recipients(subscription):
    recipients = set()
    if subscription.payer_email:
        recipients.add(subscription.payer_email)

    org = subscription.organization
    if getattr(org, 'email', None):
        recipients.add(org.email)

    org_settings = OrganizationSettings.objects.filter(organization=org).first()
    if org_settings and org_settings.notification_email:
        recipients.add(org_settings.notification_email)

    return sorted(email for email in recipients if email)


def _send_billing_email(subscription, subject: str, message: str):
    return send_email_notification(
        organization=subscription.organization,
        event_type='billing_due_reminder',
        event_key=f'billing:generic:{subscription.id}:{hash(subject + message)}',
        subject=subject,
        message=message,
        extra_emails=_billing_recipients(subscription),
        metadata={'subscription_id': subscription.id},
    )


def log_billing_event(
    organization,
    user,
    action: str,
    description: str,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: str = '',
):
    try:
        AuditLog.objects.create(
            organization=organization,
            user=user,
            action=action,
            module='billing',
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_values or {},
            new_values=new_values or {},
        )
    except Exception:
        logger.exception('No se pudo registrar evento de auditoría billing.')


def notify_payment_registered(payment):
    subscription = payment.subscription
    subject = f"[ISO Smart] Pago registrado - Org {subscription.organization.name}"
    message = (
        f"Se registró un pago en estado {PAYMENT_STATUS_LABELS.get(payment.status, payment.status)}.\n"
        f"Organización: {subscription.organization.name}\n"
        f"Monto: {payment.amount} {payment.currency}\n"
        f"Método: {payment.payment_method}\n"
        f"Referencia: {payment.reference or '-'}\n"
        f"Vence: {payment.due_date or 'N/A'}"
    )
    send_email_notification(
        organization=subscription.organization,
        event_type='billing_payment_registered',
        event_key=f'billing:payment_registered:{payment.id}:{payment.status}',
        subject=subject,
        message=message,
        extra_emails=_billing_recipients(subscription),
        metadata={'payment_id': payment.id, 'subscription_id': subscription.id},
    )


def notify_payment_confirmed(payment):
    subscription = payment.subscription
    subject = f"[ISO Smart] Pago confirmado - Org {subscription.organization.name}"
    message = (
        f"Se confirmó un pago de suscripción.\n"
        f"Organización: {subscription.organization.name}\n"
        f"Monto: {payment.amount} {payment.currency}\n"
        f"Método: {payment.payment_method}\n"
        f"Fecha de confirmación: {payment.paid_at or 'N/A'}"
    )
    send_email_notification(
        organization=subscription.organization,
        event_type='billing_payment_confirmed',
        event_key=f'billing:payment_confirmed:{payment.id}:{payment.status}',
        subject=subject,
        message=message,
        extra_emails=_billing_recipients(subscription),
        metadata={'payment_id': payment.id, 'subscription_id': subscription.id},
    )


def notify_payment_rejected(payment):
    subscription = payment.subscription
    subject = f"[ISO Smart] Pago rechazado - Org {subscription.organization.name}"
    message = (
        f"Un pago fue rechazado.\n"
        f"Organización: {subscription.organization.name}\n"
        f"Monto: {payment.amount} {payment.currency}\n"
        f"Referencia: {payment.reference or '-'}\n"
        f"Motivo: {payment.rejection_reason or 'No especificado'}"
    )
    send_email_notification(
        organization=subscription.organization,
        event_type='billing_payment_rejected',
        event_key=f'billing:payment_rejected:{payment.id}:{payment.status}',
        subject=subject,
        message=message,
        extra_emails=_billing_recipients(subscription),
        metadata={'payment_id': payment.id, 'subscription_id': subscription.id},
    )


def notify_subscription_status_change(subscription, previous_status: str, source: str = 'automatic'):
    if previous_status == subscription.status:
        return

    subject = f"[ISO Smart] Cambio de estado de facturación - Org {subscription.organization.name}"
    message = (
        f"Se actualizó el estado de facturación.\n"
        f"Organización: {subscription.organization.name}\n"
        f"Estado anterior: {STATUS_LABELS.get(previous_status, previous_status)}\n"
        f"Estado actual: {STATUS_LABELS.get(subscription.status, subscription.status)}\n"
        f"Origen: {source}\n"
        f"Próximo cobro: {subscription.next_due_date or 'N/A'}"
    )
    send_email_notification(
        organization=subscription.organization,
        event_type='billing_status_changed',
        event_key=f'billing:status_changed:{subscription.id}:{previous_status}:{subscription.status}:{source}',
        subject=subject,
        message=message,
        extra_emails=_billing_recipients(subscription),
        metadata={'subscription_id': subscription.id, 'previous_status': previous_status, 'source': source},
    )


def notify_due_reminder(subscription, days_to_due: int):
    if days_to_due not in {3, 0, -1}:
        return

    subject = f"[ISO Smart] Recordatorio de cobro - Org {subscription.organization.name}"
    if days_to_due == 3:
        status_line = 'Tu suscripción vence en 3 días.'
    elif days_to_due == 0:
        status_line = 'Tu suscripción vence hoy.'
    else:
        status_line = 'Tu suscripción está vencida desde ayer.'

    message = (
        f"{status_line}\n"
        f"Organización: {subscription.organization.name}\n"
        f"Monto mensual: {subscription.monthly_price} {subscription.currency}\n"
        f"Fecha de cobro: {subscription.next_due_date or 'N/A'}\n"
        f"Días de gracia: {subscription.grace_days}"
    )
    send_email_notification(
        organization=subscription.organization,
        event_type='billing_due_reminder',
        event_key=f'billing:due_reminder:{subscription.id}:{subscription.next_due_date}:{days_to_due}',
        subject=subject,
        message=message,
        extra_emails=_billing_recipients(subscription),
        metadata={'subscription_id': subscription.id, 'days_to_due': days_to_due},
    )
