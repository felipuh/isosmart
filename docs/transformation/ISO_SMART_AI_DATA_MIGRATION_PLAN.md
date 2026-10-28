# ISO Smart AI — plan incremental de migración de datos

## Patrón obligatorio por agregado

`EXPAND → BACKFILL → RECONCILE → DUAL-READ (sólo si necesario) → SWITCH → OBSERVE → CONTRACT`

No hay big bang, delete de objetos duplicados ni dual-write indefinido. Cada agregado tiene feature flag de read path, source mapping durable, checkpoint reanudable, métricas, stop conditions y rollback. DDL y backfill se separan cuando reduce locks.

## Gates por etapa

| Etapa | Acción | Evidencia | Rollback/stop |
|---|---|---|---|
| EXPAND | Tablas/columns nullable, índices concurrentes, roles/policies, adapters | migration forward/backward, lock budget | Revert code/objetos nuevos vacíos |
| BACKFILL | Lotes tenant-scoped, idempotentes, source IDs + hashes | counts, nulls, hash totals, checkpoints | Pause; corregir mapping; no borrar target |
| RECONCILE | Clasificar cada source row | 100% `mapped/conflict/quarantine/excluded-with-reason` | Stop si unknown/cross-tenant > 0 |
| DUAL-READ | Comparar legacy/target sin cambiar respuesta; sólo si el adapter lo exige | mismatch rate por campo/tenant | Flag a legacy |
| SWITCH | Lectura target por canary/tenant | API parity, latency, error/denial metrics | Flag a legacy; detener consumers |
| OBSERVE | Mantener legacy, bloquear nuevas divergencias | ventana aprobada + cero unknown | Extender ventana/revert flag |
| CONTRACT | Detener writes/retirar adapters en release posterior | telemetry cero, backup restore, owner approval | No contract si rollback window abierta |

Compatibility windows no se fijan por calendario en diseño; Product/Data/SRE las aprueban por agregado. Stop conditions: any cross-tenant link, unmapped source row, source/target count/hash drift no explicado, RLS escape, P0 contract regression, irreversible lock/latency, rollback test fallido o audit/outbox incompleto.

## Mapping legado

| Legacy model | Target model | Migration source | Canonical target | Dedupe rule | Conflict rule | Rollback |
|---|---|---|---|---|---|---|
| `core.Organization` | TenantProjection + Organization | `external_id`, org fields | AdminApps projection + QMS org | external ID sólo para projection; QMS business key reviewed | missing/duplicate external ID → quarantine | legacy org read flag |
| local users/profiles | UserProjection + QMS assignments | AdminApps external ID, profile | identity projection; local domain roles | exact external subject; never email alone | duplicate subject/tenant mismatch → deny/quarantine | legacy auth adapter, no password creation |
| BillingSubscription/Payment | Subscription/BillingProjection + historical snapshot | external refs/status | AdminApps authority | external payment/subscription ID | local vs AdminApps mismatch → AdminApps wins, report | legacy history read-only |
| `core.ProcessMap` / `spm.ProcessMap` | Process + source mapping/view | both tables | one Process | tenant + approved business key + provenance; not title only | differing owner/scope/status → review queue | dual read adapters |
| core/sie StakeholderProfile | Stakeholder | both sources | one Stakeholder | approved external/business identifier | semantic mismatch → separate candidates until human merge | legacy adapters |
| needs/expectations + CustomerRequirement | StakeholderRequirement | related rows | typed requirement | exact source mapping; no text-only merge | contradictory addressed/status → superseded versions/review | legacy read |
| RiskMatrix/RiskOpportunity | Risk + Opportunity + assessments | source type/IDs | one business object per type | explicit type + tenant + provenance | ambiguous combined row → quarantine/manual classification | legacy combined view |
| core/planning QualityObjective | Objective | both tables | one Objective | source mapping + approved business ID | metric/target/owner disagreement → review | legacy objective view |
| ChangeLog/ChangeControl | Change | both sources | one Change | explicit relation/source IDs | state/approval conflict → preserve both histories, review canonical | legacy adapters |
| core.Document/files | Document + DocumentVersion | DB/file metadata/content | identity + immutable versions | source ID; hash detects bytes, not identity | missing file/hash/version → quarantine | legacy download/read |
| EvidenceNode/Edge | Evidence + EvidenceCoverage + typed edge | node/edge types | canonical evidence graph | exact source IDs + approved type map | unknown edge/cross-tenant → quarantine, never import | legacy graph flag |
| InternalAudit/AuditFinding | Audit/Finding | current QMS apps | canonical aggregates | source mapping | inconsistent criteria/evidence tenant → stop | legacy APIs |
| operations/improvement Nonconformity | Nonconformity | both contexts | one NC | source mapping + approved external NC key | never merge by title; contradictory severity/state → review | dual reads |
| improvement CorrectiveAction | CorrectiveAction/EffectivenessCheck | current model | canonical CAPA | source ID + NC mapping | orphan/cross-context ambiguity → quarantine | legacy CAPA reads |
| scattered approvals | Approval | approval records/logs | common Human Gate | source record ID; preserve decision | duplicate/conflicting decisions remain separate with provenance | legacy approval adapter |
| assistant/AI logs | AgentRun/Decision/Recommendation/Basis | only records with adequate provenance | governed runtime | no inferred reconstruction | incomplete provenance → legacy historical class, not material recommendation | legacy read-only logs |
| ISOClauseConfig/standard JSON | Standard/Edition/Clause/Control | curated import only | versioned normative catalog | code within exact edition | source/license/version unknown → do not publish | retain legacy config |

## Normative edition migration

Published data never updates destructively. `standard.edition.published` creates `StandardEdition N+1`, Clause/RequirementControl and KnowledgeLayerRule/Binding release. Pipeline: publish candidate → calculate machine-readable delta → applicability review per StandardPack → evidence impact report (no reassignment) → Foundation Gate delta path → human validation for material changes → activate effective edition. EvidenceCoverage retains N and its rule/binding versions.

## Tenant/backfill safety

Backfills enumerate a validated TenantProjection and open one transaction/batch with `SET LOCAL`; source and target tenant IDs are asserted. No “default tenant”. Unknown external IDs stop/quarantine. Checkpoints include source range, tenant, row counts, source/target hashes and migration version. Management commands require explicit tenant or an approved platform mode that still fans out isolated batches.

## Metrics and rollback

Metrics: rows scanned/mapped/conflict/quarantine, lag, mismatched fields, target nulls, FK/RLS denials, query parity, API errors/latency, outbox lag, audit coverage and legacy read/write calls. Rollback changes flags/read paths and pauses dispatchers; it does not delete target data. A later cleanup requires backup manifest, successful restore, retention approval and evidence of zero reads/writes.
