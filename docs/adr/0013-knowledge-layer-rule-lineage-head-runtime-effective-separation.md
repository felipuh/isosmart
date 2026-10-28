# ADR-0013: KnowledgeLayerRule lineage head and runtime-effective revision separation

- Estado: Aceptado para POC efímero Phase 26 exclusivamente
- Fecha: 2026-08-25
- Sucede a: ADR-0012 sin reescribir ADR-0001–ADR-0012
- Policy: `knowledge-layer-rule-governed-source-reference-application-policy/v1`
- Alcance: diseño; no migration, target mutation, grant, publicación o runtime

## Contexto

Phase 25 rechazó los tres candidatos de primera aplicación. ModelPolicy sigue
rechazado porque una compensación volvería a agregar un modelo aprobado.
AgentDefinition sigue rechazado porque una compensación elevaría autonomía.
KnowledgeLayerRule fue el candidato más cercano: forward y compensation pueden
cambiar sólo el locator de la misma referencia validada, pero el contrato
promovido exige predecessor publicado y target publicado/current leaf.

El primer resultado debe permanecer draft. Por ello vN+1 no puede ser hoy el
target ni predecessor de vN+2. Publicarlo para compensar, crear otra rama desde
vN, borrar vN+1 o rebobinar pointers violaría historia, runtime y gobernanza.

## Decisión de lineage y efectividad

Se separan dos predicados:

```text
lineage_head(rule) = no existe child con previous_revision_id = rule.id
runtime_eligible(rule) = rule.status = published y el consumidor lo referencia por ID exacto
```

La fila head puede ser draft. Un head draft nunca es runtime-eligible. Los
consumidores actuales AgentRun/Recommendation seleccionan un ID exacto y exigen
`published`; no existe adopción por `ORDER BY version DESC`, max(version) o head.

La secuencia POC permitida es lineal:

```text
vN published/runtime-eligible -> vN+1 draft/inert -> vN+2 draft/inert
```

El predecessor unique existente sigue impidiendo forks. Root uniqueness,
same-layer/rule-key FK, lineage equality, no-self y no-cycle siguen vigentes.
`vN+1` y `vN+2` nombran sucesores consecutivos; no introducen aritmética sobre
el label libre `version`.

## Decisión de eligibility

La eligibility ordinaria no cambia: proposal y curator humanos siguen
requiriendo un published current leaf. Una ruta aditiva y positiva puede
aceptar un KnowledgeLayerRule draft head sólo para el mismo operation ID v1,
con exact canonical delta, y sólo si:

- ese head es el resultado intacto de un Receipt forward completo;
- no fue publicado, activado, bound o sucedido;
- la compensación tiene Proposal/Review/Decision/Authorization nuevos;
- el target/hash, forward Receipt, referencia original y delta son exactos; y
- la aplicación ocurre dentro de la capability target-specific.

No se generaliza draft succession a otros targets, operaciones o curators.

## Decisión de operación y fingerprint

Se conserva sin reinterpretación:

```text
learning.knowledge_layer_rule.source_reference.correct / v1
learning-knowledge-layer-rule-source-reference-correction-delta-v1
iso-smart-learning-delta-canonical-v1
```

El perfil ya valida el locator y congela edition UUID/source hash. Por ello
R1→R2 y R2→R1 cumplen la misma relación. Compensation no es `restore
snapshot`; su delta exacto se crea y gobierna por separado.

Un fingerprint v1 incluye Layer, lineage, rule key, logic JSON, evidence
expectation, classification, source-reference scheme, exact StandardEdition y
source hash. Excluye ID/version/predecessor/timestamps/status y sólo el locator.
Antes y después debe ser idéntico. Bindings y provenance se prueban con hashes
de conjuntos separados y no se copian ni re-point.

## Decisión de capability y curator

Se conserva Architecture D: un servicio, una conexión, una transacción externa
y una primitive canónica DB. Una primitive privada compartida concentra
lineage/predecessor/version/draft/audit. Dos wrappers tipados la consumen:

1. wrapper curator, que preserva predecessor publicado y contrato actual;
2. wrapper de aplicación exacta, que resuelve la delta gobernada y permite el
   draft predecessor sólo bajo las precondiciones anteriores.

La primitive privada nunca se concede al executor. El refactor futuro exige
golden parity del command curator. No se duplica la lógica en ORM y SQL.

## Least privilege

El executor es non-owner, NOSUPERUSER, NOINHERIT y NOBYPASSRLS, sin DML target,
publish, activate, curator membership ni SET ROLE. Recibe EXECUTE sólo sobre un
wrapper de firma fija sin target type, field, value, status, operation selector
o payload.

Owners SECURITY DEFINER son NOLOGIN/NOSUPERUSER/NOINHERIT/NOBYPASSRLS, no
poseen tablas/sequences, schema CREATE, role membership, ALTER, TRIGGER o
TRUNCATE. Usan `search_path=pg_catalog`, objetos calificados, sin SQL dinámico y
PUBLIC revocado. El owner con INSERT mínimo es inasumible y sus writes quedan
cerrados por primitive, trigger, claim, Receipt y constraints.

## Receipt, evento, audit y atomicidad

Cada forward/compensation tiene claim/idempotency y Receipt independientes.
Target successor, curation ledger, target-domain event global/outbox, Receipt y
application audit comparten la transacción. Se autoriza para el POC sólo
`knowledge_layer_rule.source_reference_corrected` v1; no se autoriza un evento
de lifecycle de aplicación.

Fallas en cualquier punto revierten todo. Exact replay devuelve el mismo
Receipt; provenance distinta es conflict. Locks y predecessor unique producen
un solo child. Publication/activation/runtime no cambian.

## Migración e historia retenida

Phase 26 probablemente requiere 0021 por claim, Receipt, eligibility exacta,
primitive/grants, fingerprint y target event/outbox. 0001–0020 permanecen
byte-for-byte intactas. 0021 debe ser aditiva antes de historia y forward-only
después del primer Receipt/successor retenido. Disablement revoca EXECUTE y
preserva rows; downgrade nunca borra vN+1/vN+2/event/audit/Receipt.

## Alternativas rechazadas

1. Publicar o activar vN+1 para compensar.
2. Crear vN+2 como segundo child de vN.
3. Mutar/borrar vN+1 o re-pointar predecessors.
4. Usar latest/head como runtime selection.
5. Crear `restore previous version`, snapshot copy o generic patch.
6. Conceder INSERT genérico al executor o reutilizar curator credentials.
7. Permitir draft predecessors a curators u otros target types.
8. Rehabilitar ModelPolicy o AgentDefinition.

## Consecuencias

El diseño cierra el blocker exacto sin autorizar aplicación actual. Phase 26
puede implementar y probar efímeramente sólo esta capability. El costo es una
migration/primitive/Receipt/event foundation target-specific y parity tests del
curator. La ganancia es lineage reversible a nivel histórico sin afirmar
rollback de negocio ni cambiar runtime.
