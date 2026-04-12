"""AI services for ISO 9001 clause 6 planning workflows."""

import hashlib
import json
from datetime import date

from ai_modules.common.base import AIModuleBase


MODEL_VERSION = 'planning-v1-heuristic'


def _hash_prompt(prompt):
    return hashlib.sha256(prompt.encode('utf-8')).hexdigest()


class PlanningAIService(AIModuleBase):
    def __init__(self):
        super().__init__('planning')

    def process(self, data):
        operation = (data or {}).get('operation', '')
        handlers = {
            'risk_detection': self.detect_risk_from_text,
            'smart_objective': self.generate_smart_objective,
            'smart_validation': self.validate_smart_objective,
            'objective_projection': self.project_objective_completion,
            'change_simulation': self.simulate_change_impact,
            'change_plan': self.generate_change_plan,
        }
        handler = handlers.get(operation)
        if not handler:
            return {'status': 'error', 'message': f'Operación no soportada: {operation}'}
        return handler(data or {})

    def detect_risk_from_text(self, data):
        text = (data.get('text') or '').strip()
        organization_id = data.get('organization_id')
        if not text:
            return {'status': 'error', 'message': 'Texto requerido'}

        lowered = text.lower()
        category = 'operational'
        if any(token in lowered for token in ['phishing', 'ransomware', 'brecha', 'ciber', 'seguridad']):
            category = 'cyber'
        elif any(token in lowered for token in ['clima', 'inundación', 'temperatura', 'sequía', 'ambiental']):
            category = 'climatic'
        elif any(token in lowered for token in ['costo', 'liquidez', 'precio', 'financ']):
            category = 'financial'

        probability = min(1.0, round(0.35 + (0.1 * sum(1 for token in ['frecuente', 'repetitivo', 'crítico'] if token in lowered)), 2))
        impact = min(1.0, round(0.4 + (0.1 * sum(1 for token in ['cliente', 'parada', 'multa', 'incumplimiento'] if token in lowered)), 2))
        risk_score = probability * impact
        level = 'high' if risk_score >= 0.45 else 'medium' if risk_score >= 0.2 else 'low'
        proposed_actions = self._risk_actions(category, level)
        sources = data.get('sources') or ['input:text']

        prompt = f'risk_detection:{text[:500]}'
        return {
            'status': 'analysis_ready',
            'ai_requires_human_approval': True,
            'risk': {
                'description': text[:500],
                'category': category,
                'probability': probability,
                'impact': impact,
                'level': level,
                'actions': proposed_actions,
                'sources': sources,
            },
            'governance_log_data': {
                'organization_id': organization_id,
                'operation': 'risk_detection',
                'model_version': MODEL_VERSION,
                'prompt_template': 'planning/risk_detection_v1',
                'prompt_hash': _hash_prompt(prompt),
                'response_summary': text[:300],
                'ai_recommendation': {
                    'category': category,
                    'probability': probability,
                    'impact': impact,
                    'level': level,
                    'actions': proposed_actions,
                },
                'data_sources': sources,
                'privacy_check_passed': True,
            },
        }

    def generate_smart_objective(self, data):
        organization_id = data.get('organization_id')
        title = (data.get('title') or '').strip()
        strategy = (data.get('strategy') or '').strip()
        risk_context = data.get('risk_context') or []
        indicator = data.get('indicator') or 'Indicador de desempeño'
        baseline = data.get('baseline') or 0
        target = data.get('target') or max(1, baseline)
        deadline = data.get('deadline') or date.today().isoformat()

        smart = {
            'objective': title or f'Mejorar {indicator.lower()}',
            'indicator': indicator,
            'baseline': baseline,
            'target': target,
            'deadline': deadline,
            'specific': bool(title),
            'measurable': indicator not in ['', None],
            'achievable': float(target) >= float(baseline),
            'relevant': bool(strategy or risk_context),
            'time_bound': bool(deadline),
            'resources': data.get('resources') or 'Equipo responsable + seguimiento mensual',
            'rationale': strategy or 'Objetivo alineado con la mejora continua y riesgos priorizados.',
        }

        prompt = f'smart_objective:{title}:{indicator}:{baseline}:{target}:{deadline}'
        return {
            'status': 'draft_ready',
            'ai_requires_human_approval': True,
            'draft': smart,
            'governance_log_data': {
                'organization_id': organization_id,
                'operation': 'smart_objective',
                'model_version': MODEL_VERSION,
                'prompt_template': 'planning/smart_objective_v1',
                'prompt_hash': _hash_prompt(prompt),
                'response_summary': smart['objective'],
                'ai_recommendation': smart,
                'data_sources': data.get('sources') or ['input:objective'],
                'privacy_check_passed': True,
            },
        }

    def validate_smart_objective(self, data):
        checks = {
            'specific': bool(data.get('title') and len(str(data.get('title')).strip()) >= 10),
            'measurable': bool(data.get('metric') and data.get('target') not in ['', None]),
            'achievable': self._safe_num(data.get('target')) >= self._safe_num(data.get('baseline')),
            'relevant': bool(data.get('alignment')),
            'time_bound': bool(data.get('target_date')),
        }
        issues = []
        if not checks['specific']:
            issues.append('El objetivo necesita una formulación más específica.')
        if not checks['measurable']:
            issues.append('Debe incluir indicador y meta cuantificable.')
        if not checks['achievable']:
            issues.append('La meta es menor a la línea base o no es coherente.')
        if not checks['relevant']:
            issues.append('Debe alinearse con política, estrategia, cliente o mejora.')
        if not checks['time_bound']:
            issues.append('Debe incluir fecha objetivo.')

        return {
            'status': 'validated',
            'passed': all(checks.values()),
            'checks': checks,
            'issues': issues,
        }

    def project_objective_completion(self, data):
        baseline = self._safe_num(data.get('baseline'))
        current = self._safe_num(data.get('current_value'))
        target = self._safe_num(data.get('target'))
        progress = self._safe_num(data.get('progress_percentage'))
        status = 'on_track'
        if progress < 50:
            status = 'at_risk'
        if target and current >= target:
            status = 'likely_achieved'
        projected = {
            'baseline': baseline,
            'current_value': current,
            'target': target,
            'progress_percentage': progress,
            'projected_status': status,
            'recommended_action': 'Escalar seguimiento y revisar recursos' if status == 'at_risk' else 'Mantener ritmo y control mensual',
        }
        return {'status': 'projection_ready', 'forecast': projected}

    def simulate_change_impact(self, data):
        title = (data.get('title') or '').strip()
        reason = data.get('reason') or 'improvement'
        urgency = data.get('urgency') or 'medium'
        affected_areas = self._split_text(data.get('affected_areas'))
        potential_risks = self._split_text(data.get('potential_risks'))
        impact = {
            'operational': 'high' if 'process' in (data.get('change_type') or '') or len(affected_areas) > 2 else 'medium',
            'compliance': 'medium' if reason in ['compliance', 'external_requirement'] else 'low',
            'resources': 'high' if urgency in ['high', 'critical'] else 'medium',
            'timeline_days': 30 if urgency in ['low', 'medium'] else 14,
            'affected_areas_count': len(affected_areas),
            'risk_references': potential_risks,
        }
        prompt = f'change_simulation:{title}:{reason}:{urgency}'
        return {
            'status': 'simulation_ready',
            'ai_requires_human_approval': True,
            'impact_estimated': impact,
            'scenario_summary': f'El cambio "{title}" impacta {len(affected_areas)} área(s) con prioridad {urgency}.',
            'governance_log_data': {
                'organization_id': data.get('organization_id'),
                'operation': 'change_simulation',
                'model_version': MODEL_VERSION,
                'prompt_template': 'planning/change_simulation_v1',
                'prompt_hash': _hash_prompt(prompt),
                'response_summary': title,
                'ai_recommendation': impact,
                'data_sources': data.get('sources') or ['input:change'],
                'privacy_check_passed': True,
            },
        }

    def generate_change_plan(self, data):
        title = data.get('title') or 'Cambio'
        urgency = data.get('urgency') or 'medium'
        plan = [
            {'step': 1, 'title': 'Validar impacto y responsables', 'owner': 'Alta Dirección', 'days': 2},
            {'step': 2, 'title': 'Comunicar el cambio y preparar recursos', 'owner': 'Responsable del cambio', 'days': 3},
            {'step': 3, 'title': 'Implementar y monitorear indicadores', 'owner': 'Equipo operativo', 'days': 7 if urgency in ['high', 'critical'] else 14},
            {'step': 4, 'title': 'Verificar efectividad y cerrar evidencia', 'owner': 'Auditor interno / Calidad', 'days': 3},
        ]
        return {
            'status': 'plan_ready',
            'ai_requires_human_approval': True,
            'implementation_plan': plan,
            'timeline_days': sum(item['days'] for item in plan),
            'summary': f'Plan generado para {title}.',
        }

    def _risk_actions(self, category, level):
        base = {
            'cyber': ['Reforzar controles de acceso', 'Actualizar respaldos y respuesta a incidentes'],
            'climatic': ['Evaluar continuidad operativa', 'Definir medidas preventivas de infraestructura'],
            'financial': ['Revisar exposición presupuestaria', 'Definir umbrales de escalamiento financiero'],
            'operational': ['Actualizar procedimiento afectado', 'Asignar seguimiento semanal'],
        }
        actions = base.get(category, ['Documentar causa raíz', 'Asignar responsable y fecha de revisión'])
        if level == 'high':
            actions.append('Escalar a revisión por la dirección')
        return actions

    def _safe_num(self, value):
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0

    def _split_text(self, text):
        if not text:
            return []
        return [part.strip() for part in str(text).replace('\n', ',').split(',') if part.strip()]
