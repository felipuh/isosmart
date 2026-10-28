"""Real PostgreSQL 18.6 Phase 29 exact retained publication POC."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import threading
import time
from uuid import NAMESPACE_URL, UUID, uuid5

import postgres_foundation_harness as phase3
import postgres_phase19_harness as phase19


ROOT = Path(__file__).resolve().parents[2]
PHASE283 = ("foundation", "0023_retained_synthetic_source_reference_application")
POLICY_PATH = ROOT / "docs/governance/FIRST_RETAINED_SYNTHETIC_KNOWLEDGE_LAYER_RULE_PUBLICATION_POC_POLICY_V1.md"
NAMESPACE = uuid5(NAMESPACE_URL, "https://iso-smart.local/phase29/exact-retained-publication-poc/v1")
FAILURE_POINTS = (
    "after_claim", "after_authority_validation", "after_capability_admission",
    "after_lineage_lock", "after_target_revalidation", "after_status_update",
    "after_publication_insert", "after_event", "after_outbox", "after_audit",
    "before_commit",
)


def uid(name):
    return uuid5(NAMESPACE, name)


def require(value, message):
    if not value:
        raise AssertionError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def row_json(cursor, table, row_id):
    cursor.execute(f"SELECT to_jsonb(t) FROM {table} t WHERE id=%s", [str(row_id)])
    row = cursor.fetchone()
    require(row is not None, f"missing {table}/{row_id}")
    return json.loads(row[0]) if isinstance(row[0], str) else row[0]


def snapshot(cursor):
    cursor.execute(
        "SELECT r.status,r.published_at,"
        "(SELECT count(*) FROM normative.knowledge_layer_rule_governance_claim WHERE operation_kind='PUBLICATION'),"
        "(SELECT count(*) FROM normative.knowledge_layer_rule_publication),"
        "(SELECT count(*) FROM normative.knowledge_layer_rule_governance_event WHERE event_type='knowledge_layer_rule.published'),"
        "(SELECT count(*) FROM eventing.knowledge_layer_rule_governance_outbox),"
        "(SELECT count(*) FROM audit.knowledge_layer_rule_governance_audit WHERE operation_kind='PUBLICATION'),"
        "(SELECT count(*) FROM normative.knowledge_layer_rule_activation),"
        "(SELECT count(*) FROM normative.knowledge_layer_rule_runtime_adoption) "
        "FROM normative.knowledge_layer_rule r WHERE r.id=%s",
        ["01a0682b-dfc8-7b49-a601-f9bda29a70a5"],
    )
    return cursor.fetchone()


def retained_items(creation, disposition, source):
    chain = creation["governance_chain"]
    items = [
        ("source_manifest", source["deterministic_source_id"], source["manifest_material_hash"], dict(source)),
        ("creation_manifest", creation["run_id"], creation["manifest_material_hash"], creation),
        ("creation_disposition", disposition["run_id"], disposition["disposition_material_hash"], disposition),
        ("root", creation["root"]["id"], creation["root"]["full_material_hash"], creation["canonical_root_material"]),
        ("candidate", creation["candidate"]["id"], creation["candidate"]["full_material_hash"], creation["canonical_rule_material"]),
        ("learning_signal", chain["learning_signal"]["id"], chain["learning_signal"]["material_hash"], chain["learning_signal"]["material"]),
        ("learning_proposal", chain["learning_proposal_revision"]["id"], chain["learning_proposal_revision"]["material_hash"], chain["learning_proposal_revision"]["material"]),
        ("canonical_delta", chain["canonical_delta"]["id"], chain["canonical_delta"]["material_hash"], chain["canonical_delta"]["material"]),
        ("review", chain["selected_reviews"][0]["id"], chain["selected_reviews"][0]["material_hash"], chain["selected_reviews"][0]["material"]),
        ("decision", chain["decision"]["id"], chain["decision"]["material_hash"], chain["decision"]["material"]),
        ("application_authorization", chain["application_authorization"]["id"], chain["application_authorization"]["material_hash"], chain["application_authorization"]["material"]),
        ("application_receipt", chain["application_receipt"]["id"], chain["application_receipt"]["material_hash"], chain["application_receipt"]["material"]),
        ("application_event", chain["domain_events"][0]["id"], chain["domain_events"][0]["material_hash"], chain["domain_events"][0]["material"]),
        ("application_outbox", chain["transactional_outbox"][0]["id"], chain["transactional_outbox"][0]["material_hash"], chain["transactional_outbox"][0]["material"]),
        ("application_audit", chain["immutable_audits"][0]["id"], chain["immutable_audits"][0]["material_hash"], chain["immutable_audits"][0]["material"]),
        ("curator_evidence", creation["curator_evidence"]["id"], creation["curator_evidence"]["material_hash"], creation["curator_evidence"]["material"]),
    ]
    items.extend(("policy", item["id"], item["material_hash"], item["material"]) for item in chain["policies"])
    return items


def install_exact_ephemeral_boundary(cursor, creation, disposition, source, policy):
    """Install a zero-selector exact import and publication boundary in this POC DB."""
    items = retained_items(creation, disposition, source)
    evidence_json = canonical([{"kind": kind, "id": str(item_id), "material_hash": digest, "material": material} for kind, item_id, digest, material in items])
    expected_hashes = canonical({f"{kind}:{item_id}": digest for kind, item_id, digest, _ in items})
    root = creation["canonical_root_material"]
    candidate = creation["canonical_rule_material"]
    actors = creation["role_actor_ids"]
    actor_list = ",".join(f"'{value}'::uuid" for key, value in actors.items() if key != "publisher")
    policy_hash = policy["material_hash"]
    publisher = actors["publisher"]

    cursor.execute("""
        CREATE TABLE normative.phase29_retained_evidence_import(
          evidence_kind text NOT NULL, evidence_id uuid NOT NULL, material_hash char(64) NOT NULL,
          material jsonb NOT NULL, imported_at timestamptz NOT NULL DEFAULT statement_timestamp(),
          PRIMARY KEY(evidence_kind,evidence_id));
        CREATE TABLE normative.phase29_import_state_history(
          sequence integer PRIMARY KEY, state text NOT NULL UNIQUE CHECK(state IN
          ('RETAINED_EVIDENCE_ONLY','IMPORTED_UNPUBLISHED','PUBLICATION_PRECOMMIT_ELIGIBLE','PUBLISHED')),
          occurred_at timestamptz NOT NULL DEFAULT statement_timestamp());
        CREATE TABLE normative.phase29_publisher_authority_decision(
          id uuid PRIMARY KEY, predecessor_id uuid REFERENCES normative.phase29_publisher_authority_decision(id),
          actor_external_id uuid NOT NULL, decision_hash char(64) NOT NULL, allowed boolean NOT NULL,
          evaluated_at timestamptz NOT NULL, expires_at timestamptz NOT NULL,
          CHECK(expires_at>evaluated_at), UNIQUE NULLS NOT DISTINCT(predecessor_id));
        CREATE FUNCTION normative.phase29_reject_mutation() RETURNS trigger LANGUAGE plpgsql
          SET search_path=pg_catalog AS $f$ BEGIN RAISE EXCEPTION 'Phase 29 retained history is immutable'; END $f$;
        CREATE TRIGGER phase29_evidence_immutable BEFORE UPDATE OR DELETE ON normative.phase29_retained_evidence_import
          FOR EACH ROW EXECUTE FUNCTION normative.phase29_reject_mutation();
        CREATE TRIGGER phase29_state_immutable BEFORE UPDATE OR DELETE ON normative.phase29_import_state_history
          FOR EACH ROW EXECUTE FUNCTION normative.phase29_reject_mutation();
        CREATE TRIGGER phase29_authority_immutable BEFORE UPDATE OR DELETE ON normative.phase29_publisher_authority_decision
          FOR EACH ROW EXECUTE FUNCTION normative.phase29_reject_mutation();
        REVOKE ALL ON normative.phase29_retained_evidence_import,normative.phase29_import_state_history,
          normative.phase29_publisher_authority_decision FROM PUBLIC;
    """)
    import_sql = f"""
      CREATE FUNCTION normative.import_phase29_exact_retained_candidate_v1() RETURNS uuid
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $f$
      DECLARE evidence jsonb := $json${evidence_json}$json$::jsonb; item jsonb;
      BEGIN
        IF current_setting('app.phase29_import_capability',true) <> 'EXACT_RETAINED_CANDIDATE_ONLY' THEN
          RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='exact Phase 29 import capability required'; END IF;
        IF EXISTS(SELECT 1 FROM normative.phase29_import_state_history) THEN RAISE EXCEPTION 'exact import already consumed'; END IF;
        INSERT INTO normative.phase29_import_state_history VALUES(1,'RETAINED_EVIDENCE_ONLY',statement_timestamp());
        INSERT INTO normative.standard(id,code,title,publisher) VALUES
          ('{root['standard_id']}','SYNTHETIC-TEST-ONLY-NON-OFFICIAL-P29','Non-official retained synthetic fixture; non-normative and non-licensed','ISO SMART SYNTHETIC FIXTURE — NOT ISO');
        INSERT INTO normative.standard_edition(id,standard_id,edition,status,source_hash) VALUES
          ('{root['standard_edition_id']}','{root['standard_id']}','fixture-v1-non-production','published','{root['standard_edition_source_hash']}');
        INSERT INTO normative.knowledge_layer(id,standard_edition_id,layer_type,certifiability_classification) VALUES
          ('{root['knowledge_layer_id']}','{root['standard_edition_id']}','{root['knowledge_layer_type']}','non_certifiable_guidance');
        INSERT INTO normative.knowledge_layer_rule(id,knowledge_layer_id,lineage_id,rule_key,version,previous_revision_id,status,logic_json,evidence_expectation,source_reference,certifiability_classification,published_at)
        VALUES ('{root['id']}','{root['knowledge_layer_id']}','{root['lineage_id']}','{root['rule_key']}','{root['version']}',NULL,'draft',$logic${canonical(root['logic_json'])}$logic$::jsonb,$expect${canonical(root['evidence_expectation'])}$expect$::jsonb,'{root['source_reference']}','non_certifiable_guidance',NULL);
        UPDATE normative.knowledge_layer_rule SET status='published',published_at=statement_timestamp() WHERE id='{root['id']}';
        INSERT INTO normative.knowledge_layer_rule(id,knowledge_layer_id,lineage_id,rule_key,version,previous_revision_id,status,logic_json,evidence_expectation,source_reference,certifiability_classification,published_at)
        VALUES ('{candidate['id']}','{candidate['knowledge_layer_id']}','{candidate['lineage_id']}','{candidate['rule_key']}','{candidate['version']}','{candidate['previous_revision_id']}','draft',$logic${canonical(candidate['logic_json'])}$logic$::jsonb,$expect${canonical(candidate['evidence_expectation'])}$expect$::jsonb,'{candidate['source_reference']}','non_certifiable_guidance',NULL);
        FOR item IN SELECT value FROM jsonb_array_elements(evidence) LOOP
          INSERT INTO normative.phase29_retained_evidence_import(evidence_kind,evidence_id,material_hash,material)
          VALUES(item->>'kind',(item->>'id')::uuid,item->>'material_hash',item->'material');
        END LOOP;
        INSERT INTO normative.curation_audit(id,action,entity_type,entity_id,actor_id,trace_id,payload_hash,occurred_at)
        VALUES('{uid('import-audit')}','knowledge_layer_rule.phase29_retained_evidence_imported','knowledge_layer_rule','{candidate['id']}',
          'phase29-retained-evidence-bootstrap','{uid('import-trace')}','{creation['manifest_material_hash']}',statement_timestamp());
        INSERT INTO normative.phase29_import_state_history VALUES(2,'IMPORTED_UNPUBLISHED',statement_timestamp());
        RETURN '{candidate['id']}'::uuid;
      END $f$;
      REVOKE ALL ON FUNCTION normative.import_phase29_exact_retained_candidate_v1() FROM PUBLIC;
    """
    cursor.execute(import_sql)
    precommit_sql = f"""
      CREATE FUNCTION normative.phase29_mark_exact_publication_precommit_eligible_v1() RETURNS void
      LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $f$
      DECLARE expected jsonb := $json${expected_hashes}$json$::jsonb;
      BEGIN
        IF (SELECT array_agg(state ORDER BY sequence) FROM normative.phase29_import_state_history)
           IS DISTINCT FROM ARRAY['RETAINED_EVIDENCE_ONLY','IMPORTED_UNPUBLISHED'] THEN RAISE EXCEPTION 'invalid import state'; END IF;
        IF EXISTS(SELECT 1 FROM jsonb_each_text(expected) e WHERE NOT EXISTS(
          SELECT 1 FROM normative.phase29_retained_evidence_import i
          WHERE i.evidence_kind=split_part(e.key,':',1) AND i.evidence_id=split_part(e.key,':',2)::uuid AND i.material_hash=e.value))
          OR (SELECT count(*) FROM normative.phase29_retained_evidence_import) <> {len(items)} THEN RAISE EXCEPTION 'retained evidence exact comparison failed'; END IF;
        IF normative.foundation_0022_rule_material_hash('{candidate['id']}') <> '{creation['candidate']['full_material_hash']}'
          OR normative.foundation_0022_rule_semantic_hash('{candidate['id']}') <> '{creation['candidate']['lifecycle_hash']}'
          OR NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule r WHERE r.id='{candidate['id']}' AND r.status='draft' AND r.published_at IS NULL
             AND r.previous_revision_id='{root['id']}' AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule c WHERE c.previous_revision_id=r.id))
          OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_publication)
          OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_activation)
          OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption) THEN RAISE EXCEPTION 'publication precommit target mismatch'; END IF;
        INSERT INTO normative.phase29_import_state_history VALUES(3,'PUBLICATION_PRECOMMIT_ELIGIBLE',statement_timestamp());
      END $f$;
      REVOKE ALL ON FUNCTION normative.phase29_mark_exact_publication_precommit_eligible_v1() FROM PUBLIC;
    """
    cursor.execute(precommit_sql)
    publish_sql = f"""
      CREATE FUNCTION normative.publish_phase29_exact_retained_candidate_v1(p_publication_id uuid,p_idempotency_hash text,p_reason text,p_trace uuid)
      RETURNS TABLE(artifact_id uuid,replayed boolean) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $f$
      DECLARE prior record; auth record; material text; op_hash text; v_event_id uuid:=normative.foundation_0022_uuid(p_publication_id,'event');
        v_outbox_id uuid:=normative.foundation_0022_uuid(p_publication_id,'outbox'); v_audit_id uuid:=normative.foundation_0022_uuid(p_publication_id,'audit');
        curation_id uuid:=normative.foundation_0022_uuid(p_publication_id,'curation'); payload jsonb; published timestamptz:=statement_timestamp();
      BEGIN
        PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.publish');
        SELECT * INTO auth FROM normative.phase29_publisher_authority_decision d WHERE NOT EXISTS
          (SELECT 1 FROM normative.phase29_publisher_authority_decision n WHERE n.predecessor_id=d.id);
        IF auth.id IS NULL OR NOT auth.allowed OR auth.id::text<>current_setting('app.authority_decision_reference',true)
          OR auth.actor_external_id::text<>current_setting('app.actor_id',true) OR auth.actor_external_id<>'{publisher}'
          OR auth.decision_hash<>current_setting('app.authority_decision_hash',true)
          OR statement_timestamp() NOT BETWEEN auth.evaluated_at AND auth.expires_at
          OR current_setting('app.publication_policy_hash',true)<>'{policy_hash}'
          OR current_setting('app.governance_policy_version',true)<>'v1' THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='fresh exact Phase 29 authority/policy denied'; END IF;
        PERFORM normative.foundation_0022_fail('after_authority_validation');
        IF NOT normative.foundation_0022_capability_enabled('PUBLICATION') THEN RAISE EXCEPTION 'publication capability disabled'; END IF;
        PERFORM normative.foundation_0022_fail('after_capability_admission');
        IF auth.actor_external_id=ANY(ARRAY[{actor_list}]) THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='publisher actor separation of duties denied'; END IF;
        material:=normative.foundation_0022_rule_material_hash('{candidate['id']}');
        op_hash:=encode(sha256(convert_to('{candidate['id']}:{creation['candidate']['lineage_id']}:{creation['candidate']['version']}:{creation['candidate']['full_material_hash']}:{creation['candidate']['semantic_fingerprint']}:{creation['candidate']['lifecycle_hash']}:{creation['source']['manifest_hash']}:{creation['manifest_material_hash']}:{disposition['disposition_material_hash']}:{creation['governance_chain']['application_receipt']['id']}:{creation['curator_evidence']['id']}:'||auth.id::text||':{policy_hash}:'||p_reason,'UTF8')),'hex');
        PERFORM pg_advisory_xact_lock(hashtextextended('{root['id']}',29));
        PERFORM normative.foundation_0022_fail('after_lineage_lock');
        SELECT * INTO prior FROM normative.knowledge_layer_rule_publication WHERE id=p_publication_id OR idempotency_key_hash=p_idempotency_hash;
        IF prior.id IS NOT NULL THEN
          IF prior.id=p_publication_id AND prior.knowledge_layer_rule_id='{candidate['id']}' AND prior.operation_material_hash=op_hash THEN RETURN QUERY SELECT prior.id,true; RETURN; END IF;
          RAISE EXCEPTION 'publication identity conflict'; END IF;
        IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim gc WHERE gc.artifact_id=p_publication_id OR (gc.operation_kind='PUBLICATION' AND gc.idempotency_key_hash=p_idempotency_hash)) THEN RAISE EXCEPTION 'publication identity conflict: claim exists'; END IF;
        PERFORM 1 FROM normative.knowledge_layer_rule WHERE id='{candidate['id']}' FOR UPDATE;
        IF material<>'{creation['candidate']['full_material_hash']}' OR normative.foundation_0022_rule_semantic_hash('{candidate['id']}')<>'{creation['candidate']['lifecycle_hash']}'
          OR NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule r WHERE r.id='{candidate['id']}' AND r.lineage_id='{root['id']}' AND r.previous_revision_id='{root['id']}' AND r.version='sN+1' AND r.status='draft' AND r.published_at IS NULL
             AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule child WHERE child.previous_revision_id=r.id))
          OR (SELECT array_agg(state ORDER BY sequence) FROM normative.phase29_import_state_history) IS DISTINCT FROM ARRAY['RETAINED_EVIDENCE_ONLY','IMPORTED_UNPUBLISHED','PUBLICATION_PRECOMMIT_ELIGIBLE']
          OR NOT EXISTS(SELECT 1 FROM normative.phase29_retained_evidence_import WHERE evidence_kind='application_receipt' AND evidence_id='{creation['governance_chain']['application_receipt']['id']}' AND material_hash='{creation['governance_chain']['application_receipt']['material_hash']}')
          OR NOT EXISTS(SELECT 1 FROM normative.phase29_retained_evidence_import WHERE evidence_kind='curator_evidence' AND evidence_id='{creation['curator_evidence']['id']}' AND material_hash='{creation['curator_evidence']['material_hash']}')
          OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_activation) OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption)
          THEN RAISE EXCEPTION 'exact retained target revalidation failed'; END IF;
        PERFORM normative.foundation_0022_fail('after_target_revalidation');
        INSERT INTO normative.knowledge_layer_rule_governance_claim(id,operation_kind,artifact_id,target_rule_id,idempotency_key_hash,operation_material_hash,event_id,outbox_id,audit_id,trace_id,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version)
          VALUES(p_publication_id,'PUBLICATION',p_publication_id,'{candidate['id']}',p_idempotency_hash,op_hash,v_event_id,v_outbox_id,v_audit_id,p_trace,auth.actor_external_id,current_setting('app.authority_context_version',true),auth.id::text,'v1');
        PERFORM normative.foundation_0022_fail('after_claim');
        INSERT INTO normative.curation_audit(id,action,entity_type,entity_id,actor_id,trace_id,payload_hash,occurred_at)
          VALUES(curation_id,'knowledge_layer_rule.published','knowledge_layer_rule','{candidate['id']}',auth.actor_external_id::text,p_trace,op_hash,published);
        UPDATE normative.knowledge_layer_rule SET status='published',published_at=published WHERE id='{candidate['id']}';
        PERFORM normative.foundation_0022_fail('after_status_update');
        payload:=jsonb_build_object('publication_id',p_publication_id::text,'candidate_id','{candidate['id']}','lineage_id','{root['id']}','version','sN+1',
          'candidate_material_hash','{creation['candidate']['full_material_hash']}','semantic_fingerprint','{creation['candidate']['semantic_fingerprint']}','lifecycle_hash','{creation['candidate']['lifecycle_hash']}',
          'source_manifest_hash','{creation['source']['manifest_hash']}','source_reference_hash','{creation['source']['reference_hash']}','creation_manifest_hash','{creation['manifest_material_hash']}',
          'creation_disposition_hash','{disposition['disposition_material_hash']}','application_receipt_id','{creation['governance_chain']['application_receipt']['id']}',
          'curator_evidence_id','{creation['curator_evidence']['id']}','publisher_actor_id',auth.actor_external_id::text,'publisher_authority_decision_id',auth.id::text,
          'publisher_authority_decision_hash',auth.decision_hash,'publication_policy_id','first-retained-synthetic-klr-publication-poc-policy/v1','publication_policy_hash','{policy_hash}',
          'trace_id',p_trace::text,'occurred_at',published,'activated',false,'runtime_adopted',false,'runtime_effect_changed',false,'licensed_content_present',false);
        INSERT INTO normative.knowledge_layer_rule_publication(id,evidence_kind,workflow_approved,knowledge_layer_rule_id,knowledge_layer_id,lineage_id,rule_version,rule_material_hash,semantic_fingerprint,curation_audit_id,historical_published_at,evidence_imported_at,evidence_reference,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,authorized_at,reason,idempotency_key_hash,operation_material_hash,claim_id,event_id,outbox_id,audit_id,trace_id)
          VALUES(p_publication_id,'NATIVE',true,'{candidate['id']}','{candidate['knowledge_layer_id']}','{root['id']}','sN+1','{creation['candidate']['full_material_hash']}','{creation['candidate']['semantic_fingerprint']}',curation_id,published,NULL,NULL,auth.actor_external_id,current_setting('app.authority_context_version',true),auth.id::text,'v1',published,p_reason,p_idempotency_hash,op_hash,p_publication_id,v_event_id,v_outbox_id,v_audit_id,p_trace);
        PERFORM normative.foundation_0022_fail('after_publication_insert');
        INSERT INTO normative.knowledge_layer_rule_governance_event(id,event_type,schema_version,operation_kind,artifact_id,target_rule_id,payload,payload_hash,trace_id,occurred_at)
          VALUES(v_event_id,'knowledge_layer_rule.published',1,'PUBLICATION',p_publication_id,'{candidate['id']}',payload,encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(payload),'UTF8')),'hex'),p_trace,published);
        PERFORM normative.foundation_0022_fail('after_event');
        INSERT INTO eventing.knowledge_layer_rule_governance_outbox(id,event_id,destination,status,available_at,created_at)
          VALUES(v_outbox_id,v_event_id,'platform.knowledge-layer-rule-governance','pending',published,published);
        PERFORM normative.foundation_0022_fail('after_outbox');
        INSERT INTO audit.knowledge_layer_rule_governance_audit(id,operation_kind,artifact_id,target_rule_id,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,operation_material_hash,trace_id,payload_hash,occurred_at)
          VALUES(v_audit_id,'PUBLICATION',p_publication_id,'{candidate['id']}',auth.actor_external_id,current_setting('app.authority_context_version',true),auth.id::text,'v1',op_hash,p_trace,encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(payload),'UTF8')),'hex'),published);
        PERFORM normative.foundation_0022_fail('after_audit');
        INSERT INTO normative.phase29_import_state_history VALUES(4,'PUBLISHED',published);
        IF current_setting('foundation.phase29_precommit_delay',true)='true' THEN PERFORM pg_sleep(2); END IF;
        SELECT * INTO auth FROM normative.phase29_publisher_authority_decision d WHERE NOT EXISTS(SELECT 1 FROM normative.phase29_publisher_authority_decision n WHERE n.predecessor_id=d.id);
        IF NOT normative.foundation_0022_capability_enabled('PUBLICATION') OR auth.id::text<>current_setting('app.authority_decision_reference',true) OR NOT auth.allowed
          OR normative.foundation_0022_rule_material_hash('{candidate['id']}')<>'{creation['candidate']['full_material_hash']}'
          OR NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_publication p WHERE p.id=p_publication_id AND p.event_id=v_event_id AND p.outbox_id=v_outbox_id AND p.audit_id=v_audit_id)
          OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_activation) OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption)
          THEN RAISE EXCEPTION 'publication precommit drift'; END IF;
        PERFORM normative.foundation_0022_fail('before_commit');
        RETURN QUERY SELECT p_publication_id,false;
      END $f$;
      REVOKE ALL ON FUNCTION normative.publish_phase29_exact_retained_candidate_v1(uuid,text,text,uuid) FROM PUBLIC;
    """
    cursor.execute(publish_sql)
    owner = os.environ["FOUNDATION_RULE_GOVERNANCE_OWNER_ROLE"]
    publisher_role = os.environ["FOUNDATION_RULE_PUBLISHER_ROLE"]
    migrator = os.environ["FOUNDATION_MIGRATOR_ROLE"]
    cursor.execute(f'GRANT CREATE ON SCHEMA normative TO "{owner}"')
    cursor.execute(f'GRANT EXECUTE ON FUNCTION normative.publish_phase29_exact_retained_candidate_v1(uuid,text,text,uuid) TO "{publisher_role}"')
    cursor.execute(f'GRANT EXECUTE ON FUNCTION normative.phase29_mark_exact_publication_precommit_eligible_v1() TO "{migrator}"')
    cursor.execute(f'ALTER FUNCTION normative.publish_phase29_exact_retained_candidate_v1(uuid,text,text,uuid) OWNER TO "{owner}"')
    cursor.execute(f'ALTER FUNCTION normative.phase29_mark_exact_publication_precommit_eligible_v1() OWNER TO "{owner}"')
    cursor.execute(f'REVOKE CREATE ON SCHEMA normative FROM "{owner}"')
    cursor.execute(f'GRANT SELECT ON normative.phase29_retained_evidence_import,normative.phase29_import_state_history,normative.phase29_publisher_authority_decision TO "{owner}"')
    cursor.execute(f'GRANT INSERT ON normative.phase29_import_state_history TO "{owner}"')
    cursor.execute(f'GRANT EXECUTE ON FUNCTION normative.import_phase29_exact_retained_candidate_v1() TO "{migrator}"')
    cursor.execute(f'SET ROLE "{owner}"')
    cursor.execute(f'GRANT EXECUTE ON FUNCTION normative.phase29_mark_exact_publication_precommit_eligible_v1() TO "{migrator}"')
    cursor.execute(f'REVOKE EXECUTE ON FUNCTION normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid),normative.import_knowledge_layer_rule_publication_evidence_v1(uuid,uuid,text,uuid,timestamptz,text,text,text,uuid,uuid) FROM "{publisher_role}"')
    cursor.execute('RESET ROLE')


def run():
    phase19.run()
    from django.db import connections
    from foundation.phase29_exact_publication import (
        ExactPhase29PublicationConflict,
        ExactPhase29PublicationService,
        FreshPhase29PublicationAuthority,
    )
    from foundation.phase29_publication_evidence import (
        PUBLICATION_PATH,
        material_hash,
        publication_policy_material,
        retain_exclusive,
        verify_phase28_publication_inputs,
        verify_publication_manifest,
    )
    from foundation.knowledge_rule_release import (
        CAPABILITY_PERMISSION,
        GovernanceCapabilityService,
        TrustedCapabilityAuthority,
    )

    phase3.migrate(PHASE283)
    checks = []
    def check(name, condition=True):
        require(condition, name)
        checks.append(name)

    creation, disposition, source = verify_phase28_publication_inputs()
    check("offline retained evidence verified before database target")
    policy = publication_policy_material(POLICY_PATH)
    policy["material_hash"] = material_hash(policy)
    candidate_id = creation["candidate"]["id"]
    publication_id = uid("publication")
    trace_id = uid("publication-trace")
    idempotency_hash = material_hash({"phase": 29, "candidate": candidate_id, "operation": "publication"})

    with connections["default"].cursor() as cursor:
        cursor.execute("SHOW server_version_num")
        check("PostgreSQL exact 18.6", cursor.fetchone()[0] == "180006")
        install_exact_ephemeral_boundary(cursor, creation, disposition, source, policy)
        cursor.execute("SELECT set_config('app.phase29_import_capability','EXACT_RETAINED_CANDIDATE_ONLY',false)")
        cursor.execute("SELECT normative.import_phase29_exact_retained_candidate_v1()")
        check("exact retained candidate imported", str(cursor.fetchone()[0]) == candidate_id)
        imported = {}
        cursor.execute("SELECT evidence_kind,evidence_id::text,material_hash,material FROM normative.phase29_retained_evidence_import")
        for kind, evidence_id, digest, material in cursor.fetchall():
            imported[(kind, evidence_id)] = (digest, json.loads(material) if isinstance(material, str) else material)
        expected = retained_items(creation, disposition, source)
        check("post-import all retained rows byte/material exact", len(imported) == len(expected) and all(imported[(kind, str(item_id))] == (digest, material) for kind, item_id, digest, material in expected))
        check("import does not publish", snapshot(cursor)[0] == "draft" and snapshot(cursor)[1] is None and snapshot(cursor)[2:] == (0,0,0,0,0,0,0))
        cursor.execute("SELECT normative.phase29_mark_exact_publication_precommit_eligible_v1()")
        cursor.execute("SELECT array_agg(state ORDER BY sequence) FROM normative.phase29_import_state_history")
        check("explicit prepublication state machine", cursor.fetchone()[0] == ["RETAINED_EVIDENCE_ONLY","IMPORTED_UNPUBLISHED","PUBLICATION_PRECOMMIT_ELIGIBLE"])

    now = datetime.now(timezone.utc)
    authority_id = uid("publisher-authority-allow-1")
    authority_hash = material_hash({"decision": str(authority_id), "actor": creation["role_actor_ids"]["publisher"], "allowed": True})
    with connections["default"].cursor() as cursor:
        cursor.execute("INSERT INTO normative.phase29_publisher_authority_decision VALUES(%s,NULL,%s,%s,true,%s,%s)",
          [str(authority_id), creation["role_actor_ids"]["publisher"], authority_hash, now, now + timedelta(minutes=10)])
    def authority(decision_id=authority_id, decision_hash=authority_hash, evaluated=now):
        return FreshPhase29PublicationAuthority(UUID(creation["role_actor_ids"]["publisher"]), decision_id, decision_hash,
          "adminapps-phase29-publication/v1", "v1", policy["material_hash"], evaluated.isoformat(),
          (evaluated + timedelta(minutes=10)).isoformat(), True, True, True,
          frozenset({"qms.knowledge_layer_rule.publish"}), True)
    service = ExactPhase29PublicationService()

    with connections["default"].cursor() as cursor:
        baseline = snapshot(cursor)
    for point in FAILURE_POINTS:
        with connections["rule_publisher"].cursor() as cursor:
            cursor.execute("SELECT set_config('foundation.phase272_failure_point',%s,false)", [point])
        try:
            service.publish(authority=authority(), publication_id=publication_id, idempotency_key_hash=idempotency_hash, reason="Exact retained synthetic Phase 29 publication POC.", trace_id=trace_id)
        except Exception:
            pass
        else:
            raise AssertionError(f"publication committed at injected failure point {point}")
        finally:
            with connections["rule_publisher"].cursor() as cursor:
                cursor.execute("SELECT set_config('foundation.phase272_failure_point','',false)")
        with connections["default"].cursor() as cursor:
            check(f"rollback {point}", snapshot(cursor) == baseline)

    # Capability race: disable appends while the fixed publication sleeps, so precommit denies and rolls back.
    controller_actor = uid("capability-controller")
    controller = TrustedCapabilityAuthority(controller_actor, frozenset({CAPABILITY_PERMISSION}), True, True, True,
      "adminapps-phase29-capability/v1", "phase29-capability-controller", "v1")
    cap_service = GovernanceCapabilityService()
    cap_disable = uid("capability-disable")
    with connections["rule_publisher"].cursor() as cursor:
        cursor.execute("SELECT set_config('foundation.phase29_precommit_delay','true',false)")
    race_error = []
    def delayed_publish():
        try:
            with connections["rule_publisher"].cursor() as cursor:
                cursor.execute("SELECT set_config('foundation.phase29_precommit_delay','true',false)")
            service.publish(authority=authority(), publication_id=publication_id, idempotency_key_hash=idempotency_hash, reason="Exact retained synthetic Phase 29 publication POC.", trace_id=trace_id)
        except Exception as exc:
            race_error.append(str(exc))
        finally:
            connections["rule_publisher"].close()
    thread = threading.Thread(target=delayed_publish)
    thread.start(); time.sleep(.5)
    cap_service.decide(authority=controller, decision_id=cap_disable, capability="PUBLICATION", enabled=False, expected_predecessor_id=None, reason="Phase 29 race disable", trace_id=uid("cap-disable-trace"))
    thread.join()
    check("capability disable race denied precommit", bool(race_error))
    cap_enable = uid("capability-enable")
    cap_service.decide(authority=controller, decision_id=cap_enable, capability="PUBLICATION", enabled=True, expected_predecessor_id=cap_disable, reason="Append-only Phase 29 re-enable", trace_id=uid("cap-enable-trace"))

    # Authority race: revoke the exact decision during the same precommit window.
    with connections["rule_publisher"].cursor() as cursor:
        cursor.execute("SELECT set_config('foundation.phase29_precommit_delay','true',false)")
    race_error.clear(); thread = threading.Thread(target=delayed_publish); thread.start(); time.sleep(.5)
    revoke_id = uid("publisher-authority-revoke")
    revoke_hash = material_hash({"decision": str(revoke_id), "allowed": False})
    with connections["default"].cursor() as cursor:
        cursor.execute("INSERT INTO normative.phase29_publisher_authority_decision VALUES(%s,%s,%s,%s,false,%s,%s)",
          [str(revoke_id), str(authority_id), creation["role_actor_ids"]["publisher"], revoke_hash, datetime.now(timezone.utc), datetime.now(timezone.utc)+timedelta(minutes=10)])
    thread.join(); check("authority revoked race denied precommit", bool(race_error))
    authority_id2 = uid("publisher-authority-allow-2")
    authority_hash2 = material_hash({"decision": str(authority_id2), "actor": creation["role_actor_ids"]["publisher"], "allowed": True})
    now2 = datetime.now(timezone.utc)
    with connections["default"].cursor() as cursor:
        cursor.execute("INSERT INTO normative.phase29_publisher_authority_decision VALUES(%s,%s,%s,%s,true,%s,%s)",
          [str(authority_id2), str(revoke_id), creation["role_actor_ids"]["publisher"], authority_hash2, now2, now2+timedelta(minutes=10)])
    live_authority = authority(authority_id2, authority_hash2, now2)

    with connections["rule_publisher"].cursor() as cursor:
        cursor.execute("SELECT set_config('foundation.phase29_precommit_delay','',false)")
    def publish_exact(_):
        try:
            return service.publish(authority=live_authority, publication_id=publication_id, idempotency_key_hash=idempotency_hash, reason="Exact retained synthetic Phase 29 publication POC.", trace_id=trace_id)
        finally:
            connections["rule_publisher"].close()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(publish_exact, range(2)))
    check("same exact publication concurrency one commit one replay", sorted(item.replayed for item in results) == [False, True])
    try:
        service.publish(authority=live_authority, publication_id=publication_id, idempotency_key_hash=idempotency_hash, reason="Changed material under same idempotency key.", trace_id=trace_id)
    except ExactPhase29PublicationConflict:
        check("changed publication material conflicts")
    else:
        raise AssertionError("changed publication material replayed")

    # The publisher cannot bypass the fixed function to target another candidate.
    with connections["rule_publisher"].cursor() as cursor:
        cursor.execute("SELECT has_function_privilege(current_user,'normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid)','EXECUTE')")
        check("generic native publisher revoked", cursor.fetchone()[0] is False)
        cursor.execute("SET search_path=pg_temp,public")
    with connections["default"].cursor() as cursor:
        final = snapshot(cursor)
        check("exactly one publication", final[0] == "published" and final[1] is not None and final[2:7] == (1,1,1,1,1))
        check("zero activation and RuntimeAdoption", final[7:] == (0,0))
        cursor.execute("SELECT array_agg(state ORDER BY sequence) FROM normative.phase29_import_state_history")
        states = cursor.fetchone()[0]
        check("publication state machine complete", states == [s for s in ("RETAINED_EVIDENCE_ONLY","IMPORTED_UNPUBLISHED","PUBLICATION_PRECOMMIT_ELIGIBLE","PUBLISHED")])
        claim = row_json(cursor, "normative.knowledge_layer_rule_governance_claim", publication_id)
        artifact = row_json(cursor, "normative.knowledge_layer_rule_publication", publication_id)
        event = row_json(cursor, "normative.knowledge_layer_rule_governance_event", artifact["event_id"])
        outbox = row_json(cursor, "eventing.knowledge_layer_rule_governance_outbox", artifact["outbox_id"])
        audit = row_json(cursor, "audit.knowledge_layer_rule_governance_audit", artifact["audit_id"])
        check("live publication graph exact", event["event_type"] == "knowledge_layer_rule.published" and event["schema_version"] == 1 and event["payload"]["application_receipt_id"] == creation["governance_chain"]["application_receipt"]["id"] and claim["event_id"] == event["id"] and outbox["event_id"] == event["id"] and audit["artifact_id"] == artifact["id"])
    with connections["release_repair"].cursor() as cursor:
        cursor.execute("SELECT outcome FROM normative.reconcile_knowledge_layer_rule_publication_v1(%s)", [str(publication_id)])
        check("ambiguous commit complete graph reconciles committed", cursor.fetchone()[0] == "COMMITTED")
        cursor.execute("SELECT outcome FROM normative.reconcile_knowledge_layer_rule_publication_v1(%s)", [str(uid("never-admitted"))])
        check("absent operation reconciles not committed", cursor.fetchone()[0] == "NOT_COMMITTED")

    def reference(material):
        return {"material_hash": material_hash(material), "material": material}
    publication_doc = {
      "manifest_schema":"governed-target-publication-evidence-manifest/v1","evidence_state":"PUBLISHED_AND_RETAINED",
      "candidate_id":candidate_id,"lineage_id":creation["candidate"]["lineage_id"],"candidate_version":creation["candidate"]["version"],
      "candidate_material_hash":creation["candidate"]["full_material_hash"],"semantic_fingerprint":creation["candidate"]["semantic_fingerprint"],
      "lifecycle_hash":creation["candidate"]["lifecycle_hash"],"source_manifest_hash":source["manifest_material_hash"],
      "creation_manifest_hash":creation["manifest_material_hash"],"creation_disposition_hash":disposition["disposition_material_hash"],
      "application_receipt_id":creation["governance_chain"]["application_receipt"]["id"],"curator_evidence":creation["curator_evidence"],
      "import_state_history":states,"publication":{"id":str(publication_id),"claim_id":str(publication_id),"event_id":event["id"],"outbox_id":outbox["id"],"audit_id":audit["id"],"trace_id":str(trace_id),"event_type":"knowledge_layer_rule.published","event_schema_version":1,"candidate_status_before":"draft","candidate_status_after":"published","published_at":artifact["historical_published_at"]},
      "live_graph":{"claim":reference(claim),"artifact":reference(artifact),"event":reference(event),"outbox":reference(outbox),"audit":reference(audit)},
      "publisher_authority":{"actor_external_id":str(live_authority.actor_external_id),"authority_decision_id":str(live_authority.authority_decision_id),"authority_decision_hash":live_authority.authority_decision_hash,"server_resolved":True,"mfa_verified":True,"access_active":True,"global_governance":True,"permission":"qms.knowledge_layer_rule.publish","evaluated_at":live_authority.evaluated_at,"expires_at":live_authority.expires_at},
      "publication_policy":policy,"role_actor_ids":creation["role_actor_ids"],"idempotency_key_hash":idempotency_hash,
      "runtime_effect_changed":False,"zero_effects":{"activation_rows":0,"runtime_adoption_rows":0,"activation_events":0,"runtime_adoption_events":0,"runtime_behavior_delta":0,"normative_delta":0,"automatic_learning_delta":0,"external_business_effects":0},
      "integrity_verified":True,"live_graph_verified":True,"exported_at":datetime.now(timezone.utc).isoformat(),
    }
    publication_doc["manifest_material_hash"] = material_hash(publication_doc)
    verify_publication_manifest(publication_doc)
    retain_exclusive(PUBLICATION_PATH, publication_doc)
    check("publication evidence retained before teardown")
    print(json.dumps({"status":"PASS","postgresql":"18.6","checks":len(checks),"publication_id":str(publication_id),"publication_manifest_hash":publication_doc["manifest_material_hash"],"rollback_matrix":f"{len(FAILURE_POINTS)}/{len(FAILURE_POINTS)} PASS","concurrency":"one commit + one replay PASS","activation_rows":0,"runtime_adoption_rows":0,"runtime_effect_changed":False},indent=2))


if __name__ == "__main__":
    run()
