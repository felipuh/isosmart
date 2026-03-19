from celery import shared_task
import logging
import time
from datetime import timedelta

from django.utils import timezone
from ai_modules.sie.tasks.stakeholder_tasks import send_critical_alerts_task
from core.models import BillingSubscription
from core.services.billing_notifications import (
    log_billing_event,
    notify_subscription_status_change,
    notify_due_reminder,
)
from core.services.notifications import send_email_notification

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


@shared_task
def evaluate_operational_notifications_task():
    """Evalúa riesgos, objetivos y stakeholders para disparar notificaciones operativas."""
    from core.models import Organization, OrganizationSettings
    from planning.models import ObjectiveAction, QualityObjective, RiskOpportunity

    today = timezone.now().date()
    deadline_limit = today + timedelta(days=7)
    summary = {
        'risk_notifications': 0,
        'objective_notifications': 0,
        'stakeholder_alerts': 0,
    }

    org_settings_map = {
        item.organization_id: item
        for item in OrganizationSettings.objects.select_related('organization').all()
    }

    risks = RiskOpportunity.objects.select_related('owner').filter(
        item_type='risk',
        is_active=True,
        status__in=['identified', 'in_treatment', 'monitored'],
        risk_level__gte=15,
    )
    for risk in risks:
        org = Organization.objects.filter(id=risk.organization_id).first()
        if not org:
            continue

        settings = org_settings_map.get(org.id)
        is_critical = (risk.risk_level or 0) >= 20
        if settings:
            if is_critical and not settings.notify_risk_critical:
                continue
            if not is_critical and not settings.notify_risk_high:
                continue

        event_type = 'risk_critical' if is_critical else 'risk_high'
        severity_label = 'Crítico' if is_critical else 'Alto'
        subject = f"[ISO Smart] Riesgo {severity_label.lower()} - {org.name}"
        message = (
            f"Se detectó un riesgo {severity_label.lower()} pendiente de seguimiento.\n"
            f"Organización: {org.name}\n"
            f"Código: {risk.code}\n"
            f"Título: {risk.title}\n"
            f"Nivel de riesgo: {risk.risk_level}\n"
            f"Estado: {risk.get_status_display()}\n"
            f"Tratamiento: {risk.get_treatment_display() if risk.treatment else 'Sin definir'}"
        )
        delivery = send_email_notification(
            organization=org,
            event_type=event_type,
            event_key=f'risk:{risk.id}:{risk.risk_level}:{risk.status}:{risk.updated_at.isoformat()}',
            subject=subject,
            message=message,
            users=[risk.owner] if risk.owner else None,
            metadata={'risk_id': risk.id, 'risk_level': risk.risk_level, 'status': risk.status},
        )
        if delivery.status == 'sent':
            summary['risk_notifications'] += 1

    objectives = QualityObjective.objects.select_related('owner').filter(
        is_active=True,
        status__in=['approved', 'in_progress'],
        target_date__lte=deadline_limit,
    )
    for objective in objectives:
        org = Organization.objects.filter(id=objective.organization_id).first()
        if not org:
            continue

        settings = org_settings_map.get(org.id)
        if settings and not settings.notify_objective_deadline:
            continue

        days_remaining = (objective.target_date - today).days
        subject = f"[ISO Smart] Objetivo próximo a vencer - {org.name}"
        message = (
            'Un objetivo de calidad requiere atención por vencimiento cercano.\n'
            f'Organización: {org.name}\n'
            f'Código: {objective.code}\n'
            f'Título: {objective.title}\n'
            f'Fecha meta: {objective.target_date}\n'
            f'Días restantes: {days_remaining}\n'
            f'Avance: {objective.progress_percentage}%'
        )
        delivery = send_email_notification(
            organization=org,
            event_type='objective_deadline',
            event_key=f'objective:{objective.id}:{objective.target_date}:{objective.updated_at.isoformat()}',
            subject=subject,
            message=message,
            users=[objective.owner] if objective.owner else None,
            metadata={'objective_id': objective.id, 'target_date': objective.target_date.isoformat()},
        )
        if delivery.status == 'sent':
            summary['objective_notifications'] += 1

    actions = ObjectiveAction.objects.select_related('responsible', 'objective').filter(
        status__in=['planned', 'in_progress', 'delayed'],
        due_date__lte=deadline_limit,
    )
    for action in actions:
        org = Organization.objects.filter(id=action.organization_id).first()
        if not org:
            continue

        settings = org_settings_map.get(org.id)
        if settings and not settings.notify_objective_deadline:
            continue

        days_remaining = (action.due_date - today).days
        subject = f"[ISO Smart] Acción próxima a vencer - {org.name}"
        message = (
            'Una acción asociada a objetivo requiere atención por vencimiento cercano.\n'
            f'Organización: {org.name}\n'
            f'Objetivo: {action.objective.code} - {action.objective.title}\n'
            f'Acción: {action.action_number}\n'
            f'Descripción: {action.description}\n'
            f'Fecha límite: {action.due_date}\n'
            f'Días restantes: {days_remaining}\n'
            f'Estado: {action.get_status_display()}'
        )
        delivery = send_email_notification(
            organization=org,
            event_type='objective_deadline',
            event_key=f'objective_action:{action.id}:{action.due_date}:{action.updated_at.isoformat()}',
            subject=subject,
            message=message,
            users=[action.responsible] if action.responsible else None,
            metadata={'objective_action_id': action.id, 'due_date': action.due_date.isoformat()},
        )
        if delivery.status == 'sent':
            summary['objective_notifications'] += 1

    stakeholder_result = send_critical_alerts_task()
    summary['stakeholder_alerts'] = stakeholder_result.get('alerts_sent', 0)
    logger.info('Evaluación automática de notificaciones operativas completada: %s', summary)
    return summary