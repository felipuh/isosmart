"""Fail-closed, filesystem-only PRECREATION_INTEGRITY operation.

The operation may retain governance evidence, but it never opens a database
connection or invokes a domain service.  It intentionally treats every
missing, malformed, stale, or unprotected input as a failure.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any

from .phase31_4_integrity_generations import (
    BASELINE_ADOPTION_MANIFEST,
    ROOT,
    V24_CONTRACT_SHA256,
    file_sha256,
    select_v25_current_baseline,
    verify_v24_historical_integrity,
)
from .phase31_4_v2_5_verifier_remediation import (
    CAPTURE_READBACK_SCHEMA_VERSION,
    EVIDENCE_SCHEMA_VERSION,
)


PHASE_ID = "PRECREATION_INTEGRITY"
OPERATION = "verify_precreation_integrity"
EXECUTOR = "PrecreationIntegrityExecutor"
CLAIMED_GUARANTEE = (
    "Pre-creation source, contract, authority and protected-material integrity "
    "are verified before any runtime domain effect is allowed."
)
PRECREATION_EVIDENCE_SCHEMA = "phase31.4-v2.5-precreation-integrity-evidence/v1"
CURRENT_CONTRACT = Path(
    "docs/governance/fixtures/PHASE31_4_5C_ROW_LEVEL_EXECUTION_CONTRACT_V2_5.json"
)
PROTECTED_VERIFIER_SOURCES = {
    "backend/foundation/phase31_4_v2_5_runtime.py",
    "backend/foundation/phase31_4_v2_5_verifier_remediation.py",
    "backend/foundation/phase31_4_v2_5_precreation_integrity.py",
}
REQUIRED_ASSERTIONS = (
    "current_source_integrity",
    "historical_v2_4_integrity",
    "protected_source_set",
    "migration_material_integrity",
    "contract_integrity",
    "verifier_integrity",
    "run_identity_uniqueness",
    "authority_configuration",
    "evidence_serialized",
)


class PrecreationIntegrityError(RuntimeError):
    pass


@dataclass(frozen=True)
class PrecreationIntegrityOutcome:
    status: str
    evidence_path: str | None
    evidence_sha256: str | None
    assertions: tuple[dict[str, Any], ...]
    error: str | None
    started_at: str
    completed_at: str
    details: dict[str, Any]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PrecreationIntegrityError(f"unreadable or malformed JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PrecreationIntegrityError(f"JSON artifact is not an object: {path}")
    return value


def _assertion(name: str, passed: bool, detail: Any) -> dict[str, Any]:
    return {"name": name, "passed": passed, "detail": detail}


def _safe_run_slug(run_id: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", run_id).strip("._")
    if not slug:
        raise PrecreationIntegrityError("run ID cannot be converted to an evidence identity")
    return slug


def _verify_contract(root: Path, current: dict[str, Any]) -> dict[str, Any]:
    path = root / CURRENT_CONTRACT
    contract = _load_object(path)
    entry = next(
        (item for item in current["sources"] if item.get("path") == CURRENT_CONTRACT.as_posix()),
        None,
    )
    if entry is None:
        raise PrecreationIntegrityError("authoritative V2.5 contract is not protected by current generation")
    observed = file_sha256(path)
    if observed != entry.get("sha256"):
        raise PrecreationIntegrityError("authoritative V2.5 contract hash mismatch")
    if contract.get("contract_version") != "2.5":
        raise PrecreationIntegrityError("authoritative contract has wrong generation")
    return {"status": "PASS", "path": CURRENT_CONTRACT.as_posix(), "sha256": observed}


def _verify_verifier(root: Path, current: dict[str, Any]) -> dict[str, Any]:
    protected = {item.get("path") for item in current["sources"]}
    missing = sorted(PROTECTED_VERIFIER_SOURCES - protected)
    if missing:
        raise PrecreationIntegrityError(f"verifier sources are not protected: {missing}")
    runtime = (root / "backend/foundation/phase31_4_v2_5_runtime.py").read_text(encoding="utf-8")
    verifier = (root / "backend/foundation/phase31_4_v2_5_verifier_remediation.py").read_text(encoding="utf-8")
    checks = {
        "no_default_pass": 'status: str = "FAIL"' in runtime,
        "phase_result_status_propagation": "record.status = result.status" in runtime,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION in verifier,
        "capture_readback_schema_version": CAPTURE_READBACK_SCHEMA_VERSION in verifier,
    }
    if not all(checks.values()):
        raise PrecreationIntegrityError(f"fail-closed verifier integrity mismatch: {checks}")
    return {
        "status": "PASS",
        "checks": checks,
        "evidence_schema_version": EVIDENCE_SCHEMA_VERSION,
        "capture_readback_schema_version": CAPTURE_READBACK_SCHEMA_VERSION,
    }


def _verify_authority_configuration(root: Path, contract: dict[str, Any]) -> dict[str, Any]:
    settings_source = (root / "backend/backend/settings.py").read_text(encoding="utf-8")
    checks = {
        "adminapps_isolated_endpoint_reference": "ADMIN_APPS_BASE_URL" in settings_source,
        "required_credential_reference": "ADMIN_APPS_API_KEY" in settings_source,
        "entitlement_requirement": "ISO_SMART_PRODUCT_CODE" in settings_source,
        "actor_source_contract": any(
            field.get("value_binding", {}).get("kind") == "LIVE_UPSTREAM_NATIVE_CAPTURE"
            and "user" in member.get("member_identity", {}).get("qualified_table_or_artifact_index", "")
            for member in contract.get("field_bindings", ())
            for field in member.get("fields", ())
        ),
    }
    if not all(checks.values()):
        raise PrecreationIntegrityError(f"authority configuration precondition failed: {checks}")
    return {
        "status": "PASS",
        "checks": checks,
        "live_authentication_claimed": False,
        "live_entitlement_claimed": False,
        "live_approver_authority_claimed": False,
    }


def verify_precreation_integrity(*, root: str | Path, run_id: str | None) -> PrecreationIntegrityOutcome:
    """Verify protected material and retain one exclusive, immutable evidence file."""
    started_at = _now()
    project_root = Path(root).resolve()
    assertions: list[dict[str, Any]] = []
    details: dict[str, Any] = {
        "phase_id": PHASE_ID,
        "executor": EXECUTOR,
        "operation": OPERATION,
        "claimed_guarantee": CLAIMED_GUARANTEE,
        "read_only_domain_operation": True,
    }
    evidence_directory: Path | None = None
    evidence_path: Path | None = None
    error: str | None = None
    try:
        if not run_id:
            raise PrecreationIntegrityError("run ID is required")
        if run_id in {"Phase 31.4 V2.5 Clean Retry 16", "Phase 31.4 V2.5 Clean Retry 17"}:
            raise PrecreationIntegrityError("run ID collides with Retry 16/17")
        evidence_directory = (
            project_root / "docs/governance/evidence/runs" / _safe_run_slug(run_id) / PHASE_ID
        )
        evidence_directory.mkdir(parents=True, exist_ok=False)
        evidence_path = evidence_directory / "precreation_integrity.json"
        assertions.append(_assertion("run_identity_uniqueness", True, {
            "run_id": run_id,
            "evidence_directory": evidence_directory.relative_to(project_root).as_posix(),
            "historical_evidence_overwrite": False,
        }))

        manifest_path, verified_current = select_v25_current_baseline(project_root)
        manifest_hash = file_sha256(manifest_path)
        details["current_integrity_artifact"] = {
            "path": manifest_path.relative_to(project_root).as_posix(), "sha256": manifest_hash,
        }
        adoption_path = project_root / BASELINE_ADOPTION_MANIFEST.relative_to(ROOT)
        details["baseline_selection"] = {
            "kind": "EXPLICIT_SUCCESSOR_ADOPTION" if adoption_path.is_file() else "INITIAL_V12_BASELINE",
            "manifest_path": manifest_path.relative_to(project_root).as_posix(),
            "manifest_sha256": manifest_hash,
            "adoption_decision": ({
                "path": adoption_path.relative_to(project_root).as_posix(),
                "sha256": file_sha256(adoption_path),
            } if adoption_path.is_file() else None),
        }
        assertions.append(_assertion("current_source_integrity", True, details["current_integrity_artifact"]))

        historical = verify_v24_historical_integrity(project_root)
        details["historical_integrity_result"] = {
            "status": "PASS", "v2_4_sha256": historical["contract_sha256"]
        }
        if historical["contract_sha256"] != V24_CONTRACT_SHA256:
            raise PrecreationIntegrityError("historical V2.4 digest mismatch")
        assertions.append(_assertion("historical_v2_4_integrity", True, details["historical_integrity_result"]))

        source_paths = [item["path"] for item in verified_current["sources"]]
        details["protected_source_count"] = len(source_paths)
        details["protected_source_mismatches"] = []
        assertions.append(_assertion("protected_source_set", True, {
            "count": len(source_paths), "mismatches": [], "unexplained_drift": False,
        }))

        details["migration_integrity_result"] = {
            "status": "PASS", "protected_migration_count": len(verified_current["migration_file_sha256"]),
            "executed": False,
        }
        assertions.append(_assertion("migration_material_integrity", True, details["migration_integrity_result"]))

        contract_result = _verify_contract(project_root, verified_current)
        details["contract_integrity_result"] = contract_result
        assertions.append(_assertion("contract_integrity", True, contract_result))

        verifier_result = _verify_verifier(project_root, verified_current)
        details["verifier_integrity_result"] = verifier_result
        assertions.append(_assertion("verifier_integrity", True, verifier_result))

        contract = _load_object(project_root / CURRENT_CONTRACT)
        authority_result = _verify_authority_configuration(project_root, contract)
        details["authority_configuration_result"] = authority_result
        assertions.append(_assertion("authority_configuration", True, authority_result))
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"

    completed_at = _now()
    passed_before_serialization = error is None and {
        item["name"] for item in assertions if item["passed"]
    } == set(REQUIRED_ASSERTIONS) - {"evidence_serialized"}
    status = "PASS" if passed_before_serialization else "FAIL"
    payload = {
        "artifact_schema": PRECREATION_EVIDENCE_SCHEMA,
        **details,
        "run_id": run_id,
        "status": status,
        "assertions": assertions,
        "evidence_paths": [],
        "evidence_hashes": {},
        "error": error,
        "timestamp": completed_at,
        "started_at": started_at,
        "completed_at": completed_at,
    }
    evidence_sha256 = None
    if evidence_path is not None:
        try:
            payload["evidence_paths"] = [evidence_path.relative_to(project_root).as_posix()]
            input_paths = [
                details.get("current_integrity_artifact", {}).get("path"),
                details.get("contract_integrity_result", {}).get("path"),
                (details.get("baseline_selection", {}).get("adoption_decision") or {}).get("path"),
            ]
            payload["evidence_hashes"] = {
                path: file_sha256(project_root / path) for path in input_paths if path
            }
            if status == "PASS":
                assertions.append(_assertion("evidence_serialized", True, payload["evidence_paths"]))
                payload["assertions"] = assertions
            evidence_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            evidence_sha256 = file_sha256(evidence_path)
        except Exception as exc:
            status = "FAIL"
            error = f"{type(exc).__name__}: {exc}"

    if status == "PASS" and {item["name"] for item in assertions if item["passed"]} != set(REQUIRED_ASSERTIONS):
        status = "FAIL"
        error = "required evidence contract was not fully serialized"
    return PrecreationIntegrityOutcome(
        status=status,
        evidence_path=(evidence_path.relative_to(project_root).as_posix() if evidence_sha256 else None),
        evidence_sha256=evidence_sha256,
        assertions=tuple(assertions),
        error=error,
        started_at=started_at,
        completed_at=completed_at,
        details=details,
    )
