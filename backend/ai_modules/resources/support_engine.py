"""AI services for ISO 9001 clause 7 support workflows."""

from collections import Counter

from ai_modules.common.base import AIModuleBase


class SupportAIService(AIModuleBase):
    def __init__(self):
        super().__init__('resources')

    def process(self, data):
        operation = (data or {}).get('operation', '')
        handlers = {
            'competence_plan': self.build_competence_plan,
            'awareness_pulse': self.measure_awareness_pulse,
            'communication_draft': self.generate_communication_draft,
            'document_health': self.evaluate_document_health,
        }
        handler = handlers.get(operation)
        if not handler:
            return {'status': 'error', 'message': f'Operacion no soportada: {operation}'}
        return handler(data or {})

    def build_competence_plan(self, data):
        competences = data.get('competences') or []
        gaps = [item for item in competences if item.get('has_gap')]
        by_level = Counter(item.get('required_level') or 'unknown' for item in gaps)

        recommendations = []
        for item in gaps[:5]:
            recommendations.append({
                'user_id': item.get('user_id'),
                'competence': item.get('competence_name'),
                'priority': 'high' if (item.get('required_level') in ['advanced', 'expert']) else 'medium',
                'action': 'Programar capacitacion focalizada y evaluacion de cierre en 30 dias.',
            })

        return {
            'status': 'plan_ready',
            'summary': {
                'total_competences': len(competences),
                'total_gaps': len(gaps),
                'gap_ratio': round((len(gaps) / len(competences)), 2) if competences else 0,
                'critical_gaps': by_level.get('expert', 0) + by_level.get('advanced', 0),
            },
            'recommendations': recommendations,
        }

    def measure_awareness_pulse(self, data):
        activities = data.get('activities') or []
        total = len(activities)
        scored = sum(1 for item in activities if (item.get('effectiveness_evaluation') or '').strip())
        completion = round((scored / total) * 100, 1) if total else 0

        status = 'healthy'
        if completion < 40:
            status = 'critical'
        elif completion < 70:
            status = 'warning'

        suggestions = [
            'Lanzar micro-quiz semanal sobre politica y objetivos de calidad.',
            'Publicar capsulas de 3 minutos en intranet con casos reales.',
            'Reforzar areas con menor participacion usando lideres de proceso.',
        ]

        return {
            'status': 'pulse_ready',
            'awareness': {
                'activities_total': total,
                'activities_with_evidence': scored,
                'completion_percentage': completion,
                'health_status': status,
            },
            'suggested_actions': suggestions,
        }

    def generate_communication_draft(self, data):
        topic = (data.get('topic') or 'Actualizacion del SGC').strip()
        audience = (data.get('target_audience') or 'Todo el personal').strip()
        channel = (data.get('channel') or 'intranet').strip()

        return {
            'status': 'draft_ready',
            'draft': {
                'subject': f'[Calidad] {topic}',
                'body': (
                    f'Estimado equipo ({audience}),\\n\\n'
                    f'Compartimos una actualizacion relevante: {topic}.\\n'
                    'Revise las acciones asignadas y confirme lectura en el portal interno.\\n\\n'
                    'Gracias por contribuir al SGC y a la mejora continua.'
                ),
                'recommended_channel': channel,
                'cta': 'Confirmar lectura y enviar preguntas en 48 horas.',
            },
        }

    def evaluate_document_health(self, data):
        documents = data.get('documents') or []
        outdated = [doc for doc in documents if doc.get('status') == 'outdated']
        pending_approval = [doc for doc in documents if doc.get('status') == 'pending_approval']

        return {
            'status': 'analysis_ready',
            'document_health': {
                'total': len(documents),
                'outdated': len(outdated),
                'pending_approval': len(pending_approval),
                'compliance_index': max(0, 100 - (len(outdated) * 10) - (len(pending_approval) * 5)),
            },
            'recommended_actions': [
                'Priorizar revision de documentos vencidos con mayor impacto operacional.',
                'Ejecutar flujo de aprobacion digital para politicas y procedimientos criticos.',
            ],
        }
