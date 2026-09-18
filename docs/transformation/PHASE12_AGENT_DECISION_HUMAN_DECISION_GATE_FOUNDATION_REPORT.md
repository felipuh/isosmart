# Phase 12 — Agent Decision + Human Decision Gate Foundation

**Fecha:** 2026-08-17

**Gate:** `PHASE 12 — AGENT DECISION + HUMAN DECISION GATE FOUNDATION`

**PostgreSQL final:** 18.6 (`server_version_num=180006`)

**Run-id final:** `20260817T221240Z_bdab80`

**Veredicto:** **PROMOTED**

## 1. Evolución de migrations

Se agregó sólo
`foundation/0012_agent_decision_human_decision_gate_foundation`. La migration
es aditiva, reversible y condicionada a PostgreSQL mediante
`SeparateDatabaseAndState`. Crea `qms.agent_decision`, `qms.approval`, sus
constraints, triggers, RLS y el narrow database function del Human Decision
Gate. No crea `ActionExecution`, queue de ejecución, tool command, external
target ni efecto de negocio.

| Migration | SHA-256 | Estado |
|---|---|---|
| `0001_foundation_tenant_projection` | `0d72f26245c3637b579e5289b1ee99b87667a1061a245e950992724cb7d2dc51` | frozen/intacta |
| `0002_projection_organization_user_foundation` | `1f538ca4c72309fa670af773f91fd8a62be2732a3222ce3067dbd79fd5e9b537` | frozen/intacta |
| `0003_eventing_immutable_audit_foundation` | `dadfad2c14468352f9f8fc37463f5d689029b98c40e026270223dac5e79613fc` | frozen/intacta |
| `0004_qms_harmonized_context_foundation` | `045043275245e5d8068a8e03d122f5fe34b8f9f60b020336e61881550ecea125` | frozen/intacta |
| `0005_risk_opportunity_objective_foundation` | `96ab33a18252dc0c2e6142f7afdc02a165349d15d50b290b4092c844a1996e86` | frozen/intacta |
| `0006_change_performance_measurement_foundation` | `033242bd6fe801da0b090a332b9f6d1b07dba77027a0334d1830e845cd51aa95` | frozen/intacta |
| `0007_document_evidence_foundation` | `c7f6a2030c9155714093a21fadb571a1cdeb8a121be5598540d4807af62283ec` | frozen/intacta |
| `0008_evidence_coverage_normative_core_foundation` | `285aecb34d5f7e8c1a1273c9622cde7933809949ac7bdbfca04e577e9e762032` | frozen/intacta |
| `0009_knowledge_layer_foundation` | `412c645974635959c74a446f64dc0a9b6dfd2a1a50a6a2e346698850e998effc` | frozen/intacta |
| `0010_governed_recommendation_foundation` | `c4f37a9a3a8d0d20a049e4e1cc9c0e04feb947cbeec9cea18fa89b7964f57b79` | frozen/intacta |
| `0011_agent_definition_run_provenance_foundation` | `cdb23edcad75e8a8781815dac847359a368b64d8ea4b607a40d01d5296c863a2` | frozen/intacta |
| `0012_agent_decision_human_decision_gate_foundation` | `7f280e24a8e95858b8144aa6a85fc645245aa2c2d3c2ad5700dfbe19ac0f0fdc` | nueva/promovida |

La secuencia verificada fue `0001 → … → 0012 → 0011 → 0012`. La reversa
eliminó exclusivamente AgentDecision/Approval y restauró las policies/grants
Phase 11. AgentRun, AgentDefinition y ModelPolicy siguieron presentes y
funcionales.

## 2. Source reconciliation gate

Se leyeron directamente los diez artifacts: XML interno DOCX, las once hojas
XLSX, JSON, DDL, OpenAPI, Mermaid, Draw.io, ambos CSV y LEEME. El DOCX es la
autoridad funcional, XLSX/JSON la autoridad estructurada y DDL/OpenAPI son
contratos parciales. No se introdujo un workflow BPM por costumbre.

| SOURCE | ENTITY | FIELD / RELATION | SEMANTICS | IMPLEMENT? | RATIONALE |
|---|---|---|---|---:|---|
| XLSX/JSON DB_Entities + DOCX §10 | AgentDecision | `decision_id`, exact `agent_run_id`, `decision_type`, `payload_json`, confidence, `explainability_json` | decisión intermedia/final derivada de un run | Sí | contrato estructurado explícito |
| Data Architecture | AgentDecision | tenant-scoped, RLS, append-only | historia de gobernanza/legal | Sí | evita overwrite de decisión material |
| AgentRun/Recommendation promoted foundation | AgentDecision→Recommendation | exact output del exact run cuando existe | no current pointer ni re-point | Sí | FK compuesta + trigger contra AgentRunRecommendation |
| DOCX/XLSX/JSON | AgentDecision | autonomía y Human Decision Gate según política/impacto | metadata/ceiling, nunca permiso de ejecutar | Sí | `decision_autonomy` + gate derivado de exact ModelPolicy |
| DDL/XLSX/JSON | Approval | `approval_id`, tenant, subject, required role, decision, decided by/at, comments | Human Decision Gate separado | Sí, con FK tipada a AgentDecision | elimina subject polimórfico ambiguo para esta slice |
| OpenAPI | Approval decision | `approve`, `reject`, `request_changes`; comments | únicos outcomes concretos respaldados | Sí | CHECK DB exacto; no se inventó escalated |
| Data Architecture | Approval | append decision; no rewrite | cada outcome humano es nueva fila | Sí | UPDATE/DELETE siempre rechazados |
| DDL/OpenAPI | reason | `comments` | razón/comentario humano opcional | Sí | no se inventó reason taxonomy |
| DDL/XLSX/JSON | approval timestamp | `decided_at` | cuándo ocurrió outcome humano | Sí | `timestamptz NOT NULL` |
| AgentDecision source + append history | decision timestamp | fecha de creación de la fila | cuándo se registró decisión | Sí, `created_at` | no existe update timestamp en record inmutable |
| Tenant/AdminApps design + current foundation | actor identity | exact UserProjection + opaque AdminApps user snapshot | identidad histórica sin crear auth local | Sí | no copia PII, MFA, token o secret |
| DDL/XLSX/JSON | authority context | `required_role` | rol requerido en el momento de aprobación | Sí | deriva del ModelPolicy exacto; no del request |
| DOCX Mermaid/runtime + ModelPolicy | human gate | A3 o política aplicable activa revisión humana | gate explícito | Sí | policy contract mínimo, no impact engine |
| DOCX §7/§11 | A0–A4 | maxima/guardrails | techo de autonomía | Sí | A3 exige gate; policy puede exigir A0/A1/A2/A4 |
| DOCX/Mermaid/DDL | ActionExecution | entidad futura separada | ejecución posterior a autorización | No | fuera de scope; tabla ausente |
| DOCX §11 | irreversible/high-impact | nunca bypass por A4 | futuro boundary de gobierno | Documentado | no se inventó scoring/clasificador |

No existe fuente para lineage/revision de AgentDecision o Approval, estados
`pending/approved/rejected/executed`, requester-approver SoD, impact score o
execution authorization concreta. Por ello no se agregaron.

## 3. Invariantes semánticos

| Entidad | Semántica | No equivale a |
|---|---|---|
| Recommendation | propuesta advisory | Approval, AgentDecision o ejecución |
| AgentDecision | decisión/propuesta gobernada derivada de un exact AgentRun | Approval o ejecución |
| Approval | outcome humano explícito cuando el gate aplica | Recommendation o ActionExecution |
| ActionExecution | futuro record de ejecución | ausente en Phase 12 |

Los payloads y audits Phase 12 fijan `advisory_only=true`,
`execution_authorized=false` y `no_execution=true`.

## 4. AgentDecision model

`qms.agent_decision` contiene UUID, tenant, Organization, exact AgentRun,
Recommendation exacta nullable, `decision_type`, payload JSON object,
confidence normalizada `[0,1]`, explainability JSON object,
`decision_autonomy`, `human_gate_required`, exact run trace y `created_at`.

Defensas DB:

- FK compuesta tenant/Organization/AgentRun;
- FK compuesta tenant/Organization/Recommendation;
- trigger que exige Recommendation = exact AgentRunRecommendation;
- trace idéntico al AgentRun;
- autonomy no mayor a requested/effective run ceiling;
- human gate idéntico a exact ModelPolicy rules, con A3 obligatorio;
- JSON object shapes y confidence/autonomy CHECK;
- UPDATE/DELETE siempre rechazados.

No duplica Recommendation body, assumptions, RecommendationBasis ni input
provenance.

## 5. Historia y lifecycle de decisión

AgentDecision es **append-only event-like history**. Las fuentes declaran
append-only y no definen lineage/version; cada decisión material posterior crea
otra fila. No existe destructive overwrite ni current decision pointer.

El lifecycle mínimo se deriva sin un workflow engine:

1. `AgentDecision` registrada = decisión/propuesta registrada;
2. `human_gate_required=true` = human review requerido;
3. existencia de una `Approval` relacionada = human decision recorded.

Ningún estado infiere execution readiness.

## 6. Approval model e inmutabilidad

`qms.approval` contiene UUID, tenant, Organization, exact AgentDecision,
Recommendation exacta nullable, required role, decision, exact UserProjection,
opaque `adminapps_user_id_snapshot`, fixed `actor_type=human`, comments,
`decided_at`, trace y `created_at`.

Outcomes permitidos: `approve`, `reject`, `request_changes`. Un nuevo outcome
posterior es una nueva fila. UPDATE outcome/actor/comments/time/FKs/tenant y
DELETE fueron rechazados por raw SQL. No existe status mutable ni hard delete.

El trigger exige:

- Decision con `human_gate_required=true`;
- Recommendation idéntica a la Decision;
- required role idéntico al exact ModelPolicy de su run;
- UserProjection activa, en el mismo tenant;
- AdminApps user snapshot idéntico a esa projection;
- `actor_type=human`.

## 7. Human actor identity y AdminApps authority boundary

AdminApps continúa siendo system of record de identidad, global roles, MFA y
access authority. `UserProjection` sigue siendo mapping local, nunca
`AUTH_USER_MODEL` ni RBAC authority. Que exista una UserProjection no concede
approval.

`AuthorizedHumanContext` sólo representa autoridad ya resuelta por un adapter
server-side. Conserva:

- TrustedTenantIdentity;
- exact local UserProjection ID;
- opaque AdminApps user ID;
- roles autorizados ya resueltos;
- principal class `human`;
- authority source `adminapps_contract` o fixture controlada.

El command humano no recibe `tenant_id`, `actor_id`, `approver_role`,
`required_role` ni Recommendation. Tenant/actor provienen del authority context,
Recommendation de la Decision y required role del exact policy. Los tests de
firma prueban que body/query/header-shaped authority no existe en la API de
servicio. `principal_type=agent|system` es rechazado antes de DB.

La projection A suspendida por una prueba previa fue rechazada fail-closed; el
harness la reactivó únicamente mediante un evento AdminApps sintético validado,
antes de resolver autoridad.

## 8. Human approver principal

El lifecycle efímero creó `foundation_human_approver_<runid>` como LOGIN real,
non-superuser, `NOBYPASSRLS`, non-owner y `NOINHERIT`. Tiene SELECT tenant
mínimo para el gate, Event/Outbox append y audit append function. No tiene:

- direct `INSERT` sobre Approval;
- AgentDecision write;
- Recommendation/Basis/Run provenance writes;
- QMS business writes;
- normative/Knowledge/agent catalog writes;
- ActionExecution o external action.

Approval se inserta sólo mediante
`qms.foundation_0012_record_human_approval(...)`, `SECURITY DEFINER`,
`search_path` fijo, PUBLIC revoked, EXECUTE sólo al human principal y tenant
context exacto. Worker, projector, audit writer, normative curator y agent
catalog curator tienen cero direct insert y cero execute grant.

## 9. A0–A4 y policy ceiling

- A0: explain/query;
- A1: recommend;
- A2: prepare, never execute;
- A3: human approval required;
- A4: future automation only inside preapproved/reversible/monitored governance.

Todos permanecen non-executing en Phase 12. El ModelPolicy exacto usa el
contrato mínimo `required_autonomy_levels`, `always_required` y
`required_role`. A3 siempre exige gate por semántica fuente; policy puede exigir
gate en cualquier otro nivel, incluido A4. No se hardcodeó “A4 skips approval”
ni “all recommendations require approval”.

Una run con ceiling A2 rechazó Decision A3 antes de persistencia y dejó cero
estado parcial. Una run A4 produjo Decision metadata sin ActionExecution ni
business/external write.

## 10. Exact Run/Recommendation consistency y provenance congelada

El command no acepta Recommendation ID: la deriva de
`AgentRunRecommendation`. DB repite la verificación. Approval tampoco acepta
Recommendation: la deriva de AgentDecision y DB exige igualdad exacta.

La cadena determinística es:

`Approval → AgentDecision → AgentRun → exact AgentDefinition → exact ModelPolicy`

y, cuando existe output:

`AgentDecision → Recommendation → RecommendationBasis → exact Edition /`
`RequirementControl / KnowledgeLayerRule / Evidence`, junto a
`AgentRunInput` exacto.

Tras publicar Definition/Policy v2, la Approval continuó resolviendo
Definition/Policy v1, el mismo Run, Recommendation y required role. No hubo
pointer migration.

## 11. Commands, events y audit

Commands materiales:

- `record_agent_decision`;
- `record_human_approval`;
- `record_human_rejection`;
- `request_human_changes`.

No existe generic save, approve-by-body, infer, execute o tool-call command.

Eventos tenant schema v1:

- `agent_decision.recorded`;
- `approval.recorded`.

Cada command guarda aggregate + DomainEvent + TransactionalOutbox +
ImmutableAuditLog en la misma transacción. Audit de Decision identifica tenant,
Organization, worker, exact run/recommendation/policy, decision/autonomy/gate y
trace. Audit de Approval identifica tenant, Organization, opaque human actor,
Decision, Run, Recommendation, outcome, required role, reason hash, authority
source y trace. No contiene MFA, token, secret o PII copiada.

## 12. Atomic success y rollback

Success sintético:

`Run R1 → Recommendation REC1 → AgentDecision D1 → authorized human H1 → Approval A1`.

Las referencias exactas, evento, outbox y audit fueron coherentes; no apareció
ActionExecution ni mutación QMS.

Rollback deliberado después de Approval/Event/Outbox/Audit preparation dejó
cero delta en las cuatro superficies. Decision y Recommendation preexistentes
quedaron intactas. Decision rollback y ceiling rejection también dejan cero
estado parcial.

## 13. Unauthorized principal y self-approval

Catalog inspection y behavioral tests demostraron:

- worker/projector/audit writer/normative curator/agent catalog curator no
  tienen `INSERT Approval` ni EXECUTE del controlled function;
- worker usando el HumanDecisionGate service falla por permission denied;
- agent/system no puede construir AuthorizedHumanContext;
- `actor_type` DB acepta sólo `human`;
- una UserProjection suspendida no permite approval;
- existencia de UserProjection no implica authority.

Las fuentes no definen requester/approver separation-of-duties adicional, por
lo que no se inventó. Queda como futura evolución de authorization contract.

## 14. RLS, raw SQL, pool y rollback context

AgentDecision y Approval tienen `tenant_id NOT NULL`, `ENABLE ROW LEVEL
SECURITY`, `FORCE ROW LEVEL SECURITY`, cinco policies explícitas por tabla y
composite FKs tenant/Organization.

| Principal/table | Tenant A | none | Tenant B |
|---|---:|---:|---:|
| APP AgentDecision | 2 | 0 | 1 |
| APP Approval | 1 | 0 | 1 |
| HUMAN AgentDecision | 2 | 0 | 1 |
| HUMAN Approval | 1 | 0 | 1 |

Raw SQL rechazó Approval outcome/actor/comments/Decision/tenant UPDATE, DELETE y
AgentDecision Recommendation re-point. Composite FKs/triggers cubren tenant,
Organization, exact Run/Recommendation y actor consistency.

Pool reuse `A → commit → none=0 → B only` y rollback context
`A → exception → none=0 → B only` pasaron para human approver.

## 15. Recommendation/RunInput immutability negative gate

Se calculó un hash canónico conjunto de Recommendation, RecommendationBasis y
AgentRunInput antes/después de Approval: idéntico. Approval no cambió body,
confidence, assumptions, normative/evidence references ni runtime provenance.

## 16. No ActionExecution y high-impact boundary

`to_regclass('qms.action_execution') IS NULL` antes y después de la slice. No
hay execution payload, queue, rollback executor, tool command, external target,
provider call o QMS mutation.

Invariante futuro documentado: high-impact o irreversible nunca puede bypass
governance sólo porque autonomy=A4. Phase 12 no implementa un scoring/impact
engine sin fuente.

## 17. PostgreSQL, forward/reverse y teardown

Gate final sobre imagen oficial PostgreSQL 18.6, run-id
`20260817T221240Z_bdab80`. Ocho principals LOGIN fueron creados con nombres
run-scoped. Ejecutó toda la matriz Phase 1–12, incluyendo RLS, raw SQL,
privilegios, success/rollback, frozen history, pool, reverse/forward y ausencia
de execution.

El finalizer eliminó database, ocho roles, container, volume y temp directory.
`container_absent=true`, `volume_absent=true`, `temp_absent=true`: PASS. Los
runs intermedios fallidos también ejecutaron teardown PASS.

