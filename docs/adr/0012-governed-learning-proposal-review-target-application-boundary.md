# ADR-0012: governed learning proposal review and target application boundary

- Estado: Aceptado para gate posterior de foundation de review/decision/authorization
- Fecha: 2026-08-24
- Sucede a: ADR-0011 sin reescribir ADR-0001–ADR-0011
- Policy: `governed-learning-proposal-review-application-boundary/v1`
- Alcance: diseño y gobernanza; ninguna aplicación o mutación autorizada

## Contexto

Phase 21 promovió `LearningSignal` y `LearningProposal` inmutables, tenant/
Organization-scoped y no ejecutables. Las propuestas congelan un target global
publicado exacto (`ModelPolicy`, `AgentDefinition` o `KnowledgeLayerRule`), su
fila material completa y hash. El principal de learning no posee DML sobre esos
targets y sólo existen eventos `learning_signal.created` y
`learning_proposal.created`.

El siguiente problema arquitectónico es permitir review, decisión y una futura
autorización de aplicación sin convertir LearningProposal en autoridad de
ejecución ni crear una capacidad genérica de auto-modificación.

## Decisión

Adoptar `GOVERNED_LEARNING_PROPOSAL_REVIEW_APPLICATION_BOUNDARY_V1.md` y separar
cinco hechos: propuesta, review, decisión, autorización de aplicación y creación
futura de versión. `approved_for_application` sólo permite solicitar una
autorización separada; nunca ejecuta.

Cada review, decisión y autorización se liga a una revisión/hash exactos de la
propuesta y a identidad, lineage, versión y hash exactos del target. Drift o una
corrección posterior falla cerrado; no existe rebinding a “latest”. Una
autorización es inmutable, revocable/expirable si la policy lo define,
one-time e idempotente para una capability target-specific exacta.

Todos los targets actualmente allow-listed son globales. Una propuesta derivada
de tenant requiere decisión global separada. El tenant no recibe autoridad de
curador, publish, activate o release; no existe agregación ni influencia
cross-tenant.

No se concede aplicación. Un gate posterior puede implementar sólo la foundation
inert de review/decision/authorization. Otro gate posterior y target-specific
deberá probar una capability estrecha antes de crear cualquier draft vN+1.

## Target readiness

`ModelPolicy`, `AgentDefinition` y `KnowledgeLayerRule` tienen lineage/version,
published history inmutable y commands de curación estrechos que crean draft
successors. Son candidatos condicionales para diseño de review/authorization,
no targets autorizados para aplicación.

Prompt/rule bundle y retrieval configuration sólo aparecen como provenance
(`prompt_version`, `rule_bundle_version`, dataset/embedding namespace). No son
entidades target versionadas con lifecycle/curator promovido y quedan NOT READY.

## Least privilege

La arquitectura futura debe usar una capability por target + operación. El
principal de review/approval/authorization no obtiene target DML. Un futuro
executor, si se autoriza, sólo podría invocar una capability exacta y no podría
publicar, activar, borrar historia ni ejecutar UPDATE genérico. AdminApps sigue
siendo autoridad de identidad, MFA, roles globales, tenant/product access y
permisos relevantes; actor/role/tenant/approval client-side no son autoridad.

## Alternativas rechazadas

1. **Motor genérico `target/field/operation/value`:** rechazado porque destruye
   least privilege, permite campos arbitrarios y mezcla policy con ejecución.
2. **Aplicación automática de propuesta:** rechazado porque evidencia o conteos
   no son autoridad y habilitarían feedback/self-modification.
3. **Mutación global directa por tenant:** rechazada porque un tenant no puede
   alterar comportamiento compartido ni afectar otros tenants.
4. **Approval equivale a execution:** rechazado; review/decision,
   authorization, application y release son gates distintos.
5. **Overwrite de la versión actual:** rechazado; vN permanece inmutable y un
   resultado futuro sólo puede ser un draft successor vN+1.
6. **Usar `LearningProposal.status` como autoridad:** rechazado; escondería
   decisión, autoridad, expiry/revocation, idempotencia y provenance.
7. **Tratar strings de prompt/retrieval como targets:** rechazado; provenance
   sin entidad/versionado/curador no es una frontera de mutación segura.

## Consecuencias

La separación añade artefactos y gates, pero conserva trazabilidad, tenant
isolation, curator ownership y replay determinístico. Correcciones y drift
requieren nueva revisión; publicación/activación/deployment permanecen fuera de
la creación de successor. Autonomía, guardrails y contenido normativo no pueden
ampliarse mediante learning.

No se crea migration 0019, evento, executor, grant, modelo ni runtime en esta
decisión. Rollback documental usa un ADR/policy successor; no reescribe esta
historia.
