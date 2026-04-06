from celery import shared_task

from core.models import Organization
from ai_modules.sie.services.stakeholder_analyzer import StakeholderAnalyzer


@shared_task(bind=True, max_retries=3, name='ai_modules.sie.tasks.analyze_stakeholders_periodic')
def analyze_stakeholders_periodic(self):
    """Ejecuta el análisis de stakeholders por organización activa."""
    try:
        analyzed = 0
        with_findings = 0

        organization_ids = list(Organization.objects.values_list('id', flat=True))
        for organization_id in organization_ids:
            analyzer = StakeholderAnalyzer()
            result = analyzer.process({'organization_id': organization_id})
            if result.get('status') != 'completed':
                continue

            analyzed += result.get('stakeholders_analyzed', 0)
            with_findings += len(result.get('critical_stakeholders', []))

        return {
            'status': 'completed',
            'organizations_processed': len(organization_ids),
            'stakeholders_analyzed': analyzed,
            'critical_stakeholders_detected': with_findings,
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=300)


# Mantiene registradas las tareas ya existentes del módulo.
from .stakeholder_tasks import *  # noqa: F401,F403
