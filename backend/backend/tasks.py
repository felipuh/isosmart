from celery import shared_task
import logging
import time
from django.utils import timezone
from core.models import BillingSubscription
from core.services.billing_notifications import (
    log_billing_event,
    notify_subscription_status_change,
    notify_due_reminder,
)

logger = logging.getLogger(__name__)

@shared_task
def add(x, y):
    """Tarea simple de suma"""
    result = x + y
    logger.info(f"Suma ejecutada: {x} + {y} = {result}")
    return result

@shared_task
def test_task():
    """Tarea de prueba para verificar Celery"""
    logger.info("✓ Tarea de prueba ejecutada correctamente")
    time.sleep(2)  # Simular trabajo
    return "Celery funciona correctamente"

@shared_task
def multiply(x, y):
    """Tarea de multiplicación"""
    result = x * y
    logger.info(f"Multiplicación: {x} * {y} = {result}")
    return result


@shared_task
def evaluate_billing_statuses_task():
    """Evalúa automáticamente el estado de facturación de todas las organizaciones"""
    today = timezone.now().date()
    subscriptions = BillingSubscription.objects.select_related('organization').all()

    summary = {
        'processed': 0,
        'updated': 0,
        'active': 0,
        'past_due': 0,
        'suspended': 0,
        'cancelled': 0,
    }

    for subscription in subscriptions:
        summary['processed'] += 1
        previous_status = subscription.status

        subscription.evaluate_status(today=today)

        update_fields = ['status', 'past_due_since', 'suspended_at', 'updated_at']
        org_active_target = subscription.status not in ['suspended', 'cancelled']
        if subscription.organization.is_active != org_active_target:
            subscription.organization.is_active = org_active_target
            subscription.organization.save(update_fields=['is_active', 'updated_at'])

        if previous_status != subscription.status:
            summary['updated'] += 1
            notify_subscription_status_change(subscription, previous_status, source='celery_daily')
            log_billing_event(
                organization=subscription.organization,
                user=None,
                action='update',
                description='Cambio automático de estado de facturación por tarea diaria.',
                old_values={'status': previous_status},
                new_values={'status': subscription.status},
            )

        if subscription.next_due_date and subscription.status != 'cancelled':
            days_to_due = (subscription.next_due_date - today).days
            notify_due_reminder(subscription, days_to_due)

        subscription.save(update_fields=update_fields)

        if subscription.status == 'active':
            summary['active'] += 1
        elif subscription.status == 'past_due':
            summary['past_due'] += 1
        elif subscription.status == 'suspended':
            summary['suspended'] += 1
        elif subscription.status == 'cancelled':
            summary['cancelled'] += 1

    logger.info('Evaluación automática de billing completada: %s', summary)
    return summary