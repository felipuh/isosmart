"""
Tareas asíncronas para Stakeholder Intelligence Engine (SIE)
Celery Tasks
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='sie.analyze_stakeholders')
def analyze_stakeholders_task():
    """
    Tarea asíncrona para ejecutar análisis completo de stakeholders
    Se puede programar para ejecutarse periódicamente (ej: semanalmente)
    """
    from ai_modules.sie.services.stakeholder_analyzer import StakeholderAnalyzer
    
    logger.info("Iniciando análisis de stakeholders...")
    
    try:
        analyzer = StakeholderAnalyzer()
        result = analyzer.process()
        
        logger.info(
            f"Análisis completado: {result.get('stakeholders_analyzed', 0)} stakeholders analizados"
        )
        
        return {
            'status': 'success',
            'stakeholders_analyzed': result.get('stakeholders_analyzed', 0),
            'critical_count': len(result.get('critical_stakeholders', [])),
            'changes_detected': len(result.get('changes_detected', []))
        }
        
    except Exception as e:
        logger.error(f"Error en análisis de stakeholders: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='sie.detect_expectation_changes')
def detect_expectation_changes_task():
    """
    Tarea para detectar cambios en expectativas
    Se ejecuta diariamente
    """
    from ai_modules.sie.services.stakeholder_analyzer import StakeholderAnalyzer
    from ai_modules.sie.models.stakeholder import StakeholderProfile, StakeholderChangeLog
    
    logger.info("Detectando cambios en expectativas...")
    
    try:
        analyzer = StakeholderAnalyzer()
        historical_data = analyzer._load_historical_data()
        changes = analyzer.engine.detect_expectation_changes(historical_data)
        
        # Registrar cambios
        analyzer._log_changes(changes)
        
        logger.info(f"{len(changes)} cambios detectados")
        
        return {
            'status': 'success',
            'changes_detected': len(changes),
            'high_severity': len([c for c in changes if c['severity'] == 'alto'])
        }
        
    except Exception as e:
        logger.error(f"Error detectando cambios: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='sie.update_network_metrics')
def update_network_metrics_task():
    """
    Actualiza métricas de red para todos los stakeholders
    Se ejecuta semanalmente
    """
    from ai_modules.sie.services.stakeholder_analyzer import StakeholderAnalyzer
    
    logger.info("Actualizando métricas de red...")
    
    try:
        analyzer = StakeholderAnalyzer()
        stakeholders = analyzer._load_stakeholders()
        
        if len(stakeholders) == 0:
            return {'status': 'warning', 'message': 'No hay stakeholders'}
        
        # Construir red
        analyzer.engine.build_stakeholder_network(stakeholders)
        
        # Calcular métricas
        metrics = analyzer.engine.calculate_influence_metrics()
        
        # Actualizar en BD
        analyzer._update_influence_scores(metrics)
        
        logger.info(f"Métricas actualizadas para {len(metrics)} stakeholders")
        
        return {
            'status': 'success',
            'stakeholders_updated': len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Error actualizando métricas: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='sie.send_critical_alerts')
def send_critical_alerts_task():
    """
    Envía alertas para cambios críticos detectados
    Se ejecuta cada 6 horas
    """
    from ai_modules.sie.models.stakeholder import StakeholderChangeLog
    from core.models import Organization, OrganizationSettings
    from core.services.notifications import send_email_notification
    
    logger.info("Verificando alertas críticas...")
    
    try:
        # Buscar cambios críticos de las últimas 6 horas sin alerta enviada
        six_hours_ago = timezone.now() - timedelta(hours=6)
        critical_changes = StakeholderChangeLog.objects.filter(
            change_type__icontains='alto',
            detected_at__gte=six_hours_ago,
            alert_sent=False
        )
        
        if critical_changes.count() == 0:
            return {'status': 'success', 'alerts_sent': 0}
        
        alerts_sent = 0

        for change in critical_changes.select_related('stakeholder'):
            organization = Organization.objects.filter(id=change.stakeholder.organization_id).first()
            if not organization:
                continue
            org_settings = OrganizationSettings.objects.filter(organization=organization).first()
            if org_settings and not org_settings.notify_stakeholder_change:
                continue

            subject = f"[ISO Smart] Cambio crítico de stakeholder - {organization.name}"
            message = (
                'Se detectó un cambio crítico en stakeholders.\n'
                f'Organización: {organization.name}\n'
                f'Stakeholder: {change.stakeholder.name}\n'
                f'Tipo de cambio: {change.change_type}\n'
                f'Fecha de detección: {change.detected_at.isoformat()}\n'
                f'Similitud detectada: {change.similarity_score}'
            )

            delivery = send_email_notification(
                organization=organization,
                event_type='stakeholder_change',
                event_key=f'stakeholder_change:{change.id}',
                subject=subject,
                message=message,
                metadata={
                    'change_log_id': change.id,
                    'stakeholder_id': change.stakeholder_id,
                    'change_type': change.change_type,
                },
            )

            if delivery.status in {'sent', 'skipped'}:
                change.alert_sent = True
                change.save(update_fields=['alert_sent'])
                alerts_sent += 1

        logger.info(f"{alerts_sent} alertas enviadas")
        
        return {
            'status': 'success',
            'alerts_sent': alerts_sent
        }
        
    except Exception as e:
        logger.error(f"Error enviando alertas: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }


@shared_task(name='sie.cleanup_old_logs')
def cleanup_old_logs_task():
    """
    Limpia logs antiguos (mayores a 1 año)
    Se ejecuta mensualmente
    """
    from ai_modules.sie.models.stakeholder import StakeholderChangeLog
    
    logger.info("Limpiando logs antiguos...")
    
    try:
        one_year_ago = timezone.now() - timedelta(days=365)
        old_logs = StakeholderChangeLog.objects.filter(
            detected_at__lt=one_year_ago
        )
        
        count = old_logs.count()
        old_logs.delete()
        
        logger.info(f"{count} logs antiguos eliminados")
        
        return {
            'status': 'success',
            'logs_deleted': count
        }
        
    except Exception as e:
        logger.error(f"Error limpiando logs: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e)
        }
