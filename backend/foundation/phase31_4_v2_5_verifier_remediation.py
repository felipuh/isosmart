"""Fail-closed evidence primitives for the Phase 31.4 V2.5 verifier.

This module records what a disposable execution actually did.  It is a
governance boundary, not a replacement for the domain services.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping


ALLOWED_PHASE_STATUSES = {"PASS", "FAIL", "SKIPPED_NOT_APPLICABLE"}
EVIDENCE_SCHEMA_VERSION = "phase31.4-v2.5-phase-evidence/v1"
CAPTURE_READBACK_SCHEMA_VERSION = "phase31.4-v2.5-capture-readback/v1"
LIVE_CAPTURE_CATEGORIES = {
    "LIVE_UPSTREAM_NATIVE_CAPTURE",
    "CAPTURE_NATIVE_OUTPUT",
    "REFERENCE_RESOLVED_BINDING",
    "DETERMINISTIC_DERIVATION",
    "EXACT_LITERAL",
    "DERIVED_RUNTIME_INVARIANT",
}
PROVENANCE_KINDS = {
    "ADMINAPPS_EXTERNAL_TENANT",
    "ADMINAPPS_EXTERNAL_ACTOR",
    "TENANT_PROJECTION_READBACK",
    "USER_PROJECTION_READBACK",
    "QMS_NATIVE_ORGANIZATION",
    "QMS_NATIVE_PROCESS",
    "SYNTHETIC_HARNESS",
}


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "hex") and not isinstance(value, (str, bytes)):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    return value


def canonical_hash(value: Any) -> str:
    payload = json.dumps(_json_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PhaseContract:
    phase_id: str
    phase_name: str
    claimed_guarantee: str
    required_assertions: tuple[str, ...]
    required_evidence_types: tuple[str, ...]
    mandatory: bool = True
    executor: str | None = None

    def validate_registration(self) -> None:
        missing = []
        if not self.executor:
            missing.append("executor")
        if not self.claimed_guarantee:
            missing.append("claimed_guarantee")
        if self.mandatory and not self.required_assertions:
            missing.append("required_assertions")
        if self.mandatory and not self.required_evidence_types:
            missing.append("required_evidence_types")
        if missing:
            raise ValueError(f"invalid phase registration {self.phase_id}: {', '.join(missing)}")


@dataclass(frozen=True)
class PhaseExecutionResult:
    phase_id: str
    phase_name: str
    status: str
    executor: str
    native_source: str | None = None
    operation: str | None = None
    inputs_hash: str | None = None
    output_ids: tuple[str, ...] = ()
    readback_ids: tuple[str, ...] = ()
    assertions: tuple[dict[str, Any], ...] = ()
    evidence_artifacts: tuple[str, ...] = ()
    evidence_hashes: tuple[str, ...] = ()
    provenance: tuple[dict[str, Any], ...] = ()
    error: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str | None = None

    def validate(self, contract: PhaseContract) -> None:
        contract.validate_registration()
        if self.phase_id != contract.phase_id:
            raise ValueError(f"phase result mismatch: {self.phase_id} != {contract.phase_id}")
        if self.status not in ALLOWED_PHASE_STATUSES:
            raise ValueError(f"invalid phase status: {self.status}")
        if self.status == "PASS":
            if not self.executor or not self.operation:
                raise ValueError(f"PASS phase lacks executor or operation: {self.phase_id}")
            assertion_names = {item.get("name") for item in self.assertions if item.get("passed") is True}
            missing_assertions = set(contract.required_assertions) - assertion_names
            missing_evidence = set(contract.required_evidence_types) - set(self.evidence_artifacts)
            if missing_assertions:
                raise ValueError(f"PASS phase missing assertions: {sorted(missing_assertions)}")
            if missing_evidence:
                raise ValueError(f"PASS phase missing evidence: {sorted(missing_evidence)}")
            if not self.inputs_hash:
                raise ValueError(f"PASS phase missing inputs hash: {self.phase_id}")
            if not self.completed_at:
                raise ValueError(f"PASS phase missing completion time: {self.phase_id}")
            if any(item.get("resolved") is False for item in self.provenance):
                raise ValueError(f"PASS phase has unresolved provenance: {self.phase_id}")

    def to_dict(self) -> dict[str, Any]:
        return _json_value(asdict(self))


@dataclass(frozen=True)
class LiveCapture:
    capture_key: str
    category: str
    phase_id: str
    retry_id: str
    source_service: str
    source_operation: str
    value: Any
    expected_type: str
    persisted_readback: Any
    readback_source: str
    equality_verified: bool
    provenance: dict[str, Any]
    captured_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def validate(self) -> None:
        if self.category not in LIVE_CAPTURE_CATEGORIES:
            raise ValueError(f"unsupported capture category: {self.category}")
        if not self.capture_key or not self.phase_id or not self.retry_id:
            raise ValueError("capture identity is incomplete")
        if self.category == "CAPTURE_NATIVE_OUTPUT" and not self.equality_verified:
            raise ValueError(f"native capture/readback mismatch: {self.capture_key}")
        if self.category in {"LIVE_UPSTREAM_NATIVE_CAPTURE", "CAPTURE_NATIVE_OUTPUT"} and not self.readback_source:
            raise ValueError(f"live capture lacks readback source: {self.capture_key}")
        if self.provenance.get("kind") not in PROVENANCE_KINDS:
            raise ValueError(f"invalid capture provenance: {self.capture_key}")
        if self.provenance.get("synthetic") and self.category == "LIVE_UPSTREAM_NATIVE_CAPTURE":
            raise ValueError(f"synthetic value labeled live upstream: {self.capture_key}")
        if isinstance(self.value, str) and self.value.startswith("captured:"):
            raise ValueError(f"placeholder capture rejected: {self.capture_key}")

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return _json_value(asdict(self))


def reject_placeholders(value: Any) -> None:
    if isinstance(value, str) and (value.startswith("captured:") or value.startswith("fixture:")):
        raise ValueError(f"offline placeholder rejected: {value}")
    if isinstance(value, Mapping):
        for item in value.values():
            reject_placeholders(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            reject_placeholders(item)


def materialize_resolved_graph(contract: Mapping[str, Any], captures: Iterable[LiveCapture]) -> dict[str, Any]:
    capture_map = {capture.capture_key: capture for capture in captures}
    for capture in capture_map.values():
        capture.validate()
    graph = {"members": []}
    for member in contract.get("members", contract.get("field_bindings", [])):
        identity = member.get("member_identity", member.get("identity", {}))
        member_key = f"{identity.get('qualified_table_or_artifact_index', identity.get('table', ''))}::{identity.get('primary_key_or_artifact_id', identity.get('id', ''))}"
        fields = {}
        for field_spec in member.get("fields", []):
            name = field_spec["name"]
            binding = field_spec.get("value_binding", field_spec.get("binding", {}))
            key = f"{member_key}.{name}"
            kind = binding.get("kind")
            if kind in {"CAPTURE_NATIVE_OUTPUT", "LIVE_UPSTREAM_NATIVE_CAPTURE"}:
                capture = capture_map.get(key)
                if capture is None:
                    raise ValueError(f"missing live capture: {key}")
                value = capture.value
            elif kind == "EXACT_LITERAL":
                value = binding.get("typed_value")
            elif kind == "DETERMINISTIC_DERIVATION":
                value = binding.get("expected_output")
            elif kind == "REFERENCE_RESOLVED_BINDING":
                source = f"{binding['source_member']}.{binding['source_field']}"
                source_capture = capture_map.get(source)
                if source_capture is None:
                    raise ValueError(f"unresolved live reference: {key} -> {source}")
                value = source_capture.value
            elif kind == "DERIVED_RUNTIME_INVARIANT":
                raise ValueError(f"runtime invariant requires an explicit derivation: {key}")
            else:
                raise ValueError(f"unsupported graph binding: {key}:{kind}")
            reject_placeholders(value)
            fields[name] = value
        graph["members"].append({"member": member_key, "fields": fields})
    reject_placeholders(graph)
    graph["member_count"] = len(graph["members"])
    graph["field_count"] = sum(len(item["fields"]) for item in graph["members"])
    return graph


def exact_compare(expected: Mapping[str, Any], actual: Mapping[str, Any]) -> dict[str, Any]:
    expected_members = {item["member"]: item for item in expected.get("members", [])}
    actual_members = {item["member"]: item for item in actual.get("members", [])}
    missing_members = sorted(set(expected_members) - set(actual_members))
    extra_members = sorted(set(actual_members) - set(expected_members))
    missing_fields: list[str] = []
    extra_fields: list[str] = []
    type_mismatches: list[str] = []
    value_mismatches: list[str] = []
    reference_mismatches: list[str] = []
    invariant_mismatches: list[str] = []
    for member in sorted(set(expected_members) & set(actual_members)):
        expected_fields = expected_members[member].get("fields", {})
        actual_fields = actual_members[member].get("fields", {})
        missing_fields.extend(f"{member}.{name}" for name in sorted(set(expected_fields) - set(actual_fields)))
        extra_fields.extend(f"{member}.{name}" for name in sorted(set(actual_fields) - set(expected_fields)))
        for name in sorted(set(expected_fields) & set(actual_fields)):
            path = f"{member}.{name}"
            if type(expected_fields[name]) is not type(actual_fields[name]):
                type_mismatches.append(path)
            elif expected_fields[name] != actual_fields[name]:
                value_mismatches.append(path)
    total = sum(map(len, (missing_members, extra_members, missing_fields, extra_fields, type_mismatches, value_mismatches, reference_mismatches, invariant_mismatches)))
    return {
        "expected_members": len(expected_members), "actual_members": len(actual_members),
        "missing_members": missing_members, "extra_members": extra_members,
        "expected_fields": sum(len(item.get("fields", {})) for item in expected_members.values()),
        "actual_fields": sum(len(item.get("fields", {})) for item in actual_members.values()),
        "missing_fields": missing_fields, "extra_fields": extra_fields,
        "type_mismatches": type_mismatches, "value_mismatches": value_mismatches,
        "reference_mismatches": reference_mismatches, "invariant_mismatches": invariant_mismatches,
        "total_mismatches": total, "status": "PASS" if total == 0 else "FAIL",
        "live_graph_sha256": canonical_hash(actual),
    }


class AppendOnlyEvidenceStore:
    def __init__(self, root: str | Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._finalized = (self.root / "12_sha256.json").exists()

    def write(self, name: str, payload: Any) -> Path:
        if self._finalized:
            raise RuntimeError("evidence retry is finalized and immutable")
        path = self.root / name
        if path.exists():
            raise FileExistsError(f"evidence artifact already exists: {path}")
        path.write_text(json.dumps(_json_value(payload), indent=2, sort_keys=True) + "\n")
        return path

    def finalize(self) -> Path:
        if self._finalized:
            raise RuntimeError("evidence retry is already finalized")
        manifest = {
            path.name: sha256(path.read_bytes()).hexdigest()
            for path in sorted(self.root.iterdir()) if path.is_file()
        }
        path = self.root / "12_sha256.json"
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        self._finalized = True
        return path


def verify_event_outbox_audit(rows: Mapping[str, Iterable[Mapping[str, Any]]], *, aggregate_id: str, trace_id: str, payload_hash: str) -> dict[str, Any]:
    result = {}
    for name in ("domain_events", "transactional_outbox", "immutable_audit_log"):
        candidates = [row for row in rows.get(name, ()) if str(row.get("aggregate_id")) == str(aggregate_id) and row.get("trace_id") == trace_id]
        result[name] = {"count": len(candidates), "payload_hash_match": any(row.get("payload_hash") == payload_hash for row in candidates)}
    missing = [name for name, item in result.items() if item["count"] == 0 or not item["payload_hash_match"]]
    return {"records": result, "missing": missing, "status": "PASS" if not missing else "FAIL"}


def verify_security_probe(probe: Mapping[str, Any]) -> dict[str, Any]:
    required = ("principal", "tenant", "operation", "expected_result", "observed_result", "db_role", "status")
    missing = [name for name in required if name not in probe]
    if missing:
        raise ValueError(f"security probe missing fields: {missing}")
    passed = probe["expected_result"] == probe["observed_result"] and probe["status"] == "PASS"
    return {**dict(probe), "status": "PASS" if passed else "FAIL"}


def verify_post_teardown(*, teardown_completed: bool, observed_absence: Mapping[str, bool]) -> dict[str, Any]:
    if not teardown_completed:
        raise ValueError("post-teardown verification requires completed teardown")
    required = ("containers", "networks", "volumes", "db_reachability", "allocated_ports")
    missing = [name for name in required if name not in observed_absence]
    if missing:
        raise ValueError(f"post-teardown absence evidence missing: {missing}")
    absent = all(not observed_absence[name] for name in required)
    return {"observed_absence": dict(observed_absence), "status": "PASS" if absent else "FAIL"}
