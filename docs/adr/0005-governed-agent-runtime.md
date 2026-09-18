# ADR-0005: runtime común de agentes gobernados

- Estado: Propuesto
- Fecha: 2026-08-13

## Decisión

Todo agente ejecuta Observe → Contextualize → Retrieve → Validate → Analyze → Simulate → Recommend → Evaluate autonomy → Human gate → Execute → Effectiveness → Governed learning. `AgentRun` y `RecommendationBasis` congelan proveedor/modelo/versiones, prompt, reglas, evidencia, dataset, trace, confianza, supuestos, aprobación, acción y resultado.

A0–A2 no ejecutan; A3 requiere aprobación explícita; A4 solo opera dentro de guardrails reversibles, monitorizados y preautorizados. No se permite recomendación material sin provenance.

## Consecuencias

Los motores IA actuales deben envolverse en el runtime antes de ampliar autonomía. Reglas deterministas, retrieval, inferencia, policy y decisión humana son componentes probables y testeables por separado.
