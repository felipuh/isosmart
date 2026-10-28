"""Offline negative matrix for the isolated synthetic authority boundary."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from foundation.phase31_4_synthetic_authority import (
    AUTHORIZATION_PATH, FIXTURE_PATH, Phase314SyntheticAuthorityStore,
    ProductionSyntheticAuthorityReader, SyntheticAuthorityError, canonical_hash,
)
from foundation.phase31_4_v2_4_execution_wiring import OPERATIONS
from foundation.phase31_4_v2_4_execution_backend import V24ExecutionSession


class AuthorityTests(unittest.TestCase):
    def setUp(self):
        self.store = Phase314SyntheticAuthorityStore()
        self.reader = ProductionSyntheticAuthorityReader(self.store)

    def test_exact_baseline_and_fresh_immutable_reads(self):
        self.assertEqual(len(OPERATIONS), 29)
        for operation in OPERATIONS:
            first = self.reader.read(operation.operation_id)
            second = self.reader.read(operation.operation_id)
            self.assertIsNot(first, second)
            self.assertEqual(first, second)
            self.assertEqual(first["revision"], 1)
            self.assertIs(first["authorized"], True)
            self.assertEqual(first["canonical_hash"],
                             canonical_hash(first["canonical_authority_material"]))
            with self.assertRaises(TypeError):
                first["authorized"] = False
            with self.assertRaises(TypeError):
                first["canonical_authority_material"]["authorized"] = False

    def test_unknown_operation_and_wrong_tenant_fail_closed(self):
        with self.assertRaises(SyntheticAuthorityError):
            self.reader.read("unknown.operation")
        with self.assertRaises(SyntheticAuthorityError):
            self.store.read(OPERATIONS[0].operation_id, "wrong-tenant")

    def test_decision_tamper_negative_matrix(self):
        operation_id = OPERATIONS[0].operation_id
        original = deepcopy(self.store._current[operation_id])
        cases = [None,
                 {**original, "canonical_hash": "0" * 64},
                 {**original, "authorized": False},
                 {**original, "revision": 2},
                 {**original, "tenant_id": "wrong"}]
        for malformed in cases:
            with self.subTest(malformed=malformed):
                self.store._current[operation_id] = malformed
                with self.assertRaises(SyntheticAuthorityError):
                    self.reader.read(operation_id)
        del self.store._current[operation_id]
        with self.assertRaises(SyntheticAuthorityError):
            self.reader.read(operation_id)

    def test_declared_toctou_and_reset(self):
        scenario = "phase31.4-toctou-authority-revoke/v1"
        target = "action_plan.prepare"
        before = self.reader.read(target)
        self.store.apply_declared_toctou(scenario)
        after = self.reader.read(target)
        self.assertEqual((before["revision"], before["authorized"]), (1, True))
        self.assertEqual((after["revision"], after["authorized"]), (2, False))
        self.assertNotEqual(before, after)
        with self.assertRaises(SyntheticAuthorityError):
            self.store.apply_declared_toctou(scenario)
        with self.assertRaises(SyntheticAuthorityError):
            self.store.reset_declared_toctou("undeclared")
        self.store.reset_declared_toctou(scenario)
        self.assertEqual(before, self.reader.read(target))
        with self.assertRaises(SyntheticAuthorityError):
            self.store.reset_declared_toctou(scenario)

    def test_precommit_toctou_rolls_back(self):
        store = self.store
        class Port:
            commits = 0
            rollbacks = 0
            def begin(self, operation): pass
            def invoke(self, operation, material):
                store.apply_declared_toctou("phase31.4-toctou-authority-revoke/v1")
                return {}
            def reread(self, operation): return {}
            def commit(self, operation): self.commits += 1
            def rollback(self, operation): self.rollbacks += 1
            def checkpoint(self, phase, ledger): pass
        port = Port()
        session = V24ExecutionSession(port, self.reader)
        operation = next(op for op in OPERATIONS if op.operation_id == "action_plan.prepare")
        with self.assertRaises(Exception):
            session.execute_operation(operation)
        self.assertEqual(port.commits, 0)
        self.assertEqual(port.rollbacks, 1)

    def test_undeclared_transition_and_fixture_tamper(self):
        with self.assertRaises(SyntheticAuthorityError):
            self.store.apply_declared_toctou("undeclared")
        document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            fixture_path = Path(directory) / "fixture.json"
            authorization_path = Path(directory) / "authorization.json"
            fixture_path.write_text(json.dumps(document), encoding="utf-8")
            authorization_path.write_bytes(AUTHORIZATION_PATH.read_bytes())
            with self.assertRaises(SyntheticAuthorityError):
                Phase314SyntheticAuthorityStore(fixture_path, authorization_path)
            authorization = json.loads(AUTHORIZATION_PATH.read_text(encoding="utf-8"))
            authorization["fixture_sha256"] = sha256(fixture_path.read_bytes()).hexdigest()
            authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
            document["decisions"][0]["authorized"] = False
            fixture_path.write_text(json.dumps(document), encoding="utf-8")
            authorization["fixture_sha256"] = sha256(fixture_path.read_bytes()).hexdigest()
            authorization_path.write_text(json.dumps(authorization), encoding="utf-8")
            with self.assertRaises(SyntheticAuthorityError):
                Phase314SyntheticAuthorityStore(fixture_path, authorization_path)


if __name__ == "__main__":
    unittest.main()