No se usó production, staging, DB compartida, AdminApps DB, MedSupplier DB,
broker, deployment, secret ni `.env`.

## 18. Regresión e integridad Django

| Gate | Resultado |
|---|---|
| Backend completo | **156 PASS / 0 FAIL / 0 SKIP** |
| Delta vs Phase 11 baseline 152 | **+4** contract tests Phase 12 |
| Foundation suite | **58 PASS** |
| Phase 12 focused suite | **4 PASS** |
| `manage.py check` | PASS, 0 issues |
| `makemigrations --check --dry-run` | PASS, no changes detected |
| Python compilation | PASS |
| PostgreSQL Phase 1–12 | PASS |
| Forward/reverse/forward | PASS |

Warnings esperados 400/401/403/404/405, pagination y telemetría
PostHog/Chroma no produjeron failures ni skips. La telemetría preexistente falló
cerrada por DNS y no forma parte de Phase 12.

## 19. Source integrity y final verification

Los diez hashes coinciden con el manifest: `8308bd…`, `e0a59c…`, `11c2b4…`,
`952d8a…`, `ecaecd…`, `30e3c0…`, `de1b48…`, `29ac5c…`, `c41e84…`,
`eb4231…`: **10/10 MATCH**.

`0001–0011` coinciden byte-for-byte con sus hashes promovidos. No se modificó
ningún source artifact, `.env`, repo externo, producción o staging.

## 20. Riesgos residuales

1. `human_gate_rules` usa un contrato mínimo (`required_autonomy_levels`,
   `always_required`, `required_role`); condiciones por impact/reversibility
   requieren schema policy versionado, no claves ad hoc.
2. El human LOGIN representa una clase de principal y el command valida la
   autoridad individual resuelta. Una integración real AdminApps debe verificar
   roles/entitlement freshness y firma antes de construir AuthorizedHumanContext.
3. No hay requester/approver SoD porque las fuentes no lo definen. Si se exige,
   debe añadirse con actor/request contract y migration explícitos.
4. AgentDecision worker direct INSERT queda protegido por RLS/FK/triggers, pero
   Event/Outbox/Audit completos dependen del command service, igual que slices
   anteriores.
5. Approval permite múltiples outcomes append-only; un futuro query de
   “effective/latest human outcome” necesita regla temporal/policy source-backed.
6. Impact/reversibility, prepared action, idempotency y execution authorization
   todavía no existen. No debe introducirse ActionExecution real antes de esos
   contracts.
7. Audit es tamper-evident para runtime; DBA/WORM externo continúa como trust
   boundary.

No quedan P0 ni P1 bloqueando la siguiente slice.

## 21. Veredicto

**PHASE 12 — AGENT DECISION + HUMAN DECISION GATE FOUNDATION: PROMOTED**

| Component/file | State | Evidence | Risk/next action |
|---|---|---|---|
| `0001–0011` | FROZEN / INTACTAS | hashes promovidos exactos | evolucionar sólo 0013+ |
| `0012_agent_decision_human_decision_gate_foundation` | PROMOTED | PostgreSQL 18.6; hash `7f280e…`; reverse/forward PASS | congelar tras promoción |
| AgentDecision | PROMOTED | exact Run/Recommendation, policy ceiling, append-only | richer decision taxonomy sólo con fuente |
| Approval | PROMOTED | exact Decision/Recommendation/actor/outcome; immutable | effective outcome query futuro |
| Human identity/authority | PASS | trusted context; active UserProjection + AdminApps snapshot; spoof fields absent | integrar autoridad real fail-closed |
| Human approver principal | PASS | real LOGIN; function-only write; no business/catalog write | mantener privilege regression |
| A0–A4 | PASS | A2 ceiling rejection; A3 gate; A4 no execution | impact/reversibility contract next |
| Frozen provenance | PASS | v1 approval intact after v2 policy/definition | mantener exact references |
| Event/Outbox/Audit | PASS | atomic success + post-audit rollback | dispatcher futuro ya promovido |
| RLS/raw SQL | PASS | ENABLE+FORCE; A/none/B; mutation/re-point denied | repetir por cada tenant table |
| No ActionExecution | PASS | table absent; zero QMS/external effect | prepare authorization contracts first |
| Backend/Django | PASS | 156/0/0; 58 foundation; check/drift/compile | mantener gate |
| Source artifacts | INTACTOS | 10/10 SHA-256 MATCH | preservar byte-for-byte |
| Recursos efímeros | REMOVED | finalizer PASS | ninguna acción |
