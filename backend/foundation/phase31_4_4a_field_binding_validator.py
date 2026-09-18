"""Pure offline validator for the Phase 31.4.4A V2.1 field contract."""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4A_ROW_LEVEL_EXECUTION_CONTRACT_V2_1.json"
V2_PATH = ROOT / "docs/governance/fixtures/PHASE31_4_4_ROW_LEVEL_EXECUTION_CONTRACT_V2.json"
AUDIT_PATH = ROOT / "docs/governance/evidence/PHASE31_4_3_SUPPORTING_CONTRACT_AUDIT_V1.json"
ALLOWED = {
    "EXACT_LITERAL", "DETERMINISTIC_DERIVATION", "REFERENCE_TO_BOUND_FIELD",
    "ADOPTED_STATIC_SCHEMA_DEFAULT", "EXECUTION_DERIVED_PERSISTED",
    "EXECUTION_DERIVED_EXTERNAL_AUTHORITY", "NATIVE_OUTPUT", "ADR0017_MAPPED_OUTPUT",
}
STATIC_ALLOWED = {"EXACT_LITERAL", "DETERMINISTIC_DERIVATION", "REFERENCE_TO_BOUND_FIELD", "ADOPTED_STATIC_SCHEMA_DEFAULT"}
REQUIRED_BY_KIND = {
    "EXACT_LITERAL": {"typed_value", "database_type_or_schema_type", "canonical_representation", "provenance", "reason"},
    "DETERMINISTIC_DERIVATION": {"algorithm_id", "algorithm_version", "all_preimage_inputs", "input_types", "canonical_input_encoding", "output_type", "expected_output", "verification_rule"},
    "REFERENCE_TO_BOUND_FIELD": {"source_member", "source_field", "required_source_freeze", "copy_or_transform", "transform_algorithm_if_any"},
    "ADOPTED_STATIC_SCHEMA_DEFAULT": {"migration_path", "schema_object", "column", "exact_default_expression", "semantic_interpretation", "determinism_proof"},
    "EXECUTION_DERIVED_PERSISTED": {"producer", "producer_version", "source_state", "transaction_boundary", "freeze_point", "canonicalization", "downstream_consumers", "retention_rule", "verification_rule"},
    "EXECUTION_DERIVED_EXTERNAL_AUTHORITY": {"authority_contract", "actor", "permission", "scope", "MFA_requirement", "active_access_requirement", "policy_binding", "evaluation_point", "precommit_revalidation", "retained_provenance_schema"},
    "NATIVE_OUTPUT": {"native_producer", "source_file_or_migration", "output_semantics", "earliest_freeze", "downstream_binding_rule", "retention_rule"},
    "ADR0017_MAPPED_OUTPUT": {"adr", "output_identity", "freeze_point", "verification_rule"},
}
ARTIFACT_EXTRA_SCHEMAS = {
    "publication-closure-v2": ["artifact_schema", "experiment_id", "scope", "member_keys", "member_hashes", "fixed_point", "unknown_disposition_count", "canonicalization", "observed_at", "canonical_hash"],
    "activation-closure-v2": ["artifact_schema", "experiment_id", "scope", "member_keys", "member_hashes", "fixed_point", "unknown_disposition_count", "canonicalization", "observed_at", "canonical_hash"],
    "expected-retention-closure/v2": ["artifact_schema", "experiment_id", "member_keys", "member_count", "fixed_point", "unknown_disposition_count", "canonicalization", "observed_at", "canonical_hash"],
}
ENUMS = {
    ("qms.tenant_projection", "lifecycle_status"): {"pending", "active", "suspended", "deprovisioning", "deleted_tombstone", "drifted", "unknown"},
    ("qms.tenant_projection", "provisioning_status"): {"pending", "partial", "complete", "failed"},
    ("qms.tenant_projection", "reconciliation_status"): {"in_sync", "stale", "missing_local", "unexpected_local", "version_conflict", "authority_unavailable"},
    ("normative.standard_edition", "status"): {"draft", "published"},
    ("normative.knowledge_layer", "certifiability_classification"): {"non_certifiable_guidance"},
    ("normative.knowledge_layer_rule", "certifiability_classification"): {"non_certifiable_guidance"},
    ("normative.knowledge_layer_rule", "status"): {"draft", "published"},
    ("governance.model_policy", "status"): {"draft", "published"},
    ("governance.agent_definition", "status"): {"draft", "published"},
    ("qms.recommendation", "status"): {"proposed"},
    ("qms.action_plan", "impact"): {"standard", "high"},
    ("qms.action_plan", "reversibility"): {"reversible", "irreversible"},
    ("qms.approval", "decision"): {"approve", "reject", "request_changes"},
    ("qms.execution_authorization", "impact"): {"standard", "high"},
    ("qms.execution_authorization", "outcome"): {"authorized"},
    ("qms.execution_authorization", "reversibility"): {"reversible", "irreversible"},
    ("qms.action_execution", "executor_type"): {"controlled_opportunity", "synthetic_noop"},
    ("qms.action_execution", "status"): {"running", "succeeded", "failed"},
    ("qms.action_execution_receipt", "executor_type"): {"controlled_opportunity", "synthetic_noop"},
    ("qms.action_execution_receipt", "outcome"): {"opportunity_deferred", "opportunity_evaluation_resumed", "synthetic_noop_succeeded", "synthetic_noop_failed"},
    ("qms.learning_signal", "selected_outcome_snapshot"): {"effective", "ineffective", "inconclusive", "unknown"},
    ("qms.learning_signal_effectiveness", "outcome_snapshot"): {"effective", "ineffective", "inconclusive", "unknown"},
    ("eventing.transactional_outbox", "status"): {"pending", "processing", "published", "failed"},
    ("qms.learning_proposal", "status"): {"governance_pending"},
    ("qms.learning_proposal_review", "target_status_snapshot"): {"valid", "stale"},
    ("qms.learning_proposal_review", "review_outcome"): {"review_recorded"},
    ("qms.learning_proposal_decision", "outcome"): {"approved_for_application", "changes_requested", "rejected"},
    ("qms.learning_application_authorization", "authorization_status"): {"authorized"},
    ("normative.knowledge_layer_rule_governance_claim", "operation_kind"): {"PUBLICATION", "ACTIVATION"},
    ("normative.knowledge_layer_rule_governance_event", "operation_kind"): {"PUBLICATION", "ACTIVATION"},
    ("audit.knowledge_layer_rule_governance_audit", "operation_kind"): {"PUBLICATION", "ACTIVATION"},
    ("eventing.knowledge_layer_rule_governance_outbox", "status"): {"pending"},
    ("eventing.platform_transactional_outbox", "status"): {"pending"},
    ("normative.knowledge_layer_rule_publication", "evidence_kind"): {"NATIVE", "LEGACY_EVIDENCE_IMPORT"},
}


