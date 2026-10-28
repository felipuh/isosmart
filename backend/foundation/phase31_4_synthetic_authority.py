"""Isolated Phase 31.4 POC control-plane authority; never contacts AdminApps."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping
from uuid import UUID, uuid5

from .phase31_4_v2_4_execution_wiring import OPERATIONS
from .phase31_4_v2_4_execution_backend import operation_classification
from .phase31_4_v2_4_support_producer import CONTRACT_PATH, CONTRACT_SHA256, EXPERIMENT_ID


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_RELATIVE = "docs/governance/evidence/PHASE31_4_SYNTHETIC_CONTROL_PLANE_AUTHORITY_FIXTURE_V1.json"
AUTHORIZATION_RELATIVE = "docs/governance/evidence/PHASE31_4_SYNTHETIC_AUTHORITY_FIXTURE_AUTHORIZATION_V1.json"
FIXTURE_PATH = ROOT / FIXTURE_RELATIVE
AUTHORIZATION_PATH = ROOT / AUTHORIZATION_RELATIVE
SCHEMA = "phase31.4-synthetic-control-plane-authority-fixture/v1"
CANONICALIZATION = "json-sort-keys-compact-utf8-sha256/v1"
NAMESPACE = uuid5(UUID(EXPERIMENT_ID), "phase31.4/synthetic-control-plane-authority/v1")


class SyntheticAuthorityError(RuntimeError):
    pass


def canonical_hash(material: Mapping[str, Any]) -> str:
    return sha256(json.dumps(dict(material), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=False, allow_nan=False).encode("utf-8")).hexdigest()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _tenant_id() -> str:
    if sha256(CONTRACT_PATH.read_bytes()).hexdigest() != CONTRACT_SHA256:
        raise SyntheticAuthorityError("frozen V2.4 contract changed")
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    if contract.get("experiment_id") != EXPERIMENT_ID:
        raise SyntheticAuthorityError("experiment identity changed")
    tenant = next(row for row in contract["field_bindings"] if
                  row["member_identity"]["qualified_table_or_artifact_index"] == "qms.tenant_projection")
    field = next(row for row in tenant["fields"] if row["name"] == "adminapps_tenant_id")
    return field["value_binding"]["typed_value"]


def expected_decision(operation, *, revision: int = 1, authorized: bool = True) -> dict[str, Any]:
    material = {
        "operation_id": operation.operation_id,
        "tenant_id": _tenant_id(),
        "authority_subject": operation.transaction_owner,
        "operation_classification": operation_classification(operation),
        "source_path": operation.source_path,
        "source_symbol": operation.symbol,
        "authorized": authorized,
        "revision": revision,
        "decision_id": str(uuid5(NAMESPACE, f"{operation.operation_id}/revision/{revision}")),
        "decision_source": "PHASE31.4_POC_SYNTHETIC_CONTROL_PLANE_FIXTURE",
        "effective_state": "AUTHORIZED" if authorized else "DENIED",
    }
    return {**material, "canonical_authority_material": material,
            "canonical_hash": canonical_hash(material)}


def _validate_decision(decision: Any, operation) -> None:
    if not isinstance(decision, dict):
        raise SyntheticAuthorityError("authority decision is malformed")
    revision = decision.get("revision")
    authorized = decision.get("authorized")
    if type(revision) is not int or revision < 1 or type(authorized) is not bool:
        raise SyntheticAuthorityError("authority revision or state is malformed")
    if decision != expected_decision(operation, revision=revision, authorized=authorized):
        raise SyntheticAuthorityError("authority identity or canonical hash differs")


class Phase314SyntheticAuthorityStore:
    """Fresh revisioned reads with only one frozen transition and explicit reset."""

    def __init__(self, fixture_path: Path = FIXTURE_PATH,
                 authorization_path: Path = AUTHORIZATION_PATH):
        fixture_bytes = fixture_path.read_bytes()
        authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
        if (authorization.get("fixture_path") != FIXTURE_RELATIVE
                or authorization.get("fixture_sha256") != sha256(fixture_bytes).hexdigest()
                or authorization.get("operation_count") != 29
                or authorization.get("v2_4_sha256") != CONTRACT_SHA256
                or authorization.get("test_only") is not True
                or authorization.get("nonproduction") is not True
                or authorization.get("real_adminapps_contact_prohibited") is not True):
            raise SyntheticAuthorityError("POC fixture authorization failed")
        graph_hash = sha256((ROOT / "backend/foundation/phase31_4_v2_4_execution_wiring.py")
                            .read_bytes()).hexdigest()
        if authorization.get("execution_graph_sha256") != graph_hash:
            raise SyntheticAuthorityError("frozen operation graph changed")
        fixture = json.loads(fixture_bytes)
        operations = {op.operation_id: op for op in OPERATIONS}
        if (len(operations) != 29 or fixture.get("schema") != SCHEMA
                or fixture.get("operation_count") != 29
                or fixture.get("experiment_id") != EXPERIMENT_ID
                or fixture.get("synthetic_tenant_id") != _tenant_id()
                or fixture.get("canonicalization") != CANONICALIZATION
                or fixture.get("decision_namespace_rule") !=
                'uuid5(UUID(experiment_id), "phase31.4/synthetic-control-plane-authority/v1")'
                or fixture.get("decision_id_rule") !=
                f'uuid5(UUID("{NAMESPACE}"), operation_id + "/revision/" + decimal_revision)'
                or fixture.get("source", {}).get("operation_graph_sha256") != graph_hash
                or fixture.get("classification") != ["TEST ONLY", "NONPRODUCTION",
                    "NONCERTIFIABLE", "SYNTHETIC CONTROL-PLANE AUTHORITY",
                    "PHASE31.4 POC ONLY", "NO REAL ADMINAPPS CONTACT"]):
            raise SyntheticAuthorityError("POC fixture schema or identity failed")
        decisions = fixture.get("decisions")
        if not isinstance(decisions, list) or len(decisions) != 29:
            raise SyntheticAuthorityError("POC decisions incomplete")
        ids = [row.get("operation_id") for row in decisions if isinstance(row, dict)]
        if len(ids) != 29 or len(set(ids)) != 29 or set(ids) != set(operations):
            raise SyntheticAuthorityError("POC operation decisions are not exact")
        for row in decisions:
            _validate_decision(row, operations[row["operation_id"]])
            if row["revision"] != 1 or row["authorized"] is not True:
                raise SyntheticAuthorityError("POC baseline is not authorized revision one")
        scenarios = fixture.get("toctou_scenarios")
        if not isinstance(scenarios, list) or len(scenarios) != 1:
            raise SyntheticAuthorityError("POC TOCTOU scenario is not exact")
        scenario = scenarios[0]
        target = scenario.get("target_operation_id")
        if (scenario.get("scenario_id") != "phase31.4-toctou-authority-revoke/v1"
                or target not in operations
                or scenario.get("initial_revision") != 1
                or scenario.get("initial_authorized") is not True
                or scenario.get("mutated_revision") != 2
                or scenario.get("mutated_authorized") is not False
                or scenario.get("expected_result") != "PRECOMMIT_AUTHORITY_MISMATCH_AND_ROLLBACK"
                or scenario.get("reset_operation") != "RESET_TO_IMMUTABLE_BASELINE"):
            raise SyntheticAuthorityError("POC TOCTOU scenario is invalid")
        self._operations = operations
        self._baseline = {row["operation_id"]: deepcopy(row) for row in decisions}
        self._current = deepcopy(self._baseline)
        self._scenario = scenario

    @property
    def tenant_id(self) -> str:
        return _tenant_id()

    def read(self, operation_id: str, tenant_id: str) -> Mapping[str, Any]:
        if operation_id not in self._operations or tenant_id != self.tenant_id:
            raise SyntheticAuthorityError("unknown operation or tenant")
        if operation_id not in self._current:
            raise SyntheticAuthorityError("authority decision missing")
        row = deepcopy(self._current[operation_id])
        _validate_decision(row, self._operations[operation_id])
        return _freeze(row)

    def apply_declared_toctou(self, scenario_id: str) -> None:
        scenario = self._scenario
        if scenario_id != scenario["scenario_id"]:
            raise SyntheticAuthorityError("undeclared authority transition")
        target = scenario["target_operation_id"]
        if self._current[target] != self._baseline[target]:
            raise SyntheticAuthorityError("authority transition is not from baseline")
        self._current[target] = expected_decision(self._operations[target], revision=2,
                                                  authorized=False)

    def reset_declared_toctou(self, scenario_id: str) -> None:
        scenario = self._scenario
        if scenario_id != scenario["scenario_id"]:
            raise SyntheticAuthorityError("undeclared authority reset")
        target = scenario["target_operation_id"]
        if self._current[target] != expected_decision(self._operations[target], revision=2,
                                                      authorized=False):
            raise SyntheticAuthorityError("authority reset is not from declared mutation")
        self._current[target] = deepcopy(self._baseline[target])


class ProductionSyntheticAuthorityReader:
    """Operation-scoped fresh reads from the validated POC store."""

    def __init__(self, store: Phase314SyntheticAuthorityStore):
        self._store = store
        self._operation_ids = frozenset(op.operation_id for op in OPERATIONS)

    def read(self, operation_id: str) -> Mapping[str, Any]:
        if operation_id not in self._operation_ids:
            raise SyntheticAuthorityError("unknown frozen operation")
        decision = self._store.read(operation_id, self._store.tenant_id)
        if decision["operation_id"] != operation_id:
            raise SyntheticAuthorityError("operation authority identity differs")
        return decision
