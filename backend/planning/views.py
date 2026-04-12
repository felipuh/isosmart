# planning/views.py
"""Views for Planning Module."""

from django.db.models import Count, Q
from django.forms.models import model_to_dict
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from ai_modules.planning.planning_engine import PlanningAIService
from core.organization_scoping import OrganizationScopedViewSetMixin
from .models import (
    ChangeControl,
    ObjectiveAction,
    PlanningAIGovernanceLog,
    PlanningApprovalRecord,
    PlanningVersionRecord,
    QualityObjective,
    RiskOpportunity,
)
from .serializers import (
    ChangeControlSerializer,
    ObjectiveActionSerializer,
    PlanningAIGovernanceLogSerializer,
    PlanningApprovalRecordSerializer,
    PlanningVersionRecordSerializer,
    QualityObjectiveSerializer,
    RiskOpportunitySerializer,
)


def _serialize_value(value):
    if value is None or isinstance(value, (bool, int, float, str, list, dict)):
        return value
    if hasattr(value, 'isoformat'):
        return value.isoformat()
    return str(value)


def _snapshot_instance(instance):
    data = {}
    for field in instance._meta.fields:
        data[field.name] = _serialize_value(getattr(instance, field.attname))
    for field in instance._meta.many_to_many:
        data[field.name] = list(getattr(instance, field.name).values_list('id', flat=True))
    return data


def _record_version(instance, user, entity_type, reason=''):
    last_version = PlanningVersionRecord.objects.filter(
        entity_type=entity_type,
        entity_id=instance.pk,
    ).order_by('-version_number').first()
    version_number = (last_version.version_number + 1) if last_version else 1
    PlanningVersionRecord.objects.create(
        organization_id=getattr(instance, 'organization_id', None) or 0,
        entity_type=entity_type,
        entity_id=instance.pk,
        version_number=version_number,
        snapshot=_snapshot_instance(instance),
        changed_by=user if getattr(user, 'is_authenticated', False) else None,
        change_reason=reason,
    )


def _record_approval(instance, user, workflow_type, title, notes=''):
    snapshot = _snapshot_instance(instance)
    timestamp_iso = getattr(instance, 'approval_date', None)
    if hasattr(timestamp_iso, 'isoformat'):
        timestamp_iso = timestamp_iso.isoformat()
    else:
        timestamp_iso = getattr(instance, 'approved_at', None)
        timestamp_iso = timestamp_iso.isoformat() if hasattr(timestamp_iso, 'isoformat') else ''
    signature = PlanningApprovalRecord.generate_signature(snapshot, user.pk, timestamp_iso)
    return PlanningApprovalRecord.objects.create(
        organization_id=getattr(instance, 'organization_id', None) or 0,
        workflow_type=workflow_type,
        reference_model=f'{instance._meta.app_label}.{instance.__class__.__name__}',
        reference_id=instance.pk,
        title=title,
        approved_by=user,
        digital_signature=signature,
        content_snapshot=snapshot,
        notes=notes,
    )


def _persist_ai_log(data):
    if not data:
        return None
    allowed = {field.name for field in PlanningAIGovernanceLog._meta.fields}
    payload = {key: value for key, value in data.items() if key in allowed}
    return PlanningAIGovernanceLog.objects.create(**payload)


class RiskOpportunityViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Riesgos y Oportunidades."""
    queryset = RiskOpportunity.objects.all()
    serializer_class = RiskOpportunitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'item_type', 'category', 'status', 'context', 'is_active']
    search_fields = ['code', 'title', 'description']
    ordering_fields = ['risk_level', 'opportunity_score', 'created_at', 'review_date']
    ordering = ['-risk_level', '-opportunity_score']

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _record_version(serializer.instance, self.request.user, 'risk_opportunity', 'created')

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _record_version(serializer.instance, self.request.user, 'risk_opportunity', 'updated')

    @action(detail=False, methods=['get'])
    def risks(self, request):
        queryset = self.get_queryset().filter(item_type='risk', is_active=True).order_by('-risk_level')
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=['get'])
    def opportunities(self, request):
        queryset = self.get_queryset().filter(item_type='opportunity', is_active=True).order_by('-opportunity_score')
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=['get'])
    def high_priority(self, request):
        queryset = self.get_queryset().filter(item_type='risk', risk_level__gte=15, is_active=True).order_by('-risk_level')
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=['get'])
    def heatmap(self, request):
        risks = self.get_queryset().filter(item_type='risk', is_active=True)
        matrix = []
        for probability in range(1, 6):
            row = []
            for impact in range(1, 6):
                count = risks.filter(probability=probability, impact=impact).count()
                row.append({'probability': probability, 'impact': impact, 'count': count})
            matrix.append(row)
        return Response({'matrix': matrix, 'total': risks.count()})

    @action(detail=False, methods=['post'], url_path='ai-detect')
    def ai_detect(self, request):
        service = PlanningAIService()
        result = service.detect_risk_from_text({
            'organization_id': self.get_organization_id(),
            'text': request.data.get('text', ''),
            'sources': request.data.get('sources', []),
        })
        _persist_ai_log(result.pop('governance_log_data', {}))
        return Response(result)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        item = self.get_object()
        item.approve(request.user, request.data.get('notes', ''))
        record = _record_approval(item, request.user, 'risk_approval', item.title, request.data.get('notes', ''))
        _record_version(item, request.user, 'risk_opportunity', 'approved')
        return Response({'status': 'Riesgo/Oportunidad aprobado', 'signature': record.digital_signature})

    @action(detail=True, methods=['get'])
    def version_history(self, request, pk=None):
        item = self.get_object()
        records = PlanningVersionRecord.objects.filter(entity_type='risk_opportunity', entity_id=item.pk)
        return Response(PlanningVersionRecordSerializer(records, many=True).data)


class QualityObjectiveViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Objetivos de Calidad."""
    queryset = QualityObjective.objects.all()
    serializer_class = QualityObjectiveSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status', 'alignment', 'is_active']
    search_fields = ['code', 'title', 'description', 'metric']
    ordering_fields = ['target_date', 'progress_percentage', 'created_at']
    ordering = ['-target_date']

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _record_version(serializer.instance, self.request.user, 'quality_objective', 'created')

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _record_version(serializer.instance, self.request.user, 'quality_objective', 'updated')

    @action(detail=False, methods=['get'])
    def active(self, request):
        queryset = self.get_queryset().filter(status='in_progress', is_active=True)
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=['get'])
    def smart_compliant(self, request):
        queryset = self.get_queryset().filter(
            is_specific=True,
            is_measurable=True,
            is_achievable=True,
            is_relevant=True,
            is_time_bound=True,
            is_active=True,
        )
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=['get'])
    def at_risk(self, request):
        from datetime import date, timedelta

        threshold_date = date.today() + timedelta(days=30)
        queryset = self.get_queryset().filter(
            status='in_progress',
            progress_percentage__lt=50,
            target_date__lte=threshold_date,
            is_active=True,
        )
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=False, methods=['post'])
    def validate_smart(self, request):
        service = PlanningAIService()
        return Response(service.validate_smart_objective(request.data))

    @action(detail=False, methods=['post'])
    def ai_generate(self, request):
        service = PlanningAIService()
        result = service.generate_smart_objective({
            'organization_id': self.get_organization_id(),
            **request.data,
        })
        _persist_ai_log(result.pop('governance_log_data', {}))
        return Response(result)

    @action(detail=True, methods=['get'])
    def forecast(self, request, pk=None):
        objective = self.get_object()
        service = PlanningAIService()
        result = service.project_objective_completion(_snapshot_instance(objective))
        objective.forecast_summary = result.get('forecast', {})
        objective.save(update_fields=['forecast_summary'])
        return Response(result)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        objective = self.get_object()
        objective.approve(request.user)
        record = _record_approval(objective, request.user, 'objective_approval', objective.title, request.data.get('notes', ''))
        _record_version(objective, request.user, 'quality_objective', 'approved')
        return Response({'status': 'Objetivo aprobado', 'signature': record.digital_signature})

    @action(detail=True, methods=['get'])
    def version_history(self, request, pk=None):
        objective = self.get_object()
        records = PlanningVersionRecord.objects.filter(entity_type='quality_objective', entity_id=objective.pk)
        return Response(PlanningVersionRecordSerializer(records, many=True).data)


class ObjectiveActionViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Acciones de Objetivos."""
    queryset = ObjectiveAction.objects.all()
    serializer_class = ObjectiveActionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'objective', 'status', 'responsible']
    search_fields = ['description', 'what_will_be_done']
    ordering_fields = ['due_date', 'progress_percentage', 'created_at']
    ordering = ['objective', 'action_number']

    @action(detail=False, methods=['get'])
    def overdue(self, request):
        from datetime import date

        queryset = self.get_queryset().filter(due_date__lt=date.today(), status__in=['planned', 'in_progress'])
        return Response(self.get_serializer(queryset, many=True).data)


class ChangeControlViewSet(OrganizationScopedViewSetMixin, viewsets.ModelViewSet):
    """ViewSet para Control de Cambios."""
    queryset = ChangeControl.objects.all()
    serializer_class = ChangeControlSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'status', 'change_type', 'urgency', 'reason']
    search_fields = ['change_number', 'title', 'description']
    ordering_fields = ['planned_date', 'urgency', 'created_at']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _record_version(serializer.instance, self.request.user, 'change_control', 'created')

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _record_version(serializer.instance, self.request.user, 'change_control', 'updated')

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        change = self.get_object()
        try:
            change.approve(request.user)
        except ValueError as exc:
            raise ValidationError({'impact_assessment': str(exc)})
        record = _record_approval(change, request.user, 'change_approval', change.title, request.data.get('notes', ''))
        _record_version(change, request.user, 'change_control', 'approved')
        return Response({'status': 'Cambio aprobado', 'signature': record.digital_signature})

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        change = self.get_object()
        comments = request.data.get('comments', '')
        change.reject(request.user, comments)
        record = _record_approval(change, request.user, 'change_rejection', change.title, comments)
        _record_version(change, request.user, 'change_control', 'rejected')
        return Response({'status': 'Cambio rechazado', 'signature': record.digital_signature})

    @action(detail=False, methods=['get'])
    def pending_approval(self, request):
        queryset = self.get_queryset().filter(status__in=['submitted', 'under_review']).order_by('urgency', 'planned_date')
        return Response(self.get_serializer(queryset, many=True).data)

    @action(detail=True, methods=['post'])
    def simulate_impact(self, request, pk=None):
        change = self.get_object()
        service = PlanningAIService()
        result = service.simulate_change_impact({
            **_snapshot_instance(change),
            'organization_id': change.organization_id,
            'sources': request.data.get('sources', []),
        })
        _persist_ai_log(result.pop('governance_log_data', {}))
        change.impact_estimated = result.get('impact_estimated', {})
        change.save(update_fields=['impact_estimated'])
        _record_version(change, request.user, 'change_control', 'impact_simulated')
        return Response(result)

    @action(detail=True, methods=['post'])
    def generate_plan(self, request, pk=None):
        change = self.get_object()
        service = PlanningAIService()
        result = service.generate_change_plan(_snapshot_instance(change))
        change.implementation_plan = result.get('implementation_plan', [])
        change.save(update_fields=['implementation_plan'])
        _record_version(change, request.user, 'change_control', 'implementation_plan_generated')
        return Response(result)

    @action(detail=True, methods=['get'])
    def timeline(self, request, pk=None):
        change = self.get_object()
        events = [
            {'event': 'created', 'date': change.created_at, 'label': 'Solicitud creada'},
        ]
        if change.approval_date:
            events.append({'event': 'approved', 'date': change.approval_date, 'label': 'Cambio evaluado'})
        if change.actual_implementation_date:
            events.append({'event': 'implemented', 'date': change.actual_implementation_date, 'label': 'Cambio implementado'})
        if change.verification_date:
            events.append({'event': 'verified', 'date': change.verification_date, 'label': 'Efectividad verificada'})
        return Response({'events': [{'event': e['event'], 'label': e['label'], 'date': _serialize_value(e['date'])} for e in events]})

    @action(detail=True, methods=['get'])
    def version_history(self, request, pk=None):
        change = self.get_object()
        records = PlanningVersionRecord.objects.filter(entity_type='change_control', entity_id=change.pk)
        return Response(PlanningVersionRecordSerializer(records, many=True).data)


class PlanningVersionRecordViewSet(OrganizationScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PlanningVersionRecord.objects.all()
    serializer_class = PlanningVersionRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'entity_type', 'entity_id']
    ordering_fields = ['created_at', 'version_number']
    ordering = ['-created_at']


class PlanningApprovalRecordViewSet(OrganizationScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PlanningApprovalRecord.objects.all()
    serializer_class = PlanningApprovalRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'workflow_type', 'reference_model', 'reference_id']
    ordering_fields = ['approved_at']
    ordering = ['-approved_at']

    @action(detail=True, methods=['get'])
    def verify_signature(self, request, pk=None):
        record = self.get_object()
        expected = PlanningApprovalRecord.generate_signature(record.content_snapshot, record.approved_by_id, record.approved_at.isoformat())
        return Response({'valid': expected == record.digital_signature, 'stored_signature': record.digital_signature, 'computed_signature': expected})


class PlanningAIGovernanceLogViewSet(OrganizationScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = PlanningAIGovernanceLog.objects.all()
    serializer_class = PlanningAIGovernanceLogSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['organization_id', 'operation', 'human_decision']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def decide(self, request, pk=None):
        log = self.get_object()
        decision = request.data.get('decision', '')
        notes = request.data.get('notes', '')
        log.record_human_decision(request.user, decision, notes)
        return Response({'status': 'decision_recorded', 'decision': log.human_decision})

    @action(detail=False, methods=['get'])
    def pending(self, request):
        queryset = self.get_queryset().filter(human_decision='pending')
        return Response(self.get_serializer(queryset, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def planning_cockpit_kpis(request):
    organization_id = getattr(request, 'organization_id', None) or request.query_params.get('organization_id')
    if not organization_id:
        raise ValidationError({'organization_id': 'organization_id requerido'})

    risks = RiskOpportunity.objects.filter(organization_id=organization_id, item_type='risk', is_active=True)
    objectives = QualityObjective.objects.filter(organization_id=organization_id, is_active=True)
    changes = ChangeControl.objects.filter(organization_id=organization_id)

    stats = {
        'risks': {
            'total': risks.count(),
            'high': risks.filter(risk_level__gte=15).count(),
            'approved': risks.filter(approved_at__isnull=False).count(),
        },
        'objectives': {
            'total': objectives.count(),
            'smart': objectives.filter(
                is_specific=True,
                is_measurable=True,
                is_achievable=True,
                is_relevant=True,
                is_time_bound=True,
            ).count(),
            'at_risk': objectives.filter(status='in_progress', progress_percentage__lt=50).count(),
        },
        'changes': {
            'total': changes.count(),
            'pending': changes.filter(status__in=['submitted', 'under_review']).count(),
            'implemented': changes.filter(status__in=['implemented', 'verified', 'closed']).count(),
        },
        'governance': {
            'pending_ai': PlanningAIGovernanceLog.objects.filter(organization_id=organization_id, human_decision='pending').count(),
            'version_records': PlanningVersionRecord.objects.filter(organization_id=organization_id).count(),
            'approval_records': PlanningApprovalRecord.objects.filter(organization_id=organization_id).count(),
        },
    }
    alerts = []
    if stats['risks']['high'] > 0:
        alerts.append({'type': 'warning', 'message': f"{stats['risks']['high']} riesgo(s) alto(s) requieren atención."})
    if stats['objectives']['at_risk'] > 0:
        alerts.append({'type': 'warning', 'message': f"{stats['objectives']['at_risk']} objetivo(s) en riesgo de incumplimiento."})
    if stats['changes']['pending'] > 0:
        alerts.append({'type': 'info', 'message': f"{stats['changes']['pending']} cambio(s) pendientes de aprobación humana."})
    if stats['governance']['pending_ai'] > 0:
        alerts.append({'type': 'info', 'message': f"{stats['governance']['pending_ai']} recomendación(es) IA pendientes de decisión."})

    return Response({'organization_id': int(organization_id), 'kpis': stats, 'alerts': alerts})
