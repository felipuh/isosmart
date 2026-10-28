from datetime import date

from django.utils import timezone

from improvement.models import Nonconformity as ImprovementNonconformity, ContinualImprovement


def _map_finding_status_to_nc(status):
    mapping = {
        'open': 'open',
        'in_progress': 'analysis',
        'resolved': 'verification',
        'verified': 'closed',
        'closed': 'closed',
    }
    return mapping.get(status, 'open')


def _map_finding_type_to_severity(finding_type):
    if finding_type == 'nc_major':
        return 'critical'
    if finding_type == 'nc_minor':
        return 'major'
    return 'minor'


def sync_finding_to_improvement_nc(finding):
    """Sincroniza hallazgos de auditoría 9.2 a no conformidades de mejora 10.2."""
    if finding.finding_type not in {'nc_major', 'nc_minor'}:
        return None

    audit = finding.audit
    nc_number = f"AUD-{finding.finding_number}"

    defaults = {
        'organization_name': audit.organization_name,
        'title': f'Hallazgo de auditoría {finding.finding_number}',
        'description': finding.description,
        'source': 'internal_audit',
        'detection_date': finding.created_at.date() if finding.created_at else timezone.now().date(),
        'severity': _map_finding_type_to_severity(finding.finding_type),
        'affected_process': f'Auditoría {audit.audit_code}',
        'iso_clause_reference': finding.clause_reference,
        'impact_description': finding.evidence,
        'immediate_action_taken': finding.immediate_action or '',
        'status': _map_finding_status_to_nc(finding.status),
        'target_closure_date': finding.due_date,
        'actual_closure_date': finding.completion_date,
    }

    obj, _ = ImprovementNonconformity.objects.update_or_create(
        organization_id=finding.organization_id,
        nc_number=nc_number,
        defaults=defaults,
    )
    return obj


def sync_operations_nc_to_improvement_nc(operations_nc):
    """Sincroniza no conformidades de operaciones 8.7 a mejora 10.2."""
    severity_map = {
        'critical': 'critical',
        'major': 'major',
        'minor': 'minor',
    }
    status_map = {
        'identified': 'open',
        'under_review': 'analysis',
        'disposition_pending': 'action_plan',
        'treated': 'verification',
        'closed': 'closed',
    }

    nc_number = f"OPS-{operations_nc.nc_number}"

    defaults = {
        'organization_name': operations_nc.organization_name,
        'title': f'NC Operaciones {operations_nc.nc_number}: {operations_nc.title}',
        'description': operations_nc.description,
        'source': 'process_monitoring',
        'detection_date': operations_nc.detection_date,
        'severity': severity_map.get(operations_nc.severity, 'minor'),
        'affected_process': operations_nc.affected_product_service,
        'iso_clause_reference': '8.7',
        'impact_description': f'Etapa: {operations_nc.detection_stage}. Tipo: {operations_nc.nc_type}.',
        'status': status_map.get(operations_nc.status, 'open'),
    }

    obj, _ = ImprovementNonconformity.objects.update_or_create(
        organization_id=operations_nc.organization_id,
        nc_number=nc_number,
        defaults=defaults,
    )
    return obj


def sync_management_review_to_continual_improvement(review):
    """Sincroniza revisión por dirección 9.3 a mejora continua 10.3."""
    opportunities_text = (review.improvement_opportunities or '').strip()
    decisions_text = (review.improvement_decisions or '').strip()

    if not opportunities_text and not decisions_text:
        return None

    proposed_improvement = decisions_text or opportunities_text
    current_situation = review.performance_results or review.process_performance or 'Resultados de revisión por dirección'

    initiative_number = f"MR-{review.review_code}"

    defaults = {
        'organization_name': review.organization_name,
        'title': f'Iniciativa derivada de revisión {review.review_code}',
        'description': f'Revisión por la dirección: {review.title}',
        'improvement_type': 'system',
        'current_situation': current_situation,
        'proposed_improvement': proposed_improvement,
        'expected_benefits': opportunities_text or 'Mejorar desempeño y eficacia del SGC',
        'alignment_with_objectives': review.qms_changes or '',
        'success_criteria': 'Ejecución de acciones acordadas y mejora de indicadores',
        'priority': 'high' if review.status == 'completed' else 'medium',
        'proposed_date': review.actual_date or review.scheduled_date or date.today(),
        'status': 'approved' if review.status == 'completed' else 'proposed',
        'implementation_plan': review.action_items or '',
        'risks_and_mitigation': review.resource_needs or '',
    }

    obj, _ = ContinualImprovement.objects.update_or_create(
        organization_id=review.organization_id,
        initiative_number=initiative_number,
        defaults=defaults,
    )
    return obj
