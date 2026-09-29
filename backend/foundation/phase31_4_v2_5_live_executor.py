"""Fail-closed operational bridge for Phase 31.4 V2.5 evidence execution.

Operational mode has no default/fake adapter: each claimed fact comes from an
explicit adapter and every Stage EXT identity is independently read back.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol
from uuid import UUID

from .phase31_4_v2_5_precreation_integrity import verify_precreation_integrity
from .phase31_4_v2_5_runtime import CaptureBundle, build_v25_runtime

LIVE_EXECUTOR_CLASSIFICATION = "LIVE_EXECUTOR_OPERATIONAL_DIAGNOSTIC"
OPERATIONAL_MODES = frozenset({"evidence", "diagnostic"})
FORBIDDEN_PROVENANCE = frozenset({"fixture", "historical", "literal", "fallback", "synthetic"})


class LiveExecutorError(RuntimeError):
    def __init__(self, code: str, message: str, *, step: str | None = None) -> None:
        super().__init__(message); self.code = code; self.step = step
    def __str__(self) -> str:
        return f"{self.code}: {super().__str__()}"


@dataclass(frozen=True)
class LiveExecutionContext:
    run_id: str
    run_slug: str
    repository_root: Path
    evidence_root: Path
    authorization_reference: str
    integrity_generation: str
    resource_manifest: Mapping[str, Any]
    adminapps_db_endpoint: str
    isosmart_db_endpoint: str
    allocated_host_ports: dict[str, int]
    environment: dict[str, str] = field(default_factory=dict)
    service_urls: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class OperationalEvidenceAdapter(Protocol):
    """Explicit boundary for all mandatory operational actions."""
    test_only: bool
    def bootstrap_adminapps(self, context: LiveExecutionContext) -> Mapping[str, Any]: ...
    def bootstrap_isosmart(self, context: LiveExecutionContext) -> Mapping[str, Any]: ...
    def start_adminapps(self, context: LiveExecutionContext) -> Mapping[str, Any]: ...
    def start_isosmart(self, context: LiveExecutionContext) -> Mapping[str, Any]: ...
    def create_adminapps_authority(self, context: LiveExecutionContext) -> Mapping[str, Any]: ...
    def deliver_projection_events(self, context: LiveExecutionContext, authority: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def read_tenant_projection(self, context: LiveExecutionContext, delivery: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def read_user_projection(self, context: LiveExecutionContext, delivery: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def create_qms_organization(self, context: LiveExecutionContext, authority: Mapping[str, Any], delivery: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def read_qms_organization(self, context: LiveExecutionContext, returned_id: str) -> Mapping[str, Any]: ...
    def create_process(self, context: LiveExecutionContext, organization_id: str, authority: Mapping[str, Any]) -> Mapping[str, Any]: ...
    def read_process(self, context: LiveExecutionContext, returned_id: str) -> Mapping[str, Any]: ...
    def stop_services(self) -> Mapping[str, Any]: ...


def _require_uuid(value: Any, *, label: str, code: str = "STAGE_EXT_INCOMPLETE") -> str:
    text = str(value or "")
    try: UUID(text)
    except (TypeError, ValueError, AttributeError) as exc:
        raise LiveExecutorError(code, f"invalid or missing UUID for {label}", step="stage_ext") from exc
    return text


def _resource_port(resources: Mapping[str, Any], role: str) -> int:
    item = resources.get(role)
    if not isinstance(item, Mapping) or not isinstance(item.get("host_port"), int) or int(item["host_port"]) <= 0:
        raise LiveExecutorError("RUNTIME_HANDOFF_FAILURE", f"missing dynamic PostgreSQL port for {role}")
    return int(item["host_port"])


def build_live_execution_context(*, repository_root: str | Path, runner: Any,
    evidence_root: str | Path, authorization_reference: str, integrity_generation: str,
    resource_manifest: Mapping[str, Any] | None = None,
    adminapps_db_endpoint: str | None = None, isosmart_db_endpoint: str | None = None,
    allocated_host_ports: dict[str, int] | None = None,
    environment: Mapping[str, str] | None = None,
    service_urls: Mapping[str, str] | None = None, run_id: str | None = None) -> LiveExecutionContext:
    root = Path(repository_root).resolve()
    manifest = dict(resource_manifest or getattr(runner, "manifest", {}))
    identifier, slug = run_id or str(manifest.get("run_id") or ""), str(manifest.get("run_slug") or "")
    resources = manifest.get("resources")
    if not identifier or not slug or not isinstance(resources, Mapping):
        raise LiveExecutorError("RUNTIME_HANDOFF_FAILURE", "runner manifest is incomplete")
    ports = dict(allocated_host_ports or {})
    for role in ("adminapps", "isosmart"): ports.setdefault(role, _resource_port(resources, role))
    admin_name, iso_name = str(resources["adminapps"].get("database_name") or ""), str(resources["isosmart"].get("database_name") or "")
    if not admin_name or not iso_name: raise LiveExecutorError("RUNTIME_HANDOFF_FAILURE", "run-scoped database names are required")
    env, urls = dict(environment or {}), dict(service_urls or {})
    for key, value in urls.items():
        if key in {"adminapps", "isosmart"} and not str(value).startswith(("http://", "https://")):
            raise LiveExecutorError("RUNTIME_HANDOFF_FAILURE", f"invalid {key} service URL")
    if "adminapps" in urls: env["ADMIN_APPS_BASE_URL"] = str(urls["adminapps"])
    if "isosmart" in urls: env["ISO_SMART_BASE_URL"] = str(urls["isosmart"])
    env.update(PHASE31_RUN_ID=identifier, PHASE31_EVIDENCE_ROOT=str(Path(evidence_root).resolve()))
    return LiveExecutionContext(identifier, slug, root, Path(evidence_root).resolve(), authorization_reference,
        integrity_generation, manifest,
        adminapps_db_endpoint or f"postgresql://127.0.0.1:{ports['adminapps']}/{admin_name}",
        isosmart_db_endpoint or f"postgresql://127.0.0.1:{ports['isosmart']}/{iso_name}",
        {str(k): int(v) for k, v in ports.items()}, env, urls)


class Phase31_4V25LiveEvidenceExecutor:
    def __init__(self, *, runner: Any, context: LiveExecutionContext,
                 adapter: OperationalEvidenceAdapter, mode: str = "diagnostic",
                 runtime_factory: Any = build_v25_runtime, allow_runtime_execution: bool = False) -> None:
        if mode not in OPERATIONAL_MODES | {"test"}: raise LiveExecutorError("AUTHORIZATION_INVALID", f"unsupported mode: {mode}")
        if mode in OPERATIONAL_MODES and getattr(adapter, "test_only", True):
            raise LiveExecutorError("OPERATIONAL_ADAPTER_REQUIRED", "test/fake adapter forbidden in operational mode")
        self.runner, self.context, self.adapter, self.mode = runner, context, adapter, mode
        self.runtime_factory, self.allow_runtime_execution = runtime_factory, allow_runtime_execution
        self.stage_ext_values: dict[str, Any] = {}; self.stage_ext_evidence: dict[str, Any] = {}
        self._authority: Mapping[str, Any] | None = None; self._delivery: Mapping[str, Any] | None = None

    def precreation(self, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
        outcome = verify_precreation_integrity(root=self.context.repository_root, run_id=self.context.run_id)
        if outcome.status != "PASS": raise LiveExecutorError("PRECREATION_FAILURE", outcome.error or "protected PRECREATION failed")
        return {"status": "PASS", "evidence_path": outcome.evidence_path, "evidence_sha256": outcome.evidence_sha256,
                "assertions": len(outcome.assertions), "executor": "PrecreationIntegrityExecutor"}

    @staticmethod
    def _pass(result: Mapping[str, Any], code: str, label: str) -> Mapping[str, Any]:
        if result.get("status") != "PASS": raise LiveExecutorError(code, f"{label} did not return PASS")
        return result

    def bootstrap_runtime(self) -> Mapping[str, Any]:
        admin = self._pass(self.adapter.bootstrap_adminapps(self.context), "DB_BOOTSTRAP_FAILURE", "AdminApps bootstrap")
        iso = self._pass(self.adapter.bootstrap_isosmart(self.context), "DB_BOOTSTRAP_FAILURE", "ISO Smart bootstrap")
        for label, result in (("AdminApps", admin), ("ISO Smart", iso)):
            if result.get("database_readiness") != "PASS": raise LiveExecutorError("DB_BOOTSTRAP_FAILURE", f"{label} readiness missing")
            if result.get("migrations_pending") != 0: raise LiveExecutorError("MIGRATION_FAILURE", f"{label} has pending migrations")
        if iso.get("roles_verified") is not True or iso.get("session_configuration_verified") is not True:
            raise LiveExecutorError("ROLE_BOOTSTRAP_FAILURE", "ISO Smart roles/session configuration not verified")
        return {"adminapps": admin, "isosmart": iso}

    def start_services(self) -> Mapping[str, Any]:
        results: dict[str, Any] = {}
        for key, method, code in (("adminapps", self.adapter.start_adminapps, "ADMINAPPS_START_FAILURE"), ("isosmart", self.adapter.start_isosmart, "ISOSMART_START_FAILURE")):
            result = self._pass(method(self.context), code, f"{key} startup")
            if not isinstance(result.get("pid"), int) or result["pid"] <= 0 or result.get("readiness") != "PASS":
                raise LiveExecutorError(code, f"{key} requires real PID and readiness")
            url = str(result.get("base_url") or "")
            if not url.startswith(("http://", "https://")): raise LiveExecutorError(code, f"{key} service URL missing")
            self.context.service_urls[key] = url; results[key] = result
        self.context.environment.update(ADMIN_APPS_BASE_URL=self.context.service_urls["adminapps"], ISO_SMART_BASE_URL=self.context.service_urls["isosmart"])
        return results

    def deliver_event_projection(self) -> Mapping[str, Any]:
        if self._authority is None: self._authority = self._pass(self.adapter.create_adminapps_authority(self.context), "ADMINAPPS_AUTHORITY_FAILURE", "AdminApps authority")
        self._delivery = self._pass(self.adapter.deliver_projection_events(self.context, self._authority), "EVENT_DELIVERY_FAILURE", "event delivery")
        for key in ("outbox_id", "delivery_result", "ingress_receipt", "tenant_projection_id", "user_projection_id"):
            if not self._delivery.get(key): raise LiveExecutorError("EVENT_DELIVERY_FAILURE", f"delivery evidence missing {key}")
        return self._delivery

    @staticmethod
    def _identity(alias: str, returned: Any, readback: Any, provenance: str, source: str) -> dict[str, Any]:
        returned_id = _require_uuid(returned, label=f"{alias}.returned_value")
        readback_id = _require_uuid(readback, label=f"{alias}.persisted_readback_value")
        if returned_id != readback_id: raise LiveExecutorError("PROJECTION_READBACK_FAILURE", f"{alias} returned/readback mismatch")
        if any(word in provenance.lower() for word in FORBIDDEN_PROVENANCE): raise LiveExecutorError("CAPTURE_BUNDLE_FAILURE", f"forbidden provenance: {provenance}")
        return {"returned_value": returned_id, "persisted_readback_value": readback_id, "equality_result": True,
                "provenance": provenance, "source_service": source, "readback_at": datetime.now(timezone.utc).isoformat()}

    def resolve_stage_ext_identities(self) -> Mapping[str, Any]:
        if self._delivery is None: self.deliver_event_projection()
        assert self._authority is not None and self._delivery is not None
        tenant_rb, actor_rb = self._authority.get("tenant_readback") or {}, self._authority.get("actor_readback") or {}
        tenant_projection = self.adapter.read_tenant_projection(self.context, self._delivery)
        user_projection = self.adapter.read_user_projection(self.context, self._delivery)
        if not tenant_projection or not user_projection: raise LiveExecutorError("PROJECTION_READBACK_FAILURE", "both projection readbacks required")
        org = self._pass(self.adapter.create_qms_organization(self.context, self._authority, self._delivery), "QMS_ORGANIZATION_FAILURE", "organization creation")
        org_id = _require_uuid(org.get("returned_id"), label="organization.returned_id")
        org_rb = self.adapter.read_qms_organization(self.context, org_id)
        process = self._pass(self.adapter.create_process(self.context, org_id, self._authority), "PROCESS_CREATION_FAILURE", "process creation")
        process_id = _require_uuid(process.get("returned_id"), label="process.returned_id")
        process_rb = self.adapter.read_process(self.context, process_id)
        records = {
            "tenant": self._identity("tenant", self._authority.get("tenant_id"), tenant_rb.get("id"), "LIVE_UPSTREAM_EXTERNAL_AUTHORITY", "AdminApps"),
            "actor": self._identity("actor", self._authority.get("actor_id"), actor_rb.get("id"), "LIVE_UPSTREAM_EXTERNAL_AUTHORITY", "AdminApps"),
            "tenant_projection": self._identity("tenant_projection", self._delivery.get("tenant_projection_id"), tenant_projection.get("id"), "LIVE_ISOSMART_LOCAL_PROJECTION", "ISO Smart"),
            "user_projection": self._identity("user_projection", self._delivery.get("user_projection_id"), user_projection.get("id"), "LIVE_ISOSMART_LOCAL_PROJECTION", "ISO Smart"),
            "organization": self._identity("organization", org_id, org_rb.get("id"), "LIVE_ISOSMART_QMS_NATIVE", "ISO Smart/QMS"),
            "process": self._identity("process", process_id, process_rb.get("id"), "LIVE_ISOSMART_QMS_NATIVE", "ISO Smart/QMS"),
        }
        self.stage_ext_values = {"retry_id": self.context.run_id, "tenant_id": records["tenant"]["returned_value"],
            "actor_id": records["actor"]["returned_value"], "tenant_projection_id": records["tenant_projection"]["returned_value"],
            "user_projection_id": records["user_projection"]["returned_value"], "organization_id": records["organization"]["returned_value"],
            "process_id": records["process"]["returned_value"]}
        self.stage_ext_evidence = {"status": "PASS", "resolved_identity_count": 6, "identity_summary": records, "run_id": self.context.run_id}
        return self.stage_ext_evidence

    def stage_ext(self, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
        self.bootstrap_runtime(); self.start_services(); return self.resolve_stage_ext_identities()

    def build_capture_bundle(self) -> CaptureBundle:
        if self.stage_ext_evidence.get("resolved_identity_count") != 6: raise LiveExecutorError("CAPTURE_BUNDLE_FAILURE", "Stage EXT 6/6 required")
        for record in self.stage_ext_evidence.get("identity_summary", {}).values():
            if not record.get("persisted_readback_value") or any(w in str(record.get("provenance", "")).lower() for w in FORBIDDEN_PROVENANCE):
                raise LiveExecutorError("CAPTURE_BUNDLE_FAILURE", "non-live Stage EXT evidence rejected")
        try:
            bundle = CaptureBundle.from_stage_ext(self.stage_ext_values, retry_id=self.context.run_id); bundle.validate_for_retry(self.context.run_id)
        except Exception as exc: raise LiveExecutorError("CAPTURE_BUNDLE_FAILURE", str(exc)) from exc
        return bundle

    def prepare_runtime(self) -> Any:
        bundle = self.build_capture_bundle()
        runtime = self.runtime_factory(project_root=self.context.repository_root, capture_bundle=bundle, retry_id=self.context.run_id)
        if not callable(getattr(runtime, "run_clean_retry", None)): raise LiveExecutorError("RUNTIME_HANDOFF_FAILURE", "runtime lacks run_clean_retry()")
        runtime.session.composition.update(live_executor=self.context.run_id, capture_bundle=bundle, stage_ext=self.stage_ext_evidence)
        if self.allow_runtime_execution: runtime.run_clean_retry()
        return runtime

    def stop_services(self) -> Mapping[str, Any]: return self.adapter.stop_services()