def load_contract(path: Path = CONTRACT_PATH) -> dict:
    return json.loads(path.read_text())


def _expected_fields(contract: dict) -> dict[tuple[str, str], set[str]]:
    audit = json.loads(AUDIT_PATH.read_text())
    by_table: dict[str, set[str]] = defaultdict(set)
    for field in audit["source_metadata_census"]["fields"]:
        by_table[field["table"]].add(field["column"])
    for table, columns in contract["field_taxonomy"]["explicit_columns"].items():
        if table not in by_table:
            by_table[table].update(columns)
    expected = {}
    for row in contract["future_row_universe"]:
        key = (row["qualified_table"], row["primary_key"])
        if row["qualified_table"] == "retained.phase31_4_4_artifact":
            expected[key] = set(contract["artifact_schemas"].get(row["row_type"]) or ARTIFACT_EXTRA_SCHEMAS[row["row_type"]])
        else:
            expected[key] = by_table[row["qualified_table"]]
    return expected


def validate(contract: dict) -> list[str]:
    errors: list[str] = []
    v2 = json.loads(V2_PATH.read_text())
    v2_ids = [(r["qualified_table"], r["primary_key"]) for r in v2["future_row_universe"]]
    ids = [(r.get("qualified_table"), r.get("primary_key")) for r in contract.get("future_row_universe", [])]
    if ids != v2_ids: errors.append("row universe/table/primary-key/order drift")
    frozen_row_keys = ("producer", "identity_mode", "freeze_point", "transaction_boundary", "tenant_or_global_scope", "RLS_contract")
    for old, new in zip(v2["future_row_universe"], contract.get("future_row_universe", [])):
        if any(old.get(k) != new.get(k) for k in frozen_row_keys): errors.append(f"producer/identity/freeze/security drift {(old['qualified_table'], old['primary_key'])}")
    if contract.get("security_rls_matrix") != v2.get("security_rls_matrix"): errors.append("security matrix drift")
    if contract.get("freeze_order") != v2.get("freeze_order"): errors.append("freeze order drift")
    if contract.get("identity_contract") != v2.get("identity_contract"): errors.append("ADR0017 or identity scope drift")
    if len(ids) != 118 or len(set(ids)) != 118: errors.append("member count or qualified identity uniqueness failure")
    if contract.get("predecessor_contract_sha256") != hashlib.sha256(V2_PATH.read_bytes()).hexdigest(): errors.append("predecessor hash drift")
    if contract.get("architecture_changed") is not False or contract.get("row_universe_changed") is not False: errors.append("architecture or row universe changed")

    expected = _expected_fields(contract)
    contracts = contract.get("field_bindings", [])
    by_member = {}
    graph: dict[str, set[str]] = defaultdict(set)
    all_fields: set[str] = set()
    for member in contracts:
        ident = member.get("member_identity", {})
        key = (ident.get("qualified_table_or_artifact_index"), ident.get("primary_key_or_artifact_id"))
        if key in by_member: errors.append(f"duplicate field contract {key}")
        by_member[key] = member
        names = [f.get("name") for f in member.get("fields", [])]
        if set(names) != expected.get(key, set()): errors.append(f"schema field mismatch {key}")
        if len(names) != len(set(names)): errors.append(f"multiple bindings {key}")
        if member.get("required_field_count") != len(names) or member.get("bound_field_count") != len(names): errors.append(f"bad member counts {key}")
        if any(member.get(x) != 0 for x in ("unbound_field_count", "ambiguous_field_count", "conflicting_binding_count")): errors.append(f"nonzero defect count {key}")
        for field in member.get("fields", []):
            node = f"{key[0]}::{key[1]}.{field.get('name')}"
            all_fields.add(node)
            value = field.get("value_binding")
            if not isinstance(value, dict): errors.append(f"missing binding {node}"); continue
            kind = value.get("kind")
            if kind not in ALLOWED: errors.append(f"invalid binding kind {node}"); continue
            if not REQUIRED_BY_KIND[kind] <= value.keys(): errors.append(f"incomplete {kind} binding {node}")
            if field.get("taxonomy_classification") == "PREBOUND_STATIC" and kind not in STATIC_ALLOWED: errors.append(f"dynamic PREBOUND_STATIC {node}")
            if kind == "EXACT_LITERAL" and isinstance(value.get("typed_value"), str) and re.search(r"<synthetic>|fixture value|generated later|\b(TBD|UNKNOWN|AUTO|FRESH|RUNTIME_VALUE)\b", value["typed_value"], re.I): errors.append(f"placeholder literal {node}")
            allowed_values = ENUMS.get((key[0], field.get("name")))
            if kind == "EXACT_LITERAL" and allowed_values and value.get("typed_value") not in allowed_values: errors.append(f"invalid enum/check literal {node}")
            if kind == "DETERMINISTIC_DERIVATION" and (not value.get("all_preimage_inputs") or not value.get("expected_output")): errors.append(f"missing deterministic preimage {node}")
            if kind == "ADOPTED_STATIC_SCHEMA_DEFAULT" and re.search(r"statement_timestamp|transaction_timestamp|uuidv7|random|nextval|current_setting", value.get("exact_default_expression", ""), re.I): errors.append(f"dynamic default adopted as static {node}")
            if kind == "REFERENCE_TO_BOUND_FIELD": graph[value["source_member"] + "." + value["source_field"]].add(node)

    if set(by_member) != set(v2_ids): errors.append("field contract membership drift")
    for source, targets in graph.items():
        if source not in all_fields: errors.append(f"unresolved reference {source}")
        if source in targets: errors.append(f"reference self-cycle {source}")
    visiting, visited = set(), set()
    def visit(node: str) -> bool:
        if node in visiting: return True
        if node in visited: return False
        visiting.add(node)
        if any(visit(n) for n in graph.get(node, ())): return True
        visiting.remove(node); visited.add(node); return False
    if any(visit(node) for node in list(graph) if node not in visited): errors.append("reference cycle")

    tenant_key = ("qms.tenant_projection", "daa6bb22-660c-56f5-aadf-c63f06b01731")
    tenant = {f["name"]: f["value_binding"].get("typed_value") for f in by_member.get(tenant_key, {}).get("fields", []) if isinstance(f.get("value_binding"), dict) and f["value_binding"].get("kind") == "EXACT_LITERAL"}
    required_tenant = {"adminapps_tenant_id", "source_version", "display_name_snapshot", "lifecycle_status", "provisioning_status", "reconciliation_status"}
    if not required_tenant <= tenant.keys(): errors.append("TenantProjection blocker fields missing")
    if tenant.get("lifecycle_status") not in {"pending", "active", "suspended", "deprovisioning", "deleted_tombstone", "drifted", "unknown"}: errors.append("invalid TenantProjection lifecycle_status")
    if tenant.get("provisioning_status") not in {"pending", "partial", "complete", "failed"}: errors.append("invalid TenantProjection provisioning_status")
    if tenant.get("reconciliation_status") not in {"in_sync", "stale", "missing_local", "unexpected_local", "version_conflict", "authority_unavailable"}: errors.append("invalid TenantProjection reconciliation_status")
    if not isinstance(tenant.get("source_version"), int) or tenant.get("source_version", -1) < 0: errors.append("invalid TenantProjection source_version")
    if contract.get("tenant_projection_fixture_boundary", {}).get("adminapps_contact") is not False: errors.append("real AdminApps dependency")
    if contract.get("tenant_projection_fixture_boundary", {}).get("caller_controlled") is not False: errors.append("caller-controlled tenant")
    if contract.get("v2_1_promotion_predicates", {}).get("RuntimeAdoption") is not False: errors.append("RuntimeAdoption enabled")
    if any(ROOT.glob("backend/foundation/migrations/0024*")): errors.append("migration 0024 appeared")
    integrity = contract.get("frozen_source_integrity", {})
    current_migrations = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in integrity.get("migration_file_sha256", {}) if (ROOT / name).is_file()}
    if current_migrations != integrity.get("migration_file_sha256"): errors.append("migration hash drift")
    aggregate = hashlib.sha256("".join(f"{name}\0{digest}\n" for name, digest in current_migrations.items()).encode()).hexdigest()
    if aggregate != integrity.get("migration_set_sha256") or aggregate != integrity.get("expected_migration_set_sha256"): errors.append("migration-set hash drift")
    current_sources = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in integrity.get("authoritative_file_sha256", {}) if (ROOT / name).is_file()}
    if current_sources != integrity.get("authoritative_file_sha256"): errors.append("authoritative source hash drift")
    serialized = json.dumps({k: v for k, v in contract.items() if k != "fixed_digest_inventory"}, sort_keys=True)
    fixed = set(re.findall(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])", serialized))
    inventory = contract.get("fixed_digest_inventory", [])
    if fixed != {x.get("digest") for x in inventory}: errors.append("fixed digest inventory mismatch")
    if any(x.get("classification") not in {"STATIC_PREIMAGE_INCLUDED", "SOURCE_BYTES_HASH", "CANONICAL_POLICY_HASH", "HISTORICAL_REFERENCE_ONLY"} or not x.get("preimage_or_source") for x in inventory): errors.append("fixed digest without classification/preimage")

    counts = contract.get("machine_counts", {})
    if counts.get("member_count") != 118 or counts.get("field_count_total") != sum(len(x["fields"]) for x in contracts): errors.append("global counts mismatch")
    for name in ("unbound_required_field_count", "ambiguous_binding_count", "conflicting_binding_count", "reference_cycle_count"):
        if counts.get(name) != 0: errors.append(f"nonzero {name}")
    return errors


if __name__ == "__main__":
    found = validate(load_contract())
    print(json.dumps({"status": "PASS" if not found else "FAIL", "errors": found}, indent=2))
    raise SystemExit(bool(found))
