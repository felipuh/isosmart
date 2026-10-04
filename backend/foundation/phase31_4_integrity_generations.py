"""Version-aware offline integrity guards for Phase 31.4 artifacts."""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[2]
V24_CONTRACT = ROOT / "docs/governance/fixtures/PHASE31_4_5B_ROW_LEVEL_EXECUTION_CONTRACT_V2_4.json"
V24_CONTRACT_SHA256 = "a102d278bf2e5ca6e9b8bf282f5402a54f52d4690beed2ecbed5145c56539387"
HISTORICAL_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_4_HISTORICAL_MIGRATION_MANIFEST_V1.json"
CURRENT_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V1.json"
CURRENT_V2_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V2.json"
CURRENT_V3_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V3.json"
CURRENT_V4_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V4.json"
CURRENT_V5_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V5.json"
CURRENT_V6_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V6.json"
CURRENT_V7_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V7.json"
CURRENT_V8_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V8.json"
CURRENT_V9_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V9.json"
CURRENT_V10_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V10.json"
CURRENT_V11_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V11.json"
CURRENT_V12_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V12.json"
CURRENT_V12_SHA256 = "685e04fa2e94513c357bbd6d333c2fe785e967b172234cd93faae777e25f79c2"
BASELINE_ADOPTION_MANIFEST = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_BASELINE_ADOPTION_V1.json"
CURRENT_V2_SHA256 = "3897da9ed8b2538924e527af3d79e5ef56c35c6178fe0330613187b5e70aa7c5"
CURRENT_V3_SHA256 = "c47c62a52af65cab5b13f830b048017b101425d29c8c80501f9669d2647d7def"
CURRENT_V4_SHA256 = "960f2a133f72e939842762986ce3ad43762302b0caa447799732740fc4571f25"
CURRENT_V7_SHA256 = "44b161084700ae3892cb3e49d054de35ef1403409c69eeae9d370b46565d2ca8"
CURRENT_V8_SHA256 = "ed7bed0108e790c93e0c40625b215dde02ae25566b2397533b11b6aae7040946"
CURRENT_V10_SHA256 = "4d40636266ce88a8b7f63130c8f2730566f578dfa827e9320f47ef67710c1008"
PROVENANCE_DISCONTINUITY = ROOT / "docs/governance/evidence/PHASE31_4_V2_5_RUNTIME_PROVENANCE_DISCONTINUITY_V1.json"


class IntegrityGenerationError(RuntimeError):
    pass


def file_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _observed_phase31_migrations(
    root: Path,
    expected_paths: Mapping[str, Any] | None = None,
) -> list[str]:
    observed = sorted(
        path.relative_to(root).as_posix()
        for path in (root / "backend/foundation/migrations").glob("[0-9][0-9][0-9][0-9]_*.py")
    )
    if expected_paths is not None:
        return sorted(expected_paths)
    return observed


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IntegrityGenerationError(f"unreadable integrity artifact: {path}") from exc
    if not isinstance(value, dict):
        raise IntegrityGenerationError(f"integrity artifact is not an object: {path}")
    return value


def verify_v24_historical_integrity(root: Path = ROOT) -> dict[str, Any]:
    """Verify the frozen V2.4 manifest without constraining successor files."""
    contract_path = root / V24_CONTRACT.relative_to(ROOT)
    manifest_path = root / HISTORICAL_MANIFEST.relative_to(ROOT)
    if file_sha256(contract_path) != V24_CONTRACT_SHA256:
        raise IntegrityGenerationError("V2.4 contract SHA-256 drift")
    contract = _load(contract_path)
    manifest = _load(manifest_path)
    if manifest.get("schema") != "phase31.4-v2.4-historical-migration-manifest/v1":
        raise IntegrityGenerationError("V2.4 historical manifest schema mismatch")
    if manifest.get("generation") != "V2.4" or manifest.get("contract_sha256") != V24_CONTRACT_SHA256:
        raise IntegrityGenerationError("V2.4 historical generation mismatch")
    frozen = contract.get("frozen_source_integrity", {})
    expected = frozen.get("migration_file_sha256", {})
    if list(expected) != manifest.get("migration_paths") or len(expected) != 23:
        raise IntegrityGenerationError("V2.4 historical migration membership drift")
    for relative, digest in expected.items():
        path = root / relative
        if not path.is_file() or file_sha256(path) != digest:
            raise IntegrityGenerationError(f"V2.4 historical migration drift: {relative}")
    aggregate = sha256("".join(f"{path}\0{digest}\n" for path, digest in expected.items()).encode()).hexdigest()
    if aggregate != manifest.get("migration_set_sha256") or aggregate != frozen.get("migration_set_sha256"):
        raise IntegrityGenerationError("V2.4 historical migration-set digest drift")
    return manifest


