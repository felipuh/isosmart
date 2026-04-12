"""AI services for ISO 9001 clause 8 operations workflows."""

from ai_modules.common.base import AIModuleBase


class OperationsAIService(AIModuleBase):
    def __init__(self):
        super().__init__('operations')

    def process(self, data):
        operation = (data or {}).get('operation', '')
        handlers = {
            'cockpit_summary': self.cockpit_summary,
            'requirement_validation': self.requirement_validation,
            'provider_risk_scoring': self.provider_risk_scoring,
            'release_recommendation': self.release_recommendation,
            'root_cause_suggestions': self.root_cause_suggestions,
        }
        handler = handlers.get(operation)
        if not handler:
            return {'status': 'error', 'message': f'Operacion no soportada: {operation}'}
        return handler(data or {})

    def cockpit_summary(self, data):
        kpis = data.get('kpis') or {}
        nonconformities = (kpis.get('nonconformities') or {}).get('critical', 0)
        pending_releases = (kpis.get('releases') or {}).get('pending', 0)
        pending_requirements = (kpis.get('requirements') or {}).get('pending_review', 0)

        risk_level = 'low'
        if nonconformities > 0 or pending_releases > 5:
            risk_level = 'high'
        elif pending_requirements > 3:
            risk_level = 'medium'

        alerts = []
        if nonconformities > 0:
            alerts.append('Existen no conformidades criticas que impactan la continuidad operacional.')
        if pending_releases > 0:
            alerts.append('Hay liberaciones pendientes que requieren aprobacion formal de calidad.')
        if pending_requirements > 0:
            alerts.append('Quedan requisitos del cliente sin revision documentada.')

        return {
            'status': 'cockpit_ready',
            'risk_level': risk_level,
            'alerts': alerts,
            'recommended_focus': [
                'Priorizar cierre de no conformidades con impacto al cliente.',
                'Asegurar verificacion y criterios antes de autorizar liberaciones.',
                'Confirmar requisitos con cliente y evidencias de revision.',
            ],
        }

    def requirement_validation(self, data):
        requirements = data.get('requirements') or []
        not_reviewed = [r for r in requirements if not r.get('is_reviewed')]
        not_confirmed = [r for r in requirements if r.get('is_reviewed') and not r.get('is_confirmed')]
        not_feasible = [r for r in requirements if not r.get('can_meet_requirement')]

        return {
            'status': 'analysis_ready',
            'summary': {
                'total': len(requirements),
                'pending_review': len(not_reviewed),
                'pending_confirmation': len(not_confirmed),
                'not_feasible': len(not_feasible),
            },
            'recommendations': [
                'Estandarizar checklist de revision tecnica/comercial antes de confirmar.',
                'Escalar requisitos no factibles con alternativa de alcance o plazo.',
                'Cerrar trazabilidad de confirmacion con evidencia contractual o correo aprobado.',
            ],
        }

    def provider_risk_scoring(self, data):
        providers = data.get('providers') or []
        ranked = []
        for provider in providers:
            score = 0
            if provider.get('classification') == 'not_approved':
                score += 50
            elif provider.get('classification') == 'conditional':
                score += 25

            eval_score = provider.get('evaluation_score')
            if eval_score is None:
                score += 20
            elif eval_score < 60:
                score += 25
            elif eval_score < 75:
                score += 10

            perf = provider.get('performance_rating')
            if perf is not None and perf <= 2:
                score += 20

            ranked.append({
                'provider_id': provider.get('id'),
                'provider_name': provider.get('provider_name'),
                'risk_score': min(score, 100),
                'risk_level': 'high' if score >= 60 else 'medium' if score >= 30 else 'low',
            })

        ranked.sort(key=lambda item: item['risk_score'], reverse=True)
        return {
            'status': 'scoring_ready',
            'providers': ranked,
            'top_risks': ranked[:5],
        }

    def release_recommendation(self, data):
        releases = data.get('releases') or []
        recommendations = []
        for item in releases:
            issues = []
            if not item.get('verification_performed'):
                issues.append('verificacion no ejecutada')
            if not item.get('acceptance_criteria_met'):
                issues.append('criterios de aceptacion no cumplidos')

            decision = 'approve'
            if issues:
                decision = 'hold'

            recommendations.append({
                'release_id': item.get('id'),
                'release_code': item.get('release_code'),
                'decision': decision,
                'reason': ', '.join(issues) if issues else 'Listo para liberacion con evidencia minima completa.',
            })

        return {
            'status': 'recommendation_ready',
            'recommendations': recommendations,
        }

    def root_cause_suggestions(self, data):
        nonconformities = data.get('nonconformities') or []
        suggestions = []
        cause_by_type = {
            'process': 'Desviacion del estandar operativo y control insuficiente del proceso.',
            'product': 'Variabilidad de insumos/especificaciones y controles de verificacion incompletos.',
            'service': 'Deficiencia en criterios de servicio y validacion de salida antes de entrega.',
            'documentation': 'Instrucciones desactualizadas o no comunicadas al personal operativo.',
        }

        for nc in nonconformities[:10]:
            nc_type = nc.get('nc_type') or 'process'
            suggestions.append({
                'nc_id': nc.get('id'),
                'nc_number': nc.get('nc_number'),
                'suggested_root_cause': cause_by_type.get(nc_type, cause_by_type['process']),
                'next_step': 'Aplicar 5 Whys con evidencia, validar causa y definir accion correctiva con responsable y fecha.',
            })

        return {
            'status': 'suggestions_ready',
            'items': suggestions,
        }
