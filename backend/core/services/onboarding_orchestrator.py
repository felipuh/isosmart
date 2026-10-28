from typing import Dict, List, Any


class OnboardingOrchestrator:
    """Orquestador Fase 2: Perfil, Impacto/Ahorro y Propósito/Alineación."""

    def run(self, onboarding_profile: Dict[str, Any], preferred_tone: str = 'manager') -> Dict[str, Any]:
        profile_output = self._build_organizational_profile(onboarding_profile)
        impact_output = self._build_impact_and_savings(onboarding_profile)
        purpose_output = self._build_purpose_and_alignment(onboarding_profile, preferred_tone)
        iso_skeleton = self._build_iso_skeleton(onboarding_profile, profile_output, impact_output, purpose_output)
        adaptive_route = self._build_adaptive_route(onboarding_profile, profile_output)

        summary = {
            'message': 'Sesión inicial analizada. Se generaron recomendaciones de perfil, impacto y alineación.',
            'top_priorities_today': [
                'Validar mapa de procesos sugerido',
                'Confirmar quick wins con responsables',
                'Aprobar objetivos de calidad iniciales',
            ],
            'estimated_annual_savings_range_usd': impact_output.get('estimated_annual_savings_range_usd', [0, 0]),
            'iso_skeleton': iso_skeleton,
            'adaptive_route': adaptive_route,
        }

        return {
            'organizational_profile': profile_output,
            'impact_savings': impact_output,
            'purpose_alignment': purpose_output,
            'summary': summary,
        }

    def _build_adaptive_route(self, profile: Dict[str, Any], organizational_profile: Dict[str, Any]) -> Dict[str, Any]:
        expertise = profile.get('iso_expertise') or 'intermediate'
        route_code = organizational_profile.get('recommended_route') or self._recommend_route_by_expertise(expertise)

        route_catalog = {
            'guided_workshop': {
                'title': 'Ruta Guiada (Nulo/Aprendiz)',
                'mode': 'step_by_step',
                'cadence': 'semanal',
                'description': 'Implementación asistida con foco en lenguaje simple y avances cortos.',
                'recommended_actions': [
                    'Completar checklist base de contexto y alcance',
                    'Documentar 5-8 procesos principales con responsables',
                    'Configurar 3 indicadores críticos con seguimiento semanal',
                    'Ejecutar primera revisión de riesgos y oportunidades',
                ],
            },
            'fast_track': {
                'title': 'Ruta Fast-Track (Intermedio)',
                'mode': 'sprints',
                'cadence': 'quincenal',
                'description': 'Implementación en sprints con entregables concretos y trazables.',
                'recommended_actions': [
                    'Sprint 1: validar alcance, mapa de procesos y stakeholders',
                    'Sprint 2: cerrar matriz de riesgos y objetivos SMART',
                    'Sprint 3: activar control operacional y seguimiento de KPI',
                    'Sprint 4: consolidar auditoría interna y plan de mejora',
                ],
            },
            'advanced_mode': {
                'title': 'Ruta Avanzada (Experto)',
                'mode': 'advanced',
                'cadence': 'mensual',
                'description': 'Optimización de sistema existente con foco en brechas y madurez.',
                'recommended_actions': [
                    'Importar documentación actual y mapear brechas de actualización',
                    'Alinear matriz de riesgos y objetivos con desempeño histórico',
                    'Diseñar tablero ejecutivo con indicadores predictivos',
                    'Ejecutar plan de mejora continua por frentes priorizados',
                ],
            },
            'consultant_mode': {
                'title': 'Modo Consultor (Ninja)',
                'mode': 'multi_org',
                'cadence': 'personalizable',
                'description': 'Gestión avanzada multiempresa con plantillas y estandarización.',
                'recommended_actions': [
                    'Definir plantilla maestra de procesos y riesgos por sector',
                    'Configurar estándares de evidencia y auditoría cruzada',
                    'Asignar roadmap por organización con hitos trimestrales',
                    'Comparar desempeño inter-organización y replicar buenas prácticas',
                ],
            },
        }

        route = route_catalog.get(route_code, route_catalog['fast_track'])
        return {
            'route_code': route_code,
            **route,
        }

    def _build_iso_skeleton(
        self,
        profile: Dict[str, Any],
        organizational_profile: Dict[str, Any],
        impact_output: Dict[str, Any],
        purpose_output: Dict[str, Any],
    ) -> Dict[str, Any]:
        process_template = organizational_profile.get('process_template', {})
        all_processes = (
            process_template.get('strategic', [])
            + process_template.get('operational', [])
            + process_template.get('support', [])
        )

        industry = profile.get('industry_sector') or 'organización de servicios y/o manufactura'
        countries = profile.get('countries') or []
        if isinstance(countries, str):
            countries = [item.strip() for item in countries.split(',') if item.strip()]

        scope_draft = (
            f"El Sistema de Gestión de la Calidad aplica a los procesos estratégicos, operativos y de apoyo "
            f"de la organización en el sector {industry}, incluyendo actividades en {', '.join(countries) if countries else 'sus ubicaciones declaradas'}, "
            f"con enfoque en cumplimiento de requisitos del cliente, mejora continua y gestión basada en riesgos."
        )

        top_risks = [
            {'title': 'Variabilidad operativa', 'clause': '6.1', 'priority': 'alta'},
            {'title': 'Retrasos en entrega', 'clause': '8.5', 'priority': 'alta'},
            {'title': 'Dependencia de proveedores críticos', 'clause': '8.4', 'priority': 'media'},
            {'title': 'Brechas documentales', 'clause': '7.5', 'priority': 'media'},
            {'title': 'No conformidades recurrentes', 'clause': '10.2', 'priority': 'alta'},
        ]

        top_opportunities = [
            {'title': 'Estandarización transversal de procesos', 'clause': '4.4', 'priority': 'alta'},
            {'title': 'Digitalización de evidencias', 'clause': '7.5', 'priority': 'alta'},
            {'title': 'Mejora de desempeño de proveedores', 'clause': '8.4', 'priority': 'media'},
            {'title': 'Gestión visual de KPIs', 'clause': '9.1', 'priority': 'media'},
            {'title': 'Programa de mejora continua por sprints', 'clause': '10.3', 'priority': 'alta'},
        ]

        draft_objectives = purpose_output.get('draft_quality_objectives', [])
        quick_wins = impact_output.get('quick_wins', [])

        suggested_modules = [
            'planning_risks_opportunities',
            'planning_quality_objectives',
            'performance_indicators',
            'improvement_corrective_actions',
            'operations_provider_control',
        ]

        readiness_breakdown = {
            'scope_draft_ready': bool(scope_draft),
            'process_map_ready': len(all_processes) > 0,
            'objectives_v1_ready': len(draft_objectives) > 0,
            'opportunities_identified': len(top_opportunities) > 0,
        }
        readiness_score = round((sum(1 for v in readiness_breakdown.values() if v) / len(readiness_breakdown)) * 100)

        return {
            'scope_draft': scope_draft,
            'initial_process_map': {
                'strategic': process_template.get('strategic', []),
                'operational': process_template.get('operational', []),
                'support': process_template.get('support', []),
            },
            'interested_parties_initial': organizational_profile.get('stakeholder_template', []),
            'top_5_risks': top_risks,
            'top_5_opportunities': top_opportunities,
            'quality_objectives_v1': draft_objectives,
            'quick_wins': quick_wins,
            'suggested_modules': suggested_modules,
            'system_readiness': {
                'score_percentage': readiness_score,
                'breakdown': readiness_breakdown,
            },
        }

    def _build_organizational_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        expertise = profile.get('iso_expertise') or 'intermediate'
        sector = profile.get('industry_sector') or 'general'
        size_range = profile.get('company_size_range') or '10-50'

        process_template = self._suggest_process_template(size_range=size_range)
        stakeholder_template = self._suggest_stakeholders(sector=sector)

        return {
            'recommended_route': self._recommend_route_by_expertise(expertise),
            'process_template': process_template,
            'stakeholder_template': stakeholder_template,
            'depth_level': self._depth_level(expertise),
        }

    def _build_impact_and_savings(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        employees_count = self._safe_int(profile.get('employees_count'))
        size_range = profile.get('company_size_range') or '10-50'

        quick_wins = [
            'Estandarizar control de cambios operativos de alto impacto',
            'Cerrar no conformidades vencidas con verificación de efectividad',
            'Definir tablero semanal de KPIs críticos de calidad y entrega',
        ]
        big_bets = [
            'Proyecto de reducción de reprocesos con enfoque Lean Six Sigma',
            'Rediseño de flujo de proveedores críticos con criterios de desempeño',
            'Automatización de evidencias y trazabilidad documental',
        ]

        savings_range = self._estimate_savings(size_range=size_range, employees_count=employees_count)

        return {
            'main_pain_points_detected': [
                'Retrabajos y variabilidad en procesos',
                'Riesgo de incumplimiento de plazos',
                'Falta de visibilidad integrada de desempeño',
            ],
            'quick_wins': quick_wins,
            'big_bets': big_bets,
            'estimated_annual_savings_range_usd': savings_range,
        }

    def _build_purpose_and_alignment(self, profile: Dict[str, Any], preferred_tone: str) -> Dict[str, Any]:
        leadership_benefits = [
            'Menos horas extra por reducción de urgencias operativas',
            'Mayor claridad de responsabilidades por proceso',
            'Mejor capacidad de delegación con evidencia objetiva',
        ]

        draft_objectives = [
            {
                'title': 'Reducir reprocesos críticos',
                'metric': '% de reprocesos sobre producción total',
                'target': 'Reducir 25% en 6 meses',
            },
            {
                'title': 'Mejorar cumplimiento de entregas',
                'metric': '% de entregas a tiempo',
                'target': 'Aumentar a 95% en 6 meses',
            },
            {
                'title': 'Fortalecer satisfacción del cliente',
                'metric': 'Índice de satisfacción (NPS/CSAT)',
                'target': 'Incrementar 15% en 12 meses',
            },
        ]

        return {
            'language_style_applied': preferred_tone,
            'leadership_benefits': leadership_benefits,
            'draft_quality_objectives': draft_objectives,
        }

    def _suggest_process_template(self, size_range: str) -> Dict[str, List[str]]:
        if size_range in ['10-50', '51-200']:
            return {
                'strategic': ['Direccionamiento estratégico', 'Gestión de riesgos y oportunidades'],
                'operational': ['Ventas y atención al cliente', 'Operación principal', 'Control de calidad'],
                'support': ['Gestión documental', 'Compras y proveedores', 'Talento humano'],
            }
        return {
            'strategic': ['Gobierno corporativo', 'Planificación estratégica', 'Gestión de riesgos y compliance'],
            'operational': ['Gestión comercial', 'Operación por línea de negocio', 'Aseguramiento de calidad', 'Postventa'],
            'support': ['Finanzas', 'Tecnología', 'Gestión documental', 'Talento y capacitación', 'Abastecimiento'],
        }

    def _suggest_stakeholders(self, sector: str) -> List[str]:
        base = ['Clientes', 'Colaboradores', 'Proveedores', 'Entidades regulatorias']
        sector_lower = str(sector).lower()
        if 'manufact' in sector_lower or 'industrial' in sector_lower:
            base.extend(['Certificadoras', 'Canales de distribución'])
        if 'log' in sector_lower or 'it' in sector_lower or 'ingenier' in sector_lower:
            base.extend(['Clientes corporativos clave', 'Aliados tecnológicos'])
        return list(dict.fromkeys(base))

    def _recommend_route_by_expertise(self, expertise: str) -> str:
        mapping = {
            'none': 'guided_workshop',
            'beginner': 'guided_workshop',
            'intermediate': 'fast_track',
            'expert': 'advanced_mode',
            'ninja': 'consultant_mode',
        }
        return mapping.get(expertise, 'fast_track')

    def _depth_level(self, expertise: str) -> str:
        mapping = {
            'none': 'basic',
            'beginner': 'basic',
            'intermediate': 'standard',
            'expert': 'advanced',
            'ninja': 'advanced',
        }
        return mapping.get(expertise, 'standard')

    def _estimate_savings(self, size_range: str, employees_count: int) -> List[int]:
        if employees_count > 0:
            lower = max(12000, employees_count * 150)
            upper = max(30000, employees_count * 420)
            return [lower, upper]

        by_size = {
            '10-50': [12000, 45000],
            '51-200': [30000, 120000],
            '201-500': [90000, 280000],
            '501-2000': [250000, 900000],
            '2000+': [600000, 2000000],
        }
        return by_size.get(size_range, [25000, 100000])

    def _safe_int(self, value: Any) -> int:
        try:
            if value in [None, '']:
                return 0
            return int(value)
        except (TypeError, ValueError):
            return 0