def verify_v25_current_integrity(
    root: Path = ROOT,
    manifest: Mapping[str, Any] | None = None,
    *,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Verify the promoted current source generation without weakening history."""
    if manifest is None:
        selected_path, document = _load_selected_current_baseline(root)
    else:
        document = dict(manifest)
        if re.fullmatch(
            r"phase31\.4-v2\.5-current-source-integrity/v\d+", str(document.get("schema"))
        ):
            selected_path, selected_document = _load_selected_current_baseline(root)
            if document != selected_document:
                raise IntegrityGenerationError("integrity manifest is not the selected baseline")
            if manifest_path is not None and Path(manifest_path).resolve() != selected_path.resolve():
                raise IntegrityGenerationError("integrity path is not the selected baseline")
    if re.fullmatch(r"phase31\.4-v2\.5-current-source-integrity/v(?:1[3-9]|[2-9][0-9]+)", str(document.get("schema"))):
        return verify_v25_successor_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v12":
        return verify_v25_v12_current_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v11":
        return verify_v25_v11_current_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v9":
        return verify_v25_v9_current_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v10":
        return verify_v25_v10_current_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v8":
        return verify_v25_v8_current_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v7":
        return verify_v25_v7_current_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v6":
        return verify_v25_v6_current_integrity(root, document)
    if document.get("schema") == "phase31.4-v2.5-current-source-integrity/v5":
        return verify_v25_v5_current_integrity(root, document)
    return verify_v25_v4_historical_record(root, document)


def _safe_relative_path(root: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value or Path(value).is_absolute() or ".." in Path(value).parts:
        raise IntegrityGenerationError(f"invalid repository-relative path: {value}")
    path = root / value
    if not path.resolve().is_relative_to(root.resolve()):
        raise IntegrityGenerationError(f"path escapes repository root: {value}")
    return path


def verify_v25_successor_integrity(
    root: Path,
    document: Mapping[str, Any],
    *,
    validate_sources: bool = True,
) -> dict[str, Any]:
    """Verify V13+ using predecessor-linked inventories instead of per-version code."""
    document = dict(document)
    schema = document.get("schema")
    match = re.fullmatch(r"phase31\.4-v2\.5-current-source-integrity/v(\d+)", str(schema))
    if not match or int(match.group(1)) < 13:
        raise IntegrityGenerationError("unsupported generic successor generation")
    generation_number = int(match.group(1))
    generation = f"V2.5_CURRENT_SOURCE_SUCCESSOR_V{generation_number}"
    manifest_name = f"PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V{generation_number}.json"
    predecessor_name = f"PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V{generation_number - 1}.json"
    expected_predecessor = f"docs/governance/evidence/{predecessor_name}"
    if document.get("generation") != generation or document.get("generation_id") != manifest_name.removesuffix(".json"):
        raise IntegrityGenerationError("successor generation identity mismatch")
    if document.get("governance_predecessor") != expected_predecessor:
        raise IntegrityGenerationError("successor predecessor reference mismatch")
    predecessor_path = _safe_relative_path(root, expected_predecessor)
    if not predecessor_path.is_file() or file_sha256(predecessor_path) != document.get("governance_predecessor_sha256"):
        raise IntegrityGenerationError("successor predecessor digest mismatch")
    predecessor = _load(predecessor_path)
    if generation_number == 13:
        if document.get("governance_predecessor_sha256") != CURRENT_V12_SHA256:
            raise IntegrityGenerationError("V13 must be anchored to the immutable V12 manifest")
        verify_v25_v12_current_integrity(root, predecessor, validate_sources=False)
    else:
        verify_v25_successor_integrity(root, predecessor, validate_sources=False)

    old_sources = predecessor.get("sources")
    sources = document.get("sources")
    if not isinstance(old_sources, list) or not isinstance(sources, list):
        raise IntegrityGenerationError("successor source inventory is incomplete")
    old_by_path = {entry.get("path"): entry for entry in old_sources if isinstance(entry, dict)}
    current_by_path: dict[str, Mapping[str, Any]] = {}
    for entry in sources:
        if not isinstance(entry, dict):
            raise IntegrityGenerationError("invalid successor source entry")
        relative = entry.get("path")
        _safe_relative_path(root, relative)
        if relative in current_by_path:
            raise IntegrityGenerationError("duplicate successor source path")
        current_by_path[relative] = entry
        if not entry.get("semantic_role") or not isinstance(entry.get("approval_evidence"), list) or not entry["approval_evidence"]:
            raise IntegrityGenerationError(f"unjustified successor source: {relative}")
        for evidence in entry["approval_evidence"]:
            evidence_path = _safe_relative_path(root, evidence)
            if validate_sources and not evidence_path.is_file():
                raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
        source_path = _safe_relative_path(root, relative)
        if validate_sources and (not source_path.is_file() or file_sha256(source_path) != entry.get("sha256")):
            raise IntegrityGenerationError(f"successor protected source drift: {relative}")

    old_paths = set(old_by_path)
    current_paths = set(current_by_path)
    common_paths = old_paths & current_paths
    changed_paths = {path for path in common_paths if old_by_path[path].get("sha256") != current_by_path[path].get("sha256")}
    new_paths = current_paths - old_paths
    removed_paths = old_paths - current_paths
    declared_changed = {entry.get("path") for entry in document.get("changed_sources", ()) if isinstance(entry, dict)}
    declared_new = {entry.get("path") for entry in document.get("new_sources", ()) if isinstance(entry, dict)}
    declared_removed = {entry.get("path") for entry in document.get("removed_sources", ()) if isinstance(entry, dict)}
    if declared_changed != changed_paths or declared_new != new_paths or declared_removed != removed_paths:
        raise IntegrityGenerationError("successor source-delta declarations mismatch")
    for path in changed_paths:
        old_digest = old_by_path[path].get("sha256")
        if current_by_path[path].get("predecessor_sha256") != old_digest:
            raise IntegrityGenerationError(f"successor predecessor source digest missing: {path}")
    for path in new_paths:
        if current_by_path[path].get("new_in_generation") is not True:
            raise IntegrityGenerationError(f"successor new-source marker missing: {path}")
    for entry in document.get("removed_sources", ()):
        if entry.get("sha256") != old_by_path[entry["path"]].get("sha256"):
            raise IntegrityGenerationError(f"removed-source history mismatch: {entry['path']}")
    if document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("successor inventory contains unresolved source drift")
    if document.get("protected_source_count") != len(sources) or document.get("predecessor_protected_source_count") != len(old_sources):
        raise IntegrityGenerationError("successor protected-source counts mismatch")

    old_migrations = predecessor.get("migration_file_sha256", {})
    migrations = document.get("migration_file_sha256")
    if not isinstance(old_migrations, dict) or not isinstance(migrations, dict):
        raise IntegrityGenerationError("successor migration inventory is incomplete")
    if any(migrations.get(path) != digest for path, digest in old_migrations.items()):
        raise IntegrityGenerationError("successor changed or removed historical migration material")
    inherited_paths = set(old_migrations)
    successor_migrations = set(migrations) - inherited_paths
    declared_migrations = {
        entry.get("path")
        for entry in document.get("new_migrations", ())
        if isinstance(entry, dict)
    }
    if len(declared_migrations) != len(document.get("new_migrations", ())):
        raise IntegrityGenerationError("duplicate successor migration declaration")
    if successor_migrations != declared_migrations:
        raise IntegrityGenerationError("successor migration additions are not explicitly declared")
    for entry in document.get("new_migrations", ()):
        if not isinstance(entry, dict) or not entry.get("path") or not entry.get("sha256"):
            raise IntegrityGenerationError("invalid successor migration declaration")
        if entry["path"] not in successor_migrations or migrations[entry["path"]] != entry["sha256"]:
            raise IntegrityGenerationError("successor migration declaration digest mismatch")
    migration_paths = sorted(migrations)
    if validate_sources:
        observed_migrations = _observed_phase31_migrations(root)
        if observed_migrations != migration_paths:
            raise IntegrityGenerationError("successor migration membership drift")
        for relative, digest in migrations.items():
            migration_path = _safe_relative_path(root, relative)
            if not migration_path.is_file() or file_sha256(migration_path) != digest:
                raise IntegrityGenerationError(f"successor migration drift: {relative}")
    for key in ("provenance_continuity", "provenance_discontinuity_status", "provenance_discontinuity_artifact"):
        if key in predecessor and document.get(key) != predecessor.get(key):
            raise IntegrityGenerationError(f"successor must preserve {key}")
    if document.get("retry_20_executed") is True:
        raise IntegrityGenerationError("successor cannot claim Retry 20 execution")
    return document


def _load_selected_current_baseline(root: Path) -> tuple[Path, dict[str, Any]]:
    adoption_path = root / BASELINE_ADOPTION_MANIFEST.relative_to(ROOT)
    if not adoption_path.exists():
        path = root / CURRENT_V12_MANIFEST.relative_to(ROOT)
        return path, _load(path)
    adoption = _load(adoption_path)
    required = {
        "schema": "phase31.4-v2.5-baseline-adoption/v1",
        "decision": "ADOPT_BASELINE",
    }
    if any(adoption.get(key) != value for key, value in required.items()):
        raise IntegrityGenerationError("baseline adoption decision is invalid")
    for key in ("decision_id", "adopted_by", "rationale", "manifest_path", "manifest_sha256", "generation", "adopted_at"):
        if not isinstance(adoption.get(key), str) or not adoption[key].strip():
            raise IntegrityGenerationError(f"baseline adoption is missing {key}")
    try:
        adopted_at = datetime.fromisoformat(adoption["adopted_at"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise IntegrityGenerationError("baseline adoption timestamp is invalid") from exc
    if adopted_at.tzinfo is None:
        raise IntegrityGenerationError("baseline adoption timestamp must include a timezone")
    manifest_path = _safe_relative_path(root, adoption["manifest_path"])
    if manifest_path.parent != root / "docs/governance/evidence" or not re.fullmatch(
        r"PHASE31_4_V2_5_CURRENT_SOURCE_INTEGRITY_V(?:1[3-9]|[2-9][0-9]+)\.json", manifest_path.name
    ):
        raise IntegrityGenerationError("only a numbered successor manifest may be adopted")
    if not manifest_path.is_file() or file_sha256(manifest_path) != adoption["manifest_sha256"]:
        raise IntegrityGenerationError("adopted baseline manifest digest mismatch")
    document = _load(manifest_path)
    if document.get("generation") != adoption["generation"]:
        raise IntegrityGenerationError("adopted baseline generation mismatch")
    return manifest_path, document


def select_v25_current_baseline(root: Path = ROOT) -> tuple[Path, dict[str, Any]]:
    """Return only V12 or the explicitly adopted and fully verified successor."""
    path, document = _load_selected_current_baseline(root)
    verified = verify_v25_current_integrity(root, document, manifest_path=path)
    return path, verified


def verify_v25_v12_current_integrity(
    root: Path = ROOT,
    document=None,
    *,
    validate_sources: bool = True,
) -> dict[str, Any]:
    """Verify canonical AdminApps runtime parity without rewriting V11."""
    document = dict(document) if document is not None else _load(root / CURRENT_V12_MANIFEST.relative_to(ROOT))
    predecessor_path = CURRENT_V11_MANIFEST.relative_to(ROOT).as_posix()
    predecessor_sha = "69a0eec27e96e050411e1cabf8f61aa2ca8182a736e16c3b84f67089bb4e716b"
    if (document.get("schema") != "phase31.4-v2.5-current-source-integrity/v12"
            or document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V12"
            or document.get("governance_predecessor") != predecessor_path
            or document.get("governance_predecessor_sha256") != predecessor_sha
            or file_sha256(root / predecessor_path) != predecessor_sha):
        raise IntegrityGenerationError("V12 predecessor or identity mismatch")
    predecessor = _load(root / predecessor_path)
    old = {entry["path"]: entry for entry in predecessor["sources"]}
    entries = document.get("sources", [])
    current = {entry["path"]: entry for entry in entries}
    added = "backend/foundation/phase31_4_adminapps_runtime.py"
    changed = {"backend/foundation/phase31_4_integrity_generations.py",
               "backend/foundation/phase31_4_v2_5_operational_adapters.py",
               "docs/governance/tools/phase31_4_v2_5_operational_actions.py"}
    if len(entries) != 30 or set(current) != set(old) | {added}:
        raise IntegrityGenerationError("V12 protected-source membership drift")
    for path, entry in current.items():
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V12 source: {path}")
        if validate_sources:
            for evidence in entry["approval_evidence"]:
                if not (root / evidence).is_file():
                    raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
        if validate_sources and (not (root / path).is_file() or file_sha256(root / path) != entry.get("sha256")):
            raise IntegrityGenerationError(f"V12 protected source drift: {path}")
        if path in changed and entry.get("predecessor_sha256") != old[path]["sha256"]:
            raise IntegrityGenerationError(f"V12 predecessor digest missing: {path}")
    observed = {path for path in old if current[path].get("sha256") != old[path]["sha256"]}
    if observed != changed or {entry["path"] for entry in document.get("changed_sources", [])} != changed:
        raise IntegrityGenerationError("V12 changed-source declaration drift")
    if {entry["path"] for entry in document.get("new_sources", [])} != {added}:
        raise IntegrityGenerationError("V12 new-source declaration drift")
    if document.get("migration_file_sha256") != predecessor["migration_file_sha256"]:
        raise IntegrityGenerationError("V12 migration inheritance mismatch")
    if any(document.get(key) for key in ("removed_sources", "missing_sources", "unexpected_sources")):
        raise IntegrityGenerationError("V12 unresolved source drift")
    if document.get("retry_20_executed") is not False or document.get("phase_31_5") != "EXECUTION_HELD":
        raise IntegrityGenerationError("V12 governance hold mismatch")
    return document


def verify_v25_v11_current_integrity(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify the operational bearer identity-contract successor."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V11_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v11":
        raise IntegrityGenerationError("V2.5 V11 manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V11":
        raise IntegrityGenerationError("V2.5 V11 generation mismatch")
    predecessor_relative = CURRENT_V10_MANIFEST.relative_to(ROOT).as_posix()
    predecessor_path = root / predecessor_relative
    if (document.get("governance_predecessor") != predecessor_relative
            or document.get("governance_predecessor_sha256") != CURRENT_V10_SHA256
            or file_sha256(predecessor_path) != CURRENT_V10_SHA256):
        raise IntegrityGenerationError("V10 predecessor digest mismatch")
    predecessor = _load(predecessor_path)
    predecessor_by_path = {entry["path"]: entry for entry in predecessor.get("sources", ())}
    sources = document.get("sources")
    if not isinstance(sources, list) or len(sources) != 29:
        raise IntegrityGenerationError("V11 current manifest is incomplete")
    current_by_path: dict[str, Mapping[str, Any]] = {}
    for entry in sources:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or entry["path"] in current_by_path:
            raise IntegrityGenerationError("invalid V11 source entry")
        current_by_path[entry["path"]] = entry
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V11 source: {entry.get('path')}")
        for evidence in entry["approval_evidence"]:
            if not (root / evidence).is_file():
                raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
        path = root / entry["path"]
        if not path.is_file() or file_sha256(path) != entry.get("sha256"):
            raise IntegrityGenerationError(f"V11 protected source drift: {entry['path']}")
    new_path = "backend/foundation/operational_bearer_identity.py"
    if set(current_by_path) != set(predecessor_by_path) | {new_path}:
        raise IntegrityGenerationError("V11 protected-source membership drift")
    required_changed = {
        "backend/foundation/phase31_4_integrity_generations.py",
        "backend/foundation/phase31_4_v2_5_live_executor.py",
        "backend/foundation/phase31_4_v2_5_operational_adapters.py",
        "docs/governance/tools/phase31_4_v2_5_operational_actions.py",
    }
    observed_changed = {
        path for path, old in predecessor_by_path.items()
        if current_by_path[path].get("sha256") != old.get("sha256")
    }
    declared_changed = {
        entry.get("path") for entry in document.get("changed_sources", ()) if isinstance(entry, dict)
    }
    if observed_changed != required_changed or declared_changed != required_changed:
        raise IntegrityGenerationError("V11 changed-source declaration drift")
    for path in required_changed:
        if current_by_path[path].get("predecessor_sha256") != predecessor_by_path[path].get("sha256"):
            raise IntegrityGenerationError(f"V11 predecessor digest missing: {path}")
    declared_new = {
        entry.get("path") for entry in document.get("new_sources", ()) if isinstance(entry, dict)
    }
    if declared_new != {new_path} or current_by_path[new_path].get("new_in_generation") is not True:
        raise IntegrityGenerationError("V11 new-source declaration drift")
    if document.get("removed_sources") or document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V11 inventory contains unresolved source drift")
    if document.get("migration_file_sha256") != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V11 migration inheritance mismatch")
    if document.get("retry_20_executed") is not False or document.get("phase_31_5") != "EXECUTION_HELD":
        raise IntegrityGenerationError("V11 governance hold mismatch")
    return document


def verify_v25_v9_current_integrity(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify the post-Attempt-1 operational-actions remediation successor."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V9_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v9":
        raise IntegrityGenerationError("V2.5 V9 manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V9":
        raise IntegrityGenerationError("V2.5 V9 generation mismatch")
    predecessor_relative = CURRENT_V8_MANIFEST.relative_to(ROOT).as_posix()
    if document.get("governance_predecessor") != predecessor_relative:
        raise IntegrityGenerationError("V9 predecessor reference mismatch")
    predecessor_path = root / predecessor_relative
    if file_sha256(predecessor_path) != CURRENT_V8_SHA256 or document.get("governance_predecessor_sha256") != CURRENT_V8_SHA256:
        raise IntegrityGenerationError("V8 predecessor digest mismatch")
    predecessor = _load(predecessor_path)
    predecessor_by_path = {entry["path"]: entry for entry in predecessor.get("sources", ())}
    sources = document.get("sources")
    migrations = document.get("migration_file_sha256")
    if not isinstance(sources, list) or not isinstance(migrations, dict) or len(sources) != 28:
        raise IntegrityGenerationError("V9 current manifest is incomplete")
    current_by_path: dict[str, Mapping[str, Any]] = {}
    for entry in sources:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or entry["path"] in current_by_path:
            raise IntegrityGenerationError("invalid V9 source entry")
        current_by_path[entry["path"]] = entry
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V9 source: {entry.get('path')}")
        for evidence in entry["approval_evidence"]:
            if not (root / evidence).is_file():
                raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
        path = root / entry["path"]
        if not path.is_file() or file_sha256(path) != entry.get("sha256"):
            raise IntegrityGenerationError(f"V9 protected source drift: {entry['path']}")
    if set(current_by_path) != set(predecessor_by_path):
        raise IntegrityGenerationError("V9 protected-source membership drift")
    required_changed = {
        "backend/foundation/phase31_4_integrity_generations.py",
        "docs/governance/tools/phase31_4_v2_5_operational_actions.py",
    }
    observed_changed = {path for path, old in predecessor_by_path.items() if current_by_path[path].get("sha256") != old.get("sha256")}
    declared_changed = {entry.get("path") for entry in document.get("changed_sources", ()) if isinstance(entry, dict)}
    if observed_changed != required_changed or declared_changed != required_changed:
        raise IntegrityGenerationError("V9 changed-source declaration drift")
    for path in required_changed:
        if current_by_path[path].get("predecessor_sha256") != predecessor_by_path[path].get("sha256"):
            raise IntegrityGenerationError(f"V9 predecessor digest missing: {path}")
    if document.get("new_sources") or document.get("removed_sources") or document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V9 inventory contains unresolved source drift")
    if migrations != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V9 migration inheritance mismatch")
    return document


def verify_v25_v10_current_integrity(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify the Attempt 3 readiness-path successor while preserving V9."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V10_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v10":
        raise IntegrityGenerationError("V2.5 V10 manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V10":
        raise IntegrityGenerationError("V2.5 V10 generation mismatch")
    predecessor_relative = CURRENT_V9_MANIFEST.relative_to(ROOT).as_posix()
    predecessor_path = root / predecessor_relative
    predecessor_sha = document.get("governance_predecessor_sha256")
    if document.get("governance_predecessor") != predecessor_relative or not isinstance(predecessor_sha, str) or file_sha256(predecessor_path) != predecessor_sha:
        raise IntegrityGenerationError("V9 predecessor digest mismatch")
    predecessor = _load(predecessor_path)
    predecessor_by_path = {entry["path"]: entry for entry in predecessor.get("sources", ())}
    sources = document.get("sources")
    if not isinstance(sources, list) or len(sources) != 28:
        raise IntegrityGenerationError("V10 current manifest is incomplete")
    current_by_path: dict[str, Mapping[str, Any]] = {}
    for entry in sources:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str) or entry["path"] in current_by_path:
            raise IntegrityGenerationError("invalid V10 source entry")
        current_by_path[entry["path"]] = entry
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V10 source: {entry.get('path')}")
        for evidence in entry["approval_evidence"]:
            if not (root / evidence).is_file():
                raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
        path = root / entry["path"]
        if not path.is_file() or file_sha256(path) != entry.get("sha256"):
            raise IntegrityGenerationError(f"V10 protected source drift: {entry['path']}")
    if set(current_by_path) != set(predecessor_by_path):
        raise IntegrityGenerationError("V10 protected-source membership drift")
    required_changed = {
        "backend/foundation/phase31_4_integrity_generations.py",
        "backend/foundation/phase31_4_v2_5_operational_adapters.py",
    }
    observed_changed = {path for path, old in predecessor_by_path.items() if current_by_path[path].get("sha256") != old.get("sha256")}
    declared_changed = {entry.get("path") for entry in document.get("changed_sources", ()) if isinstance(entry, dict)}
    if observed_changed != required_changed or declared_changed != required_changed:
        raise IntegrityGenerationError("V10 changed-source declaration drift")
    for path in required_changed:
        if current_by_path[path].get("predecessor_sha256") != predecessor_by_path[path].get("sha256"):
            raise IntegrityGenerationError(f"V10 predecessor digest missing: {path}")
    if document.get("new_sources") or document.get("removed_sources") or document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V10 inventory contains unresolved source drift")
    if document.get("migration_file_sha256") != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V10 migration inheritance mismatch")
    return document


def verify_v25_v4_historical_record(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
    *,
    validate_sources: bool = True,
) -> dict[str, Any]:
    """Verify V4 as an immutable predecessor while V5 is current."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V4_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v4":
        raise IntegrityGenerationError("V2.5 current manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V4":
        raise IntegrityGenerationError("V2.5 current generation mismatch")
    predecessor_path = document.get("governance_predecessor")
    if predecessor_path != CURRENT_V3_MANIFEST.relative_to(ROOT).as_posix():
        raise IntegrityGenerationError("V2.5 current predecessor reference mismatch")
    if document.get("governance_predecessor_sha256") != CURRENT_V3_SHA256:
        raise IntegrityGenerationError("V2.5 current predecessor digest mismatch")
    predecessor = verify_v25_v3_historical_record(root)
    sources = document.get("sources")
    migrations = document.get("migration_file_sha256")
    if not isinstance(sources, list) or not sources or not isinstance(migrations, dict):
        raise IntegrityGenerationError("V2.5 current manifest is incomplete")
    seen: set[str] = set()
    for entry in sources:
        if not isinstance(entry, dict):
            raise IntegrityGenerationError("invalid V2.5 source entry")
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in seen:
            raise IntegrityGenerationError("duplicate or invalid V2.5 source path")
        seen.add(relative)
        inherited = next((item for item in predecessor["sources"] if item.get("path") == relative), {})
        semantic_role = entry.get("semantic_role") or inherited.get("semantic_role")
        approval_evidence = entry.get("approval_evidence") or inherited.get("approval_evidence")
        if not semantic_role or not approval_evidence:
            raise IntegrityGenerationError(f"unjustified V2.5 source: {relative}")
        if validate_sources:
            for evidence in approval_evidence:
                if not (root / evidence).is_file():
                    raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
            path = root / relative
            if not path.is_file() or file_sha256(path) != entry.get("sha256"):
                raise IntegrityGenerationError(f"V2.5 protected source drift: {relative}")
    predecessor_by_path = {entry["path"]: entry for entry in predecessor["sources"]}
    required_new = "backend/integration/client.py"
    expected_paths = set(predecessor_by_path) | {required_new}
    if seen != expected_paths or len(sources) != 23:
        raise IntegrityGenerationError("V2.5 current protected-source membership drift")
    current_by_path = {entry["path"]: entry for entry in sources}
    changed_paths = {
        path for path, old in predecessor_by_path.items()
        if current_by_path[path].get("sha256") != old.get("sha256")
    }
    declared_changed = {
        entry.get("path") for entry in document.get("changed_sources", ())
        if isinstance(entry, dict)
    }
    if changed_paths != declared_changed:
        raise IntegrityGenerationError("V2.5 current changed-source declaration drift")
    for path in changed_paths:
        if current_by_path[path].get("predecessor_sha256") != predecessor_by_path[path].get("sha256"):
            raise IntegrityGenerationError(f"V2.5 current predecessor digest missing: {path}")
    declared_new = {
        entry.get("path") for entry in document.get("new_sources", ())
        if isinstance(entry, dict)
    }
    if declared_new != {required_new} or current_by_path[required_new].get("new_in_generation") is not True:
        raise IntegrityGenerationError("V2.5 current new-source declaration drift")
    if document.get("removed_sources") or document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V2.5 current inventory contains unresolved source drift")
    if migrations != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V2.5 current migration inheritance mismatch")
    for relative, digest in migrations.items():
        migration_path = root / relative
        if not migration_path.is_file() or file_sha256(migration_path) != digest:
            raise IntegrityGenerationError(f"V2.5 current migration drift: {relative}")
    return document


def verify_v25_v5_current_integrity(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
    *,
    validate_sources: bool = True,
) -> dict[str, Any]:
    """Verify V5 and its complete runner-material source inventory."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V5_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v5":
        raise IntegrityGenerationError("V2.5 successor manifest schema mismatch")
    if document.get("governance_predecessor") != CURRENT_V4_MANIFEST.relative_to(ROOT).as_posix():
        raise IntegrityGenerationError("V5 predecessor reference mismatch")
    if document.get("governance_predecessor_sha256") != CURRENT_V4_SHA256:
        raise IntegrityGenerationError("V5 predecessor digest mismatch")
    predecessor = verify_v25_v4_historical_record(root, validate_sources=False)
    sources = document.get("sources")
    migrations = document.get("migration_file_sha256")
    if not isinstance(sources, list) or not isinstance(migrations, dict):
        raise IntegrityGenerationError("V5 current manifest is incomplete")
    predecessor_by_path = {entry["path"]: entry for entry in predecessor["sources"]}
    required_runner = {
        "backend/foundation/phase31_4_v2_5_disposable_runner.py",
        "docs/governance/tools/phase31_4_v2_5_disposable_runner.py",
    }
    expected_paths = set(predecessor_by_path) | required_runner
    seen: set[str] = set()
    for entry in sources:
        if not isinstance(entry, dict):
            raise IntegrityGenerationError("invalid V5 source entry")
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in seen:
            raise IntegrityGenerationError("duplicate or invalid V5 source path")
        seen.add(relative)
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V5 source: {relative}")
        if validate_sources:
            for evidence in entry["approval_evidence"]:
                if not (root / evidence).is_file():
                    raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
        if validate_sources:
            path = root / relative
            if not path.is_file() or file_sha256(path) != entry.get("sha256"):
                raise IntegrityGenerationError(f"V5 protected source drift: {relative}")
    if seen != expected_paths or len(sources) != 25:
        raise IntegrityGenerationError("V5 current protected-source membership drift")
    current_by_path = {entry["path"]: entry for entry in sources}
    changed_paths = {
        path for path, old in predecessor_by_path.items()
        if current_by_path[path].get("sha256") != old.get("sha256")
    }
    declared_changed = {
        entry.get("path") for entry in document.get("changed_sources", ())
        if isinstance(entry, dict)
    }
    if changed_paths != declared_changed:
        raise IntegrityGenerationError("V5 changed-source declaration drift")
    for path in changed_paths:
        if current_by_path[path].get("predecessor_sha256") != predecessor_by_path[path].get("sha256"):
            raise IntegrityGenerationError(f"V5 predecessor digest missing: {path}")
    declared_new = {
        entry.get("path") for entry in document.get("new_sources", ())
        if isinstance(entry, dict)
    }
    if declared_new != required_runner:
        raise IntegrityGenerationError("V5 new-source declaration drift")
    if document.get("removed_sources") or document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V5 inventory contains unresolved source drift")
    if migrations != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V5 migration inheritance mismatch")
    observed = _observed_phase31_migrations(root, migrations)
    if observed != list(migrations):
        raise IntegrityGenerationError("V5 migration membership drift")
    for relative, digest in migrations.items():
        if file_sha256(root / relative) != digest:
            raise IntegrityGenerationError(f"V5 migration drift: {relative}")
    return document


def verify_v25_v6_current_integrity(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
    *,
    validate_sources: bool = True,
) -> dict[str, Any]:
    """Verify the live-executor successor while preserving V1 through V5."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V6_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v6":
        raise IntegrityGenerationError("V2.5 successor manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V6":
        raise IntegrityGenerationError("V2.5 current generation mismatch")
    if document.get("governance_predecessor") != CURRENT_V5_MANIFEST.relative_to(ROOT).as_posix():
        raise IntegrityGenerationError("V6 predecessor reference mismatch")
    predecessor_path = root / CURRENT_V5_MANIFEST.relative_to(ROOT)
    if document.get("governance_predecessor_sha256") != file_sha256(predecessor_path):
        raise IntegrityGenerationError("V6 predecessor digest mismatch")
    predecessor = verify_v25_v5_current_integrity(root, validate_sources=False)
    sources = document.get("sources")
    migrations = document.get("migration_file_sha256")
    if not isinstance(sources, list) or not isinstance(migrations, dict):
        raise IntegrityGenerationError("V6 current manifest is incomplete")
    predecessor_by_path = {entry["path"]: entry for entry in predecessor["sources"]}
    required_new = "backend/foundation/phase31_4_v2_5_live_executor.py"
    expected_paths = set(predecessor_by_path) | {required_new}
    current_by_path: dict[str, Mapping[str, Any]] = {}
    for entry in sources:
        if not isinstance(entry, dict):
            raise IntegrityGenerationError("invalid V6 source entry")
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in current_by_path:
            raise IntegrityGenerationError("duplicate or invalid V6 source path")
        current_by_path[relative] = entry
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V6 source: {relative}")
        if validate_sources:
            for evidence in entry["approval_evidence"]:
                if not (root / evidence).is_file():
                    raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
            path = root / relative
            if not path.is_file() or file_sha256(path) != entry.get("sha256"):
                raise IntegrityGenerationError(f"V6 protected source drift: {relative}")
    if set(current_by_path) != expected_paths or len(sources) != 26:
        raise IntegrityGenerationError("V6 current protected-source membership drift")
    declared_changed = {
        entry.get("path") for entry in document.get("changed_sources", ())
        if isinstance(entry, dict)
    }
    if declared_changed != {"backend/foundation/phase31_4_integrity_generations.py"}:
        raise IntegrityGenerationError("V6 changed-source declaration drift")
    changed_entry = current_by_path["backend/foundation/phase31_4_integrity_generations.py"]
    predecessor_entry = predecessor_by_path["backend/foundation/phase31_4_integrity_generations.py"]
    if changed_entry.get("predecessor_sha256") != predecessor_entry.get("sha256"):
        raise IntegrityGenerationError("V6 predecessor digest missing")
    declared_new = {
        entry.get("path") for entry in document.get("new_sources", ())
        if isinstance(entry, dict)
    }
    if declared_new != {required_new} or current_by_path[required_new].get("new_in_generation") is not True:
        raise IntegrityGenerationError("V6 new-source declaration drift")
    if document.get("removed_sources") or document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V6 inventory contains unresolved source drift")
    if migrations != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V6 migration inheritance mismatch")
    return document


def verify_v25_v7_current_integrity(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
    *,
    validate_sources: bool = True,
) -> dict[str, Any]:
    """Verify the operational-executor source successor without claiming live readiness."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V7_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v7":
        raise IntegrityGenerationError("V2.5 successor manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V7":
        raise IntegrityGenerationError("V2.5 current generation mismatch")
    predecessor_relative = CURRENT_V6_MANIFEST.relative_to(ROOT).as_posix()
    if document.get("governance_predecessor") != predecessor_relative:
        raise IntegrityGenerationError("V7 predecessor reference mismatch")
    predecessor_path = root / predecessor_relative
    if document.get("governance_predecessor_sha256") != file_sha256(predecessor_path):
        raise IntegrityGenerationError("V7 predecessor digest mismatch")
    predecessor = verify_v25_v6_current_integrity(root, validate_sources=False)
    sources = document.get("sources")
    migrations = document.get("migration_file_sha256")
    if not isinstance(sources, list) or not isinstance(migrations, dict):
        raise IntegrityGenerationError("V7 current manifest is incomplete")
    predecessor_by_path = {entry["path"]: entry for entry in predecessor["sources"]}
    required_new = {
        "backend/foundation/phase31_4_v2_5_operational_adapters.py",
        "docs/governance/tools/phase31_4_v2_5_operational_actions.py",
    }
    expected_paths = set(predecessor_by_path) | required_new
    current_by_path: dict[str, Mapping[str, Any]] = {}
    for entry in sources:
        if not isinstance(entry, dict):
            raise IntegrityGenerationError("invalid V7 source entry")
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in current_by_path:
            raise IntegrityGenerationError("duplicate or invalid V7 source path")
        current_by_path[relative] = entry
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V7 source: {relative}")
        if validate_sources:
            for evidence in entry["approval_evidence"]:
                if not (root / evidence).is_file():
                    raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
            path = root / relative
            if not path.is_file() or file_sha256(path) != entry.get("sha256"):
                raise IntegrityGenerationError(f"V7 protected source drift: {relative}")
    if set(current_by_path) != expected_paths or len(sources) != 28:
        raise IntegrityGenerationError("V7 current protected-source membership drift")
    required_changed = {
        "backend/foundation/phase31_4_integrity_generations.py",
        "backend/foundation/phase31_4_v2_5_disposable_runner.py",
        "backend/foundation/phase31_4_v2_5_live_executor.py",
    }
    declared_changed = {
        entry.get("path") for entry in document.get("changed_sources", ())
        if isinstance(entry, dict)
    }
    observed_changed = {
        path for path, old in predecessor_by_path.items()
        if current_by_path[path].get("sha256") != old.get("sha256")
    }
    if declared_changed != required_changed or observed_changed != required_changed:
        raise IntegrityGenerationError("V7 changed-source declaration drift")
    for path in required_changed:
        if current_by_path[path].get("predecessor_sha256") != predecessor_by_path[path].get("sha256"):
            raise IntegrityGenerationError(f"V7 predecessor digest missing: {path}")
    declared_new = {
        entry.get("path") for entry in document.get("new_sources", ())
        if isinstance(entry, dict)
    }
    if declared_new != required_new:
        raise IntegrityGenerationError("V7 new-source declaration drift")
    if any(current_by_path[path].get("new_in_generation") is not True for path in required_new):
        raise IntegrityGenerationError("V7 new-source marker missing")
    if document.get("removed_sources") or document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V7 inventory contains unresolved source drift")
    if migrations != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V7 migration inheritance mismatch")
    if validate_sources:
        observed_migrations = _observed_phase31_migrations(root, migrations)
        if observed_migrations != list(migrations):
            raise IntegrityGenerationError("V7 migration membership drift")
        for relative, digest in migrations.items():
            if file_sha256(root / relative) != digest:
                raise IntegrityGenerationError(f"V7 migration drift: {relative}")
    if document.get("live_execution", {}).get("operational_live_executor_diagnostic") != "FAIL":
        raise IntegrityGenerationError("V7 must retain the failed operational diagnostic")
    if document.get("live_execution", {}).get("stage_ext_live_revalidation") != "PENDING":
        raise IntegrityGenerationError("V7 must retain pending Stage EXT live revalidation")
    return document


def verify_v25_v8_current_integrity(
    root: Path = ROOT,
    document: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Verify the diagnostic state-machine successor without claiming live readiness."""
    document = dict(document) if document is not None else _load(
        root / CURRENT_V8_MANIFEST.relative_to(ROOT)
    )
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v8":
        raise IntegrityGenerationError("V2.5 successor manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V8":
        raise IntegrityGenerationError("V2.5 current generation mismatch")
    predecessor_relative = CURRENT_V7_MANIFEST.relative_to(ROOT).as_posix()
    if document.get("governance_predecessor") != predecessor_relative:
        raise IntegrityGenerationError("V8 predecessor reference mismatch")
    predecessor_path = root / predecessor_relative
    if file_sha256(predecessor_path) != CURRENT_V7_SHA256:
        raise IntegrityGenerationError("V7 predecessor manifest SHA-256 drift")
    if document.get("governance_predecessor_sha256") != CURRENT_V7_SHA256:
        raise IntegrityGenerationError("V8 predecessor digest mismatch")
    predecessor = verify_v25_v7_current_integrity(root, validate_sources=False)
    sources = document.get("sources")
    migrations = document.get("migration_file_sha256")
    if not isinstance(sources, list) or not isinstance(migrations, dict):
        raise IntegrityGenerationError("V8 current manifest is incomplete")
    predecessor_by_path = {entry["path"]: entry for entry in predecessor["sources"]}
    current_by_path: dict[str, Mapping[str, Any]] = {}
    for entry in sources:
        if not isinstance(entry, dict):
            raise IntegrityGenerationError("invalid V8 source entry")
        relative = entry.get("path")
        if not isinstance(relative, str) or relative in current_by_path:
            raise IntegrityGenerationError("duplicate or invalid V8 source path")
        current_by_path[relative] = entry
        if not entry.get("semantic_role") or not entry.get("approval_evidence"):
            raise IntegrityGenerationError(f"unjustified V8 source: {relative}")
        for evidence in entry["approval_evidence"]:
            if not (root / evidence).is_file():
                raise IntegrityGenerationError(f"missing approval evidence: {evidence}")
        path = root / relative
        if not path.is_file() or file_sha256(path) != entry.get("sha256"):
            raise IntegrityGenerationError(f"V8 protected source drift: {relative}")
    if set(current_by_path) != set(predecessor_by_path) or len(sources) != 28:
        raise IntegrityGenerationError("V8 current protected-source membership drift")
    required_changed = {
        "backend/foundation/phase31_4_integrity_generations.py",
        "backend/foundation/phase31_4_v2_5_disposable_runner.py",
    }
    declared_changed = {
        entry.get("path") for entry in document.get("changed_sources", ())
        if isinstance(entry, dict)
    }
    observed_changed = {
        path for path, old in predecessor_by_path.items()
        if current_by_path[path].get("sha256") != old.get("sha256")
    }
    if declared_changed != required_changed or observed_changed != required_changed:
        raise IntegrityGenerationError("V8 changed-source declaration drift")
    for path in required_changed:
        if current_by_path[path].get("predecessor_sha256") != predecessor_by_path[path].get("sha256"):
            raise IntegrityGenerationError(f"V8 predecessor digest missing: {path}")
    if document.get("new_sources") or document.get("removed_sources"):
        raise IntegrityGenerationError("V8 source membership evolution is not permitted")
    if document.get("missing_sources") or document.get("unexpected_sources"):
        raise IntegrityGenerationError("V8 inventory contains unresolved source drift")
    if migrations != predecessor.get("migration_file_sha256", {}):
        raise IntegrityGenerationError("V8 migration inheritance mismatch")
    observed_migrations = _observed_phase31_migrations(root, migrations)
    if observed_migrations != list(migrations):
        raise IntegrityGenerationError("V8 migration membership drift")
    for relative, digest in migrations.items():
        if file_sha256(root / relative) != digest:
            raise IntegrityGenerationError(f"V8 migration drift: {relative}")
    if document.get("provenance_discontinuity_status") != "PROVENANCE_DISCONTINUITY":
        raise IntegrityGenerationError("V8 must inherit the provenance discontinuity")
    live = document.get("live_execution", {})
    if live.get("stage_ext_live_revalidation") != "PENDING":
        raise IntegrityGenerationError("V8 must retain pending Stage EXT live revalidation")
    if live.get("operational_readiness") != "NOT_READY":
        raise IntegrityGenerationError("V8 source integrity cannot assert operational readiness")
    if document.get("retry_20_executed") is not False:
        raise IntegrityGenerationError("V8 must retain Retry 20 as not executed")
    return document


def verify_v25_v3_historical_record(root: Path = ROOT) -> dict[str, Any]:
    """Verify V3's immutable artifact identity without requiring old source bytes."""
    path = root / CURRENT_V3_MANIFEST.relative_to(ROOT)
    if file_sha256(path) != CURRENT_V3_SHA256:
        raise IntegrityGenerationError("V3 predecessor manifest SHA-256 drift")
    document = _load(path)
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v3":
        raise IntegrityGenerationError("V3 predecessor manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_SUCCESSOR_V3":
        raise IntegrityGenerationError("V3 predecessor generation mismatch")
    if len(document.get("sources", ())) != 22:
        raise IntegrityGenerationError("V3 predecessor protected-source membership drift")
    return document


def verify_v25_v2_historical_record(root: Path = ROOT) -> dict[str, Any]:
    """Verify V2 remains the immutable governance predecessor of current V3."""
    path = root / CURRENT_V2_MANIFEST.relative_to(ROOT)
    if file_sha256(path) != CURRENT_V2_SHA256:
        raise IntegrityGenerationError("V2 predecessor manifest SHA-256 drift")
    document = _load(path)
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v2":
        raise IntegrityGenerationError("V2 predecessor manifest schema mismatch")
    if document.get("generation") != "V2.5_CURRENT_SOURCE_BASELINE":
        raise IntegrityGenerationError("V2 predecessor generation mismatch")
    if len(document.get("sources", ())) != 21:
        raise IntegrityGenerationError("V2 predecessor protected-source membership drift")
    if len(document.get("migration_file_sha256", {})) != 24:
        raise IntegrityGenerationError("V2 predecessor migration membership drift")
    return document


def verify_v25_v1_historical_record(root: Path = ROOT) -> dict[str, Any]:
    """Verify V1 remains the immutable predecessor record, not current authority."""
    document = _load(root / CURRENT_MANIFEST.relative_to(ROOT))
    if document.get("schema") != "phase31.4-v2.5-current-source-integrity/v1":
        raise IntegrityGenerationError("V1 historical manifest schema mismatch")
    runtime = next((entry for entry in document.get("sources", [])
                    if entry.get("path") == "backend/foundation/phase31_4_v2_5_runtime.py"), None)
    if not runtime or runtime.get("sha256") != "5be7650ac78eae653f4e6cd0b656ab0ccd9556a75f9c41cb3edd512d6a012cfd":
        raise IntegrityGenerationError("V1 predecessor runtime record changed")
    return document


def verify_approved_successor(
    path: str,
    historical_sha256: str,
    root: Path = ROOT,
) -> None:
    """Accept current bytes only when the V2.5 manifest links the old generation."""
    current = file_sha256(root / path)
    if current == historical_sha256:
        return
    manifest = verify_v25_current_integrity(root)
    match = next((entry for entry in manifest["sources"] if entry["path"] == path), None)
    if not match:
        raise IntegrityGenerationError(f"unapproved successor for historical source: {path}")
    v3 = verify_v25_v3_historical_record(root)
    v3_match = next((entry for entry in v3["sources"] if entry["path"] == path), None)
    predecessor_sha256 = match.get("predecessor_sha256") or (v3_match or {}).get("predecessor_sha256")
    if predecessor_sha256 != historical_sha256:
        predecessor = verify_v25_v2_historical_record(root)
        predecessor_match = next(
            (entry for entry in predecessor["sources"] if entry["path"] == path), None
        )
        if (not predecessor_match
                or predecessor_sha256 != predecessor_match.get("sha256")
                or predecessor_match.get("predecessor_sha256") != historical_sha256):
            raise IntegrityGenerationError(f"unapproved successor for historical source: {path}")
    if match.get("provenance_relation") == "governance_predecessor":
        discontinuity = root / match.get("provenance_discontinuity", "")
        if not discontinuity.is_file() or file_sha256(discontinuity) != match.get("provenance_discontinuity_sha256"):
            raise IntegrityGenerationError(f"missing provenance discontinuity for: {path}")
