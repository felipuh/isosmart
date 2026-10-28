# ADR-0014: Separate KnowledgeLayerRule publication, activation and runtime adoption

- Estado: Aceptado para un gate posterior de foundation inerte exclusivamente
- Fecha: 2026-09-02
- Sucede a: ADR-0013 sin reescribir ADR-0001–ADR-0013
- Policy: `knowledge-layer-rule-publication-activation-runtime-adoption/v1`
- Alcance: diseño; cero migration, datos, grants, runtime o efectos externos

## Contexto

Phase 26 demostró una aplicación exacta que crea vN+1 y una compensación
separadamente gobernada que crea vN+2. Ambos sucesores permanecen draft e
inertes y el runtime conserva vN.

El runtime actual no tiene un bug latest-wins: AgentRun y Recommendation
reciben un `knowledge_layer_rule_id` exacto y exigen que esa fila tenga
`status=published`; los triggers de AgentRunInput y RecommendationBasis repiten
la validación. Sin embargo, esa publicación es también toda la elegibilidad
persistida. No existe Activation, RuntimeAdoption, release binding ni pointer
explícito. Por tanto, un caller podría seleccionar una revisión recién
publicada sin otra decisión de activación/adopción.

Phase 27 registró correctamente este blocker y quedó NOT PROMOTED. Phase 27.1
debe cerrarlo sólo por diseño, sin modificar el comportamiento actual.

## Decisión

Se adoptan cuatro hechos independientes:

```text
VERSION_CREATED
VERSION_PUBLISHED
VERSION_ACTIVATED
RUNTIME_ADOPTED
```

Una futura foundation aditiva usará tres artefactos inmutables:

1. `KnowledgeLayerRulePublication`, evidencia/decisión exacta de publicación;
2. `KnowledgeLayerRuleActivation`, elegibilidad global exacta para release; y
3. `KnowledgeLayerRuleRuntimeAdoption`, transición exacta de configuración de
   runtime.

La publicación nativa y la proyección compatible `status/published_at` deberán
ser atómicas. Esa proyección no será elegibilidad suficiente después del
cutover. La activación referencia publicación exacta y no muta la regla. La
adopción referencia activación exacta y no muta regla, bindings ni provenance.

El runtime futuro recibirá desde configuración confiable un
`runtime_adoption_id` exacto y resolverá la revisión/hash exactos. Missing o
mismatch falla cerrado. Se prohíben greatest/max version, fecha más nueva,
published latest, lineage head/leaf y fallback a cualquier revisión publicada.

Version lineage y adoption lineage son independientes. Una recuperación crea
otra adopción, por ejemplo A1→vN, A2→vN+1, A3→vN. A2 nunca se reescribe y ningún
pointer se rebobina silenciosamente.

## Historia legada

No se inventan decisiones retroactivas. Una fila publicada previa puede
incorporarse sólo como `LEGACY_EVIDENCE_IMPORT`, enlazada a su estado, timestamp,
audit y hash reales, sin afirmar que pasó por el nuevo workflow.

Si la continuidad exige representar la selección runtime preexistente, sólo
una autorización posterior puede crear `LEGACY_BOOTSTRAP`. Este tipo declara
explícitamente que importa la configuración exacta existente, no que hubo una
activación histórica. Debe tener `activation_id=NULL` y
`historical_activation_claim=false`. La foundation inerte no crea ese registro;
si no se aprueba el inventario/bootstrap exacto, el cutover queda bloqueado.

AgentRunInput, RecommendationBasis, KnowledgeLayerBinding, Receipts, eventos y
audits históricos conservan sus IDs exactos y nunca se reescriben.

## Autoridad y separación de funciones

AdminApps permanece autoridad de identidad, MFA, roles globales, acceso y
permisos de gobernanza. Los contextos son resueltos en servidor y fallan
cerrados; claims de cliente no son autoridad.

Publicación, activación y adopción requieren permisos y actores independientes
en la misma cadena. El executor Phase 26 no puede publicar, activar, adoptar ni
reparar. El publisher no puede activar la misma revisión; el activator no puede
adoptar la misma activación. Learning proposer/reviewer/approver/authorizer no
heredan release authority. Un tenant no puede aprobar un cambio global.

Repair es otra autoridad: puede inspeccionar, clasificar, deshabilitar una
capability exacta, auditar un incidente y solicitar recovery. No recibe DML de
target, curation, publish/activate/adopt, SQL arbitrario ni history rewrite.

## Historia, concurrencia y reconciliación

Cada boundary usa ID preasignado, material/idempotency hash, predecessor exacto,
locks y uniqueness. Replay exacto devuelve el artefacto; material distinto es
conflict. Dos adopciones sobre el mismo predecessor producen exactamente un
sucesor; la otra es replay/conflict/stale.

Reconciliation lee el grafo durable y clasifica `COMMITTED`, `NOT_COMMITTED`,
`ABANDONED` o `INCONSISTENT`. Target state solo nunca prueba commit. `ABANDONED`
requiere decisión terminal explícita, no timeout. Missing/mismatched artifact,
event, outbox o audit es `INCONSISTENT`; no se reconstruye Receipt ni autoridad.

Publication, activation, adoption, recovery y capability disable/re-enable son
append-only. Las capabilities de aplicación, publicación, activación y adopción
se pueden cercar independientemente sin cambiar historia ni selección actual.

## Alcance runtime y eventos

El único scope aprobado por diseño es global por lineage de
KnowledgeLayerRule, coherente con el catálogo global actual. No se inventan
scopes por environment, tenant, Organization o agent.

Los eventos futuros son distintos:

- `knowledge_layer_rule.published` v1;
- `knowledge_layer_rule.activation_recorded` v1;
- `knowledge_layer_rule.runtime_adopted` v1.

No reutilizan el evento de aplicación Phase 26 y no encadenan automáticamente
la siguiente transición. RuntimeAdoption es la única fuente de verdad de la
adopción; un Receipt separado sería autoridad redundante.

## Alternativas rechazadas

1. **Publicación equivale a elegibilidad runtime:** mezcla curation con release
   y es el blocker actual.
2. **Latest published wins:** hace que una publicación cambie runtime de forma
   implícita y no determinística.
3. **`is_active` mutable como única historia:** no reconstruye decisiones,
   autoridades ni transiciones.
4. **Pointer rewind recovery:** oculta el incidente y reescribe el significado
   de la selección actual.
5. **Application executor publica:** viola least privilege y permite una cadena
   de auto-release.
6. **Selector genérico de target runtime:** amplía el blast radius a tipos y
   operaciones no autorizados.
7. **Fabricar approvals/activations históricas:** falsea provenance; se usa
   import/bootstrap explícito o se bloquea.
8. **Un solo artefacto publication+activation+adoption:** impide autoridades,
   tiempos, conflictos y disablement independientes.

## Consecuencias

La solución añade tres artefactos y una línea de adopción, pero conserva el
runtime exact-ID actual durante una migración incremental y permite probar la
foundation sin efectuar transiciones. Un gate posterior puede crear migration
0022+ aditiva, roles, constraints, eventos, audit, reconciliación y capability
fences sólo si no inserta datos ni modifica runtime.

El cutover de runtime, legacy bootstrap, publicación, activación, adopción,
deployment y learning-change effectiveness requieren gates posteriores. Phase
26 vN+1/vN+2 permanecen explícitamente excluidos e inertes.
