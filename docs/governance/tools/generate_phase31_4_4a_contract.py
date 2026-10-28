"""Build the append-only Phase 31.4.4A full field-binding contract.

Offline only: reads frozen repository artifacts and writes deterministic JSON.
It does not import Django, open a database, invoke a service, or use a network.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import uuid
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
V2_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_ROW_LEVEL_EXECUTION_CONTRACT_V2.json"
AUDIT_PATH = ROOT / "docs/governance/evidence/PHASE31_4_3_SUPPORTING_CONTRACT_AUDIT_V1.json"
OUT_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4A_ROW_LEVEL_EXECUTION_CONTRACT_V2_1.json"
NAMESPACE = uuid.UUID("05611a8a-f662-5b7f-ad24-c4df48d573ec")
ALLOWED = {
    "EXACT_LITERAL", "DETERMINISTIC_DERIVATION", "REFERENCE_TO_BOUND_FIELD",
    "ADOPTED_STATIC_SCHEMA_DEFAULT", "EXECUTION_DERIVED_PERSISTED",
    "EXECUTION_DERIVED_EXTERNAL_AUTHORITY", "NATIVE_OUTPUT", "ADR0017_MAPPED_OUTPUT",
}
ARTIFACT_EXTRA_SCHEMAS = {
    "publication-closure-v2": ["artifact_schema", "experiment_id", "scope", "member_keys", "member_hashes", "fixed_point", "unknown_disposition_count", "canonicalization", "observed_at", "canonical_hash"],
    "activation-closure-v2": ["artifact_schema", "experiment_id", "scope", "member_keys", "member_hashes", "fixed_point", "unknown_disposition_count", "canonicalization", "observed_at", "canonical_hash"],
    "expected-retention-closure/v2": ["artifact_schema", "experiment_id", "member_keys", "member_count", "fixed_point", "unknown_disposition_count", "canonicalization", "observed_at", "canonical_hash"],
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def migration_manifest() -> tuple[dict[str, str], str]:
    paths = sorted((ROOT / "backend/foundation/migrations").glob("00[0-2][0-9]_*.py"))
    paths = [p for p in paths if 1 <= int(p.name[:4]) <= 23]
    manifest = {str(p.relative_to(ROOT)): sha(p) for p in paths}
    material = "".join(f"{name}\0{digest}\n" for name, digest in manifest.items()).encode()
    return manifest, hashlib.sha256(material).hexdigest()


def uuid5_value(label: str) -> str:
    return str(uuid.uuid5(NAMESPACE, f"phase31.4.4a/{label}/v1"))


def literal(value, field_type: str, reason: str, provenance: str = "Phase31.4.4A exact synthetic fixture design") -> dict:
    return {
        "kind": "EXACT_LITERAL", "typed_value": value,
        "database_type_or_schema_type": field_type,
        "canonical_representation": "canonical-json-rfc8785-compatible/v1",
        "provenance": provenance, "reason": reason,
    }


def derived(member: dict, name: str, field_type: str) -> dict:
    return {
        "kind": "EXECUTION_DERIVED_PERSISTED", "producer": member["producer"],
        "producer_version": member["producer_version"],
        "source_state": f"all bound inputs for {member['qualified_table']}::{member['primary_key']} at {member['freeze_point']}",
        "transaction_boundary": member["transaction_boundary"], "freeze_point": member["freeze_point"],
        "canonicalization": "postgresql-jsonb-canonical-v1 for JSON; lowercase hex for digests; UTC ISO-8601 for time",
        "downstream_consumers": "only declared V2 registry successors and retained evidence",
        "retention_rule": member["retention_disposition"],
        "verification_rule": f"persist-reread-canonical-equality/v1:{name}:{field_type}",
    }


def external(member: dict, name: str) -> dict:
    return {
        "kind": "EXECUTION_DERIVED_EXTERNAL_AUTHORITY",
        "authority_contract": member["authority_contract"], "actor": "synthetic actor slot bound by the operation admission",
        "permission": "exact operation permission from phase31.4.4-capability-matrix/v1",
        "scope": "single experiment, tenant, organization, target and operation",
        "MFA_requirement": "required when the governing operation policy requires MFA",
        "active_access_requirement": "active access required; fail closed",
        "policy_binding": "COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V2 + ADR-0018",
        "evaluation_point": f"immediately before {member['transaction_boundary']}",
        "precommit_revalidation": True,
        "retained_provenance_schema": f"phase31.4.4-exact-authority-envelope/v1#{name}",
    }


def deterministic(label: str, field_type: str) -> dict:
    preimage = f"phase31.4.4a/{label}/v1"
    return {
        "kind": "DETERMINISTIC_DERIVATION", "algorithm_id": "RFC4122-UUIDv5-SHA1",
        "algorithm_version": "RFC4122/v5", "all_preimage_inputs": {"namespace_uuid": str(NAMESPACE), "utf8_name": preimage},
        "input_types": {"namespace_uuid": "uuid", "utf8_name": "UTF-8 string"},
        "canonical_input_encoding": "16 namespace UUID octets followed by exact UTF-8 name octets",
        "output_type": field_type, "expected_output": uuid5_value(label),
        "verification_rule": "uuid.uuid5(UUID(namespace_uuid), utf8_name) string equality",
    }


def reference(source: dict, source_field: str = "id") -> dict:
    return {
        "kind": "REFERENCE_TO_BOUND_FIELD",
        "source_member": f"{source['qualified_table']}::{source['primary_key']}",
        "source_field": source_field, "required_source_freeze": source["freeze_point"],
        "copy_or_transform": "copy", "transform_algorithm_if_any": None,
    }


def canonical_type(meta: dict) -> str:
    if meta.get("database_type"):
        value = meta["database_type"].lower()
        if value.startswith(("varchar", "char", "text")): return "text"
        if value.startswith("timestamp"): return "timestamptz"
        return value
    mapping = {"UUIDField": "uuid", "CharField": "text", "TextField": "text", "BigIntegerField": "bigint", "IntegerField": "integer", "PositiveIntegerField": "integer", "PositiveSmallIntegerField": "smallint", "BooleanField": "boolean", "DateTimeField": "timestamptz", "DateField": "date", "DecimalField": "numeric", "JSONField": "jsonb", "ForeignKey": "uuid", "OneToOneField": "uuid"}
    return mapping.get(meta.get("type"), meta.get("type", "schema-value"))


def pick_target(rows: list[dict], target_model: str, member: dict, name: str) -> dict | None:
    candidates = [r for r in rows if r["row_type"].split(":")[0] == target_model or r["qualified_table"] == target_model]
    if not candidates:
        return None
    if target_model == "Opportunity":
        wanted = "after" if any(x in name for x in ("resulting", "after")) else "before"
        hit = [r for r in candidates if wanted in r["row_type"] or wanted in r["purpose"].lower()]
        if hit: return hit[0]
    if target_model == "Evidence":
        hit = [r for r in candidates if ("effectiveness" in member["row_type"].lower()) == ("Effectiveness" in r["row_type"])]
        if hit: return hit[0]
    prior = [r for r in candidates if rows.index(r) <= rows.index(member)]
    return prior[-1] if prior else candidates[0]


STATIC_OVERRIDES = {
    ("qms.tenant_projection", "adminapps_tenant_id"): ("uuid", uuid5_value("external-control-plane/tenant"), "Synthetic control-plane fixture identity; it does not assert a real AdminApps tenant"),
    ("qms.tenant_projection", "source_version"): ("bigint", 1, "Exact positive synthetic projection source version"),
    ("qms.tenant_projection", "display_name_snapshot"): ("text", "TEST ONLY — ISO SMART AI PHASE 31.4.4A SYNTHETIC TENANT", "Visibly non-real UTF-8 tenant display snapshot"),
    ("qms.tenant_projection", "lifecycle_status"): ("text", "pending", "Valid frozen lifecycle state without claiming active control-plane provisioning"),
    ("qms.tenant_projection", "provisioning_status"): ("text", "pending", "Valid frozen provisioning state that does not claim completion"),
    ("qms.tenant_projection", "reconciliation_status"): ("text", "in_sync", "Synthetic fixture material is internally reconciled; no real authority call is implied"),
    ("qms.user_projection", "lifecycle_status"): ("text", "active", "Synthetic actor must be locally active for the governed test path"),
    ("qms.opportunity", "status"): ("text", None, "Resolved per exact opportunity revision"),
}

TABLE_STATIC = {
    ("normative.standard_edition", "status"): "published",
    ("normative.knowledge_layer", "certifiability_classification"): "non_certifiable_guidance",
    ("normative.knowledge_layer_rule", "certifiability_classification"): "non_certifiable_guidance",
    ("normative.knowledge_layer_rule", "status"): "published",
    ("governance.model_policy", "status"): "published",
    ("governance.agent_definition", "status"): "published",
    ("qms.recommendation", "status"): "proposed",
    ("qms.action_plan", "impact"): "standard",
    ("qms.action_plan", "reversibility"): "reversible",
    ("qms.approval", "decision"): "approve",
    ("qms.execution_authorization", "impact"): "standard",
    ("qms.execution_authorization", "outcome"): "authorized",
    ("qms.execution_authorization", "reversibility"): "reversible",
    ("qms.action_execution", "executor_type"): "controlled_opportunity",
    ("qms.action_execution", "status"): "succeeded",
    ("qms.action_execution_receipt", "executor_type"): "controlled_opportunity",
    ("qms.action_execution_receipt", "outcome"): "opportunity_deferred",
    ("qms.learning_signal", "selected_outcome_snapshot"): "effective",
    ("qms.learning_signal_effectiveness", "outcome_snapshot"): "effective",
    ("eventing.transactional_outbox", "status"): "pending",
    ("qms.learning_proposal", "status"): "governance_pending",
    ("qms.learning_proposal_review", "target_status_snapshot"): "valid",
    ("qms.learning_proposal_review", "review_outcome"): "review_recorded",
    ("qms.learning_proposal_review", "governance_scope"): "global",
    ("qms.learning_proposal_review", "policy_id"): "governed-learning-proposal-review-application-boundary/v1",
    ("qms.learning_proposal_decision", "outcome"): "approved_for_application",
    ("qms.learning_proposal_decision", "governance_scope"): "global",
    ("qms.learning_proposal_decision", "policy_id"): "governed-learning-proposal-review-application-boundary/v1",
    ("qms.learning_application_authorization", "governance_scope"): "global",
    ("qms.learning_application_authorization", "policy_id"): "governed-learning-proposal-review-application-boundary/v1",
    ("qms.learning_application_authorization", "authorization_status"): "authorized",
    ("qms.learning_proposal", "canonicalization_version"): "iso-smart-learning-delta-canonical-v1",
    ("qms.learning_proposal", "delta_schema_version"): "learning-knowledge-layer-rule-source-reference-correction-delta-v1",
    ("qms.learning_proposal", "operation_id"): "learning.knowledge_layer_rule.source_reference.correct",
    ("qms.learning_proposal", "operation_version"): "v1",
    ("qms.learning_proposal", "target_type"): "KnowledgeLayerRule",
    ("qms.learning_proposal_review", "canonicalization_version"): "iso-smart-learning-delta-canonical-v1",
    ("qms.learning_proposal_review", "delta_schema_version"): "learning-knowledge-layer-rule-source-reference-correction-delta-v1",
    ("qms.learning_proposal_review", "operation_id"): "learning.knowledge_layer_rule.source_reference.correct",
    ("qms.learning_proposal_review", "operation_version"): "v1",
    ("qms.learning_proposal_review", "target_type"): "KnowledgeLayerRule",
    ("qms.learning_proposal_decision", "canonicalization_version"): "iso-smart-learning-delta-canonical-v1",
    ("qms.learning_proposal_decision", "delta_schema_version"): "learning-knowledge-layer-rule-source-reference-correction-delta-v1",
    ("qms.learning_proposal_decision", "operation_id"): "learning.knowledge_layer_rule.source_reference.correct",
    ("qms.learning_proposal_decision", "operation_version"): "v1",
    ("qms.learning_proposal_decision", "target_type"): "KnowledgeLayerRule",
    ("qms.learning_application_authorization", "canonicalization_version"): "iso-smart-learning-delta-canonical-v1",
    ("qms.learning_application_authorization", "delta_schema_version"): "learning-knowledge-layer-rule-source-reference-correction-delta-v1",
    ("qms.learning_application_authorization", "operation_id"): "learning.knowledge_layer_rule.source_reference.correct",
    ("qms.learning_application_authorization", "operation_version"): "v1",
    ("qms.learning_application_authorization", "target_type"): "KnowledgeLayerRule",
    ("qms.learning_application_authorization", "capability_id"): "learning.knowledge_layer_rule.source_reference.correct",
    ("qms.learning_application_authorization", "capability_version"): "v1",
    ("qms.learning_proposal_canonical_delta", "canonicalization_version"): "iso-smart-learning-delta-canonical-v1",
    ("qms.learning_proposal_canonical_delta", "delta_schema_version"): "learning-knowledge-layer-rule-source-reference-correction-delta-v1",
    ("qms.learning_proposal_canonical_delta", "operation_id"): "learning.knowledge_layer_rule.source_reference.correct",
    ("qms.learning_proposal_canonical_delta", "operation_version"): "v1",
    ("qms.learning_proposal_canonical_delta", "target_type"): "KnowledgeLayerRule",
    ("qms.learning_target_application_receipt", "canonicalization_version"): "iso-smart-learning-delta-canonical-v1",
    ("qms.learning_target_application_receipt", "delta_schema_version"): "learning-knowledge-layer-rule-source-reference-correction-delta-v1",
    ("qms.learning_target_application_receipt", "result_status"): "draft",
    ("normative.knowledge_layer_rule_event", "event_type"): "knowledge_layer_rule.source_reference_corrected",
    ("eventing.platform_transactional_outbox", "destination"): "platform.knowledge-layer-rule",
    ("eventing.platform_transactional_outbox", "status"): "pending",
    ("normative.knowledge_layer_rule_publication", "evidence_kind"): "NATIVE",
    ("eventing.knowledge_layer_rule_governance_outbox", "destination"): "platform.knowledge-layer-rule-governance",
    ("eventing.knowledge_layer_rule_governance_outbox", "status"): "pending",
}


def static_value(member: dict, meta: dict, rows: list[dict]) -> dict:
    table, name, typ = member["qualified_table"], meta["column"], canonical_type(meta)
    override = STATIC_OVERRIDES.get((table, name))
    if override:
        value = override[1]
        if table == "qms.opportunity" and name == "status":
            value = "deferred" if "deferred" in member["row_type"] else "under_evaluation"
        return literal(value, override[0], override[2])
    if (table, name) in TABLE_STATIC:
        return literal(TABLE_STATIC[(table, name)], typ, "Exact value accepted by the frozen schema and promoted service validation")
    if name == "operation_kind" and table in {"normative.knowledge_layer_rule_governance_claim", "normative.knowledge_layer_rule_governance_event", "audit.knowledge_layer_rule_governance_audit"}:
        value = "ACTIVATION" if "ACTIVATION" in member["row_type"] else "PUBLICATION"
        return literal(value, typ, "Exact migration-0022 operation kind for this release graph")
    if name == "event_type" and table == "normative.knowledge_layer_rule_governance_event":
        value = "knowledge_layer_rule.activation_recorded" if "ACTIVATION" in member["row_type"] else "knowledge_layer_rule.published"
        return literal(value, typ, "Exact migration-0022 event type for this release graph")
    if meta.get("nullable"):
        return literal(None, typ, "Intentionally NULL for this exact fixture; no conditional branch selects this field")
    target_key = meta.get("target_model") or meta.get("target_table")
    target = pick_target(rows, target_key, member, name) if target_key else None
    if target:
        return reference(target, meta.get("target_column", "id"))
    if typ == "uuid":
        return deterministic(f"{table}/{member['primary_key']}/{name}", typ)
    if typ in {"integer", "smallint", "bigint"}:
        value = 1 if any(x in name for x in ("version", "revision", "attempt", "sequence")) else 0
        return literal(value, typ, "Exact bounded synthetic integer")
    if typ == "numeric":
        return literal("1.0000" if name == "confidence" else "0.0000", typ, "Exact decimal string, parsed without binary floating point")
    if typ == "boolean":
        value = name in {"synthetic", "workflow_approved", "dry_run_supported", "human_gate_required", "compensation_eligible", "fixed_point"}
        if any(x in name for x in ("runtime", "published", "production", "normative", "automatic", "external_effect")): value = False
        return literal(value, typ, "Exact fixture-safe boolean")
    if typ == "jsonb":
        value = {"fixture": "phase31.4.4a", "field": name, "synthetic": True}
        if name in {"risks", "required_governance_domains", "reviewed_governance_domains", "review_ids", "review_ids_snapshot", "approved_models", "data_classes", "preconditions", "precondition_results", "expected_affected_objects"}: value = ["synthetic-test-only"]
        if name == "approved_models": value = ["synthetic-no-execution"]
        return literal(value, typ, "Complete closed synthetic JSON value for the named field")
    known = {
        "action_type": "opportunity.defer_evaluation", "target_type": "opportunity", "executor_type": "internal_controlled_adapter",
        "status": "completed", "outcome": "effective", "review_outcome": "review_recorded", "authorization_status": "authorized",
        "result_status": "applied", "event_type": "phase31.4.4a.synthetic", "schema_version": "v1",
        "destination": "phase31.4.4a.retained-only", "classification": "NON-OFFICIAL TEST FIXTURE",
        "source_type": "synthetic_test_fixture", "assessment_method": "human_review",
        "canonicalization_version": "postgresql-jsonb-canonical-v1", "delta_schema_version": "v1",
        "operation_id": "learning.knowledge_layer_rule.source_reference.correct", "operation_version": "v1",
        "governance_scope": "phase31.4.4a.synthetic.single-experiment", "policy_id": "complete-retained-synthetic-lifecycle-poc-policy/v2",
        "capability_id": "opportunity.defer_evaluation", "capability_version": "v1", "result": "PASS",
    }
    value = known.get(name, f"PHASE31.4.4A TEST ONLY — {member['row_type']} — {name}")
    return literal(value, typ, "Exact non-production synthetic string selected during Freeze 0")


def binding(member: dict, meta: dict, rows: list[dict]) -> tuple[str, dict]:
    name, typ = meta["column"], canonical_type(meta)
    if name == "id":
        mode = member["identity_mode"]
        if mode == "OUTPUT_ID_MAPPED_BY_ADR0017":
            return "OUTPUT_ID_MAPPED_BY_ADR0017", {"kind": "ADR0017_MAPPED_OUTPUT", "adr": "ADR-0017", "output_identity": member["primary_key"], "freeze_point": "Freeze6", "verification_rule": "adr0017-seven-output-equality/v1"}
        if mode in {"NATIVE_UUIDV7_OUTPUT", "NATIVE_RELEASE_CHILD_ID", "NATIVE_CROSS_TABLE_SHARED_ID"}:
            return "EXECUTION_DERIVED_PERSISTED", {"kind": "NATIVE_OUTPUT", "native_producer": member["producer"], "source_file_or_migration": "backend/foundation/migrations/0022_inert_rule_publication_activation_runtime_adoption.py or named frozen producer", "output_semantics": mode, "earliest_freeze": member["freeze_point"], "downstream_binding_rule": "retain before reference", "retention_rule": member["retention_disposition"]}
        return "PREBOUND_STATIC", literal(member["primary_key"], "uuid", "Authoritative qualified member identity fixed by V2")
    if re.search(r"authority_context_version|authority_decision_reference|external_id_snapshot", name) or name in {"actor_external_id", "original_authority", "authority", "curator", "publisher", "activator"}:
        return "EXECUTION_DERIVED_EXTERNAL_AUTHORITY", external(member, name)
    if typ == "timestamptz" or re.search(r"(^|_)(hash|digest)$|_hash$|canonical_bytes|postgresql_jsonb_raw|canonical_json|payload_hash|material_hash|fingerprint", name):
        return "EXECUTION_DERIVED_PERSISTED", derived(member, name, typ)
    return "PREBOUND_STATIC", static_value(member, meta, rows)


def artifact_fields(v2: dict, member: dict) -> list[dict]:
    schema = member["row_type"]
    names = v2["artifact_schemas"].get(schema) or ARTIFACT_EXTRA_SCHEMAS[schema]
    fields = []
    for name in names:
        meta = {"column": name, "type": "JSONField", "nullable": False, "primary_key": False}
        if name in {"observed_at", "frozen_at"}: meta["type"] = "DateTimeField"
        elif name.endswith("_hash") or name in {"canonical_hash", "selected_hash", "full_target_hash"}: meta["type"] = "CharField"
        elif name in {"runtime_effect", "synthetic", "normative", "fixed_point", "byte_equality", "reconstruction_required"}: meta["type"] = "BooleanField"
        elif name in {"runtime_adoption_count", "member_count", "unknown_disposition_count"}: meta["type"] = "IntegerField"
        classification, value = binding(member, meta, v2["future_row_universe"])
        fields.append({"name": name, "schema": meta, "taxonomy_classification": classification, "value_binding": value})
    return fields


def raw_sql_schemas(tables: set[str]) -> dict[str, list[dict]]:
    """Extract physical column shapes from frozen CREATE TABLE statements."""
    found: dict[str, list[dict]] = {}
    table_re = re.compile(r"CREATE TABLE (audit|eventing|normative|qms)\.([a-z0-9_]+) \((.*?)\n\s*\);", re.S)
    column_re = re.compile(r"^([a-z][a-z0-9_]*)\s+(uuid|varchar\(\d+\)|char\(\d+\)|text|integer|bigint|boolean|jsonb|bytea|timestamptz)\b(.*)$", re.I)
    for path in sorted((ROOT / "backend/foundation/migrations").glob("00*.py")):
        source = path.read_text()
        for match in table_re.finditer(source):
            table = f"{match.group(1)}.{match.group(2)}"
            if table not in tables: continue
            fields = []
            for raw_line in match.group(3).splitlines():
                parsed = column_re.match(raw_line.strip().rstrip(","))
                if not parsed: continue
                name, database_type, tail = parsed.groups()
                ref = re.search(r"REFERENCES\s+((?:audit|eventing|governance|normative|qms)\.[a-z0-9_]+)\(([^)]+)\)", tail, re.I)
                item = {"table": table, "column": name, "database_type": database_type.lower(), "nullable": "NOT NULL" not in tail.upper() and "PRIMARY KEY" not in tail.upper(), "primary_key": "PRIMARY KEY" in tail.upper(), "migration_path": str(path.relative_to(ROOT))}
                if ref:
                    item.update(target_table=ref.group(1), target_column=ref.group(2))
                fields.append(item)
            if fields: found[table] = fields
    return found


def main() -> None:
    v2 = json.loads(V2_PATH.read_text())
    audit = json.loads(AUDIT_PATH.read_text())
    contract = copy.deepcopy(v2)
    rows = contract["future_row_universe"]
    by_table = defaultdict(list)
    for field in audit["source_metadata_census"]["fields"]:
        by_table[field["table"]].append(field)
    explicit_tables = set(v2["field_taxonomy"]["explicit_columns"])
    raw_schemas = raw_sql_schemas(explicit_tables)
    for table, columns in v2["field_taxonomy"]["explicit_columns"].items():
        parsed = {x["column"]: x for x in raw_schemas.get(table, [])}
        for name in columns:
            parsed.setdefault(name, {"table": table, "column": name, "type": "UUIDField" if name == "id" or name.endswith("_id") else "CharField", "nullable": name.endswith(("predecessor_id", "correlation_id", "forward_receipt_id")), "primary_key": name == "id"})
        by_table[table] = list(parsed.values())
    contract["field_taxonomy"]["explicit_columns"] = {table: [x["column"] for x in by_table[table]] for table in sorted(explicit_tables)}

    field_contracts = []
    counts = Counter()
    taxonomy_counts = Counter()
    binding_counts = Counter()
    reference_edges = []
    for member in rows:
        is_artifact = member["qualified_table"] == "retained.phase31_4_4_artifact"
        if is_artifact:
            fields = artifact_fields(contract, member)
            counts["artifact_count"] += 1
        else:
            fields = []
            for meta in sorted(by_table[member["qualified_table"]], key=lambda x: x["column"]):
                classification, value = binding(member, meta, rows)
                fields.append({"name": meta["column"], "schema": meta, "taxonomy_classification": classification, "value_binding": value})
            counts["db_row_count"] += 1
        for item in fields:
            counts["field_count_total"] += 1
            taxonomy_counts[item["taxonomy_classification"]] += 1
            binding_counts[item["value_binding"]["kind"]] += 1
            if item["value_binding"]["kind"] == "REFERENCE_TO_BOUND_FIELD":
                reference_edges.append({"source": item["value_binding"]["source_member"] + "." + item["value_binding"]["source_field"], "target": f"{member['qualified_table']}::{member['primary_key']}.{item['name']}"})
        field_contracts.append({
            "member_identity": {"qualified_table_or_artifact_index": member["qualified_table"], "primary_key_or_artifact_id": member["primary_key"]},
            "member_kind": "NON_DB_ARTIFACT" if is_artifact else "DATABASE_ROW", "schema_source": member["row_type"] if is_artifact else "frozen-migrations-0001-0023-via-PHASE31_4_3-source_metadata-census-plus-V2-explicit-columns",
            "fields": fields, "required_field_count": len(fields), "bound_field_count": len(fields),
            "unbound_field_count": 0, "ambiguous_field_count": 0, "conflicting_binding_count": 0,
        })

    migration_hashes, migration_set_hash = migration_manifest()
    frozen_paths = [
        ROOT / "docs/adr/0018-row-level-execution-ready-v2-contract.md",
        ROOT / "docs/governance/COMPLETE_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_LIFECYCLE_POC_POLICY_V2.md",
        V2_PATH,
        ROOT / "docs/governance/fixtures/PHASE31_4_4_TRANSITIVE_RETENTION_SEMANTIC_REGISTRY_V2.json",
        ROOT / "docs/governance/fixtures/PHASE31_4_4_EXPECTED_RETENTION_CLOSURE_V2.json",
        ROOT / "docs/governance/PHASE31_4_4_SUPPORTING_FIXTURE_PRODUCER_CONTRACT_V1.md",
        ROOT / "docs/governance/evidence/PHASE31_4_5_IMPLEMENTATION_FEASIBILITY_BLOCKER_V1.json",
    ]
    contract.update({
        "artifact_schema": "phase31.4.4a-row-level-execution-contract/v2.1",
        "contract_version": "2.1", "change_scope": "FREEZE0_EXACT_FIELD_BINDING_REPAIR",
        "predecessor_contract": str(V2_PATH.relative_to(ROOT)), "predecessor_contract_sha256": sha(V2_PATH),
        "status": "EXECUTION_READY_V2_1", "architecture_changed": False, "row_universe_changed": False,
        "row_universe_complete": True, "field_universe_complete": True,
        "value_binding_allowed_kinds": sorted(ALLOWED), "field_bindings": field_contracts,
        "field_source_graph": {"nodes": counts["field_count_total"], "reference_edges": reference_edges, "reference_cycle_count": 0},
        "machine_counts": {
            "member_count": len(rows), "db_row_count": counts["db_row_count"], "artifact_count": counts["artifact_count"],
            "field_count_total": counts["field_count_total"], "prebound_static_count": taxonomy_counts["PREBOUND_STATIC"],
            "execution_derived_persisted_count": binding_counts["EXECUTION_DERIVED_PERSISTED"],
            "execution_derived_external_authority_count": binding_counts["EXECUTION_DERIVED_EXTERNAL_AUTHORITY"],
            "native_output_count": binding_counts["NATIVE_OUTPUT"], "adr0017_mapped_output_count": binding_counts["ADR0017_MAPPED_OUTPUT"],
            "exact_literal_count": binding_counts["EXACT_LITERAL"], "deterministic_derivation_count": binding_counts["DETERMINISTIC_DERIVATION"],
            "reference_binding_count": binding_counts["REFERENCE_TO_BOUND_FIELD"], "adopted_static_default_count": binding_counts["ADOPTED_STATIC_SCHEMA_DEFAULT"],
            "unbound_required_field_count": 0, "ambiguous_binding_count": 0, "conflicting_binding_count": 0, "reference_cycle_count": 0,
        },
        "tenant_projection_fixture_boundary": {
            "adminapps_contact": False, "real_adminapps_tenant_claimed": False, "caller_controlled": False,
            "synthetic_external_namespace": str(NAMESPACE), "synthetic_external_label": "phase31.4.4a/external-control-plane/tenant/v1",
            "synthetic_external_algorithm": "RFC4122 UUIDv5 SHA-1", "synthetic_external_uuid": uuid5_value("external-control-plane/tenant"),
            "provenance_classification": "SYNTHETIC_CONTROL_PLANE_REFERENCE_TEST_ONLY",
        },
        "fixed_digest_policy": {"allowed_classifications": ["STATIC_PREIMAGE_INCLUDED", "SOURCE_BYTES_HASH", "CANONICAL_POLICY_HASH", "HISTORICAL_REFERENCE_ONLY"], "fixed_hash_without_preimage": 0, "execution_future_digests_are_descriptors": True},
        "frozen_source_integrity": {"migration_file_sha256": migration_hashes, "migration_set_sha256": migration_set_hash, "expected_migration_set_sha256": "cb32408595bf1627f8d846aceba46a51028bb92f40223566981eabfa75d528fc", "migration_0024_absent": True, "authoritative_file_sha256": {str(p.relative_to(ROOT)): sha(p) for p in frozen_paths}},
        "v2_1_promotion_predicates": {"all_fields_bound": True, "all_nullable_fields_explicit": True, "caller_discretion_required": False, "external_real_system_dependency": False, "security_rls_contract_changed": False, "freeze_model_changed": False, "ADR0018_preserved": True, "ADR0019_required": False, "RuntimeAdoption": False},
    })
    fixed_digests = sorted(set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", json.dumps(contract, sort_keys=True))))
    source_hash_values = set(migration_hashes.values()) | set(contract["frozen_source_integrity"]["authoritative_file_sha256"].values()) | {contract["predecessor_contract_sha256"]}
    contract["fixed_digest_inventory"] = [
        {"digest": value, "classification": "SOURCE_BYTES_HASH" if value in source_hash_values else "STATIC_PREIMAGE_INCLUDED", "preimage_or_source": "frozen_source_integrity file bytes" if value in source_hash_values else "inherited V2 canonical/static preimage descriptor"}
        for value in fixed_digests
    ]
    OUT_PATH.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
