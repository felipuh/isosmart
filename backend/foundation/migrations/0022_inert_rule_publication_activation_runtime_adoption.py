"""Phase 27.2 inert KnowledgeLayerRule release-governance foundation."""

import uuid

from django.db import migrations, models
import django.db.models.deletion


FORWARD_SQL = r"""
DO $migration$
DECLARE
  owner_role text:=current_setting('foundation.rule_governance_owner_role',true);
  publisher_role text:=current_setting('foundation.rule_publisher_role',true);
  activator_role text:=current_setting('foundation.rule_activator_role',true);
  adopter_role text:=current_setting('foundation.rule_adopter_role',true);
  resolver_role text:=current_setting('foundation.rule_resolver_role',true);
  repair_role text:=current_setting('foundation.release_repair_role',true);
  controller_role text:=current_setting('foundation.release_controller_role',true);
BEGIN
  IF owner_role IS NULL OR publisher_role IS NULL OR activator_role IS NULL OR
     adopter_role IS NULL OR resolver_role IS NULL OR repair_role IS NULL OR
     controller_role IS NULL OR owner_role='' OR publisher_role='' OR
     activator_role='' OR adopter_role='' OR resolver_role='' OR repair_role='' OR
     controller_role='' THEN
    RAISE EXCEPTION 'Phase 27.2 exact governance roles are required';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=owner_role AND NOT rolcanlogin
                AND NOT rolsuper AND NOT rolbypassrls AND NOT rolinherit) THEN
    RAISE EXCEPTION 'Phase 27.2 owner role attributes are unsafe';
  END IF;
  IF EXISTS(SELECT 1 FROM pg_roles WHERE rolname IN
       (publisher_role,activator_role,adopter_role,resolver_role,repair_role,controller_role)
       AND (NOT rolcanlogin OR rolsuper OR rolbypassrls OR rolinherit)) THEN
    RAISE EXCEPTION 'Phase 27.2 LOGIN role attributes are unsafe';
  END IF;

  CREATE TABLE normative.knowledge_layer_rule_release_foundation (
    singleton boolean PRIMARY KEY DEFAULT true CHECK(singleton),
    installed_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );
  INSERT INTO normative.knowledge_layer_rule_release_foundation DEFAULT VALUES;

  CREATE TABLE normative.knowledge_layer_rule_governance_claim (
    id uuid PRIMARY KEY,
    operation_kind varchar(32) NOT NULL CHECK(operation_kind IN ('PUBLICATION','ACTIVATION','RUNTIME_ADOPTION')),
    artifact_id uuid NOT NULL UNIQUE,
    target_rule_id uuid REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    idempotency_key_hash char(64) NOT NULL CHECK(idempotency_key_hash ~ '^[0-9a-f]{64}$'),
    operation_material_hash char(64) NOT NULL CHECK(operation_material_hash ~ '^[0-9a-f]{64}$'),
    event_id uuid,
    outbox_id uuid,
    audit_id uuid,
    trace_id uuid NOT NULL,
    actor_external_id uuid NOT NULL,
    authority_context_version varchar(160) NOT NULL CHECK(btrim(authority_context_version)<>''),
    authority_decision_reference varchar(255) NOT NULL CHECK(btrim(authority_decision_reference)<>''),
    governance_policy_version varchar(160) NOT NULL CHECK(btrim(governance_policy_version)<>''),
    admitted_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    UNIQUE(operation_kind,idempotency_key_hash),
    CHECK((event_id IS NULL AND outbox_id IS NULL AND audit_id IS NULL) OR
          (event_id IS NOT NULL AND outbox_id IS NOT NULL AND audit_id IS NOT NULL))
  );

  CREATE TABLE normative.knowledge_layer_rule_publication (
    id uuid PRIMARY KEY,
    evidence_kind varchar(32) NOT NULL CHECK(evidence_kind IN ('NATIVE','LEGACY_EVIDENCE_IMPORT')),
    workflow_approved boolean NOT NULL,
    knowledge_layer_rule_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    knowledge_layer_id uuid NOT NULL REFERENCES normative.knowledge_layer(id) ON DELETE RESTRICT,
    lineage_id uuid NOT NULL,
    rule_version varchar(120) NOT NULL CHECK(btrim(rule_version)<>''),
    rule_material_hash char(64) NOT NULL CHECK(rule_material_hash ~ '^[0-9a-f]{64}$'),
    semantic_fingerprint char(64) NOT NULL CHECK(semantic_fingerprint ~ '^[0-9a-f]{64}$'),
    curation_audit_id uuid NOT NULL UNIQUE REFERENCES normative.curation_audit(id) ON DELETE RESTRICT,
    historical_published_at timestamptz,
    evidence_imported_at timestamptz,
    evidence_reference varchar(500),
    actor_external_id uuid NOT NULL,
    authority_context_version varchar(160) NOT NULL,
    authority_decision_reference varchar(255) NOT NULL,
    governance_policy_version varchar(160) NOT NULL,
    authorized_at timestamptz NOT NULL,
    reason varchar(500) NOT NULL CHECK(btrim(reason)<>''),
    idempotency_key_hash char(64) NOT NULL UNIQUE CHECK(idempotency_key_hash ~ '^[0-9a-f]{64}$'),
    operation_material_hash char(64) NOT NULL CHECK(operation_material_hash ~ '^[0-9a-f]{64}$'),
    claim_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule_governance_claim(id) ON DELETE RESTRICT,
    event_id uuid NOT NULL UNIQUE,
    outbox_id uuid NOT NULL UNIQUE,
    audit_id uuid NOT NULL UNIQUE,
    trace_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CHECK((evidence_kind='NATIVE' AND workflow_approved AND evidence_imported_at IS NULL) OR
          (evidence_kind='LEGACY_EVIDENCE_IMPORT' AND NOT workflow_approved AND
           evidence_imported_at IS NOT NULL AND evidence_reference IS NOT NULL)),
    CHECK(historical_published_at IS NULL OR evidence_imported_at IS NULL OR
          historical_published_at<>evidence_imported_at)
  );

  CREATE TABLE normative.knowledge_layer_rule_activation (
    id uuid PRIMARY KEY,
    publication_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule_publication(id) ON DELETE RESTRICT,
    knowledge_layer_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    knowledge_layer_id uuid NOT NULL REFERENCES normative.knowledge_layer(id) ON DELETE RESTRICT,
    lineage_id uuid NOT NULL,
    rule_version varchar(120) NOT NULL,
    rule_material_hash char(64) NOT NULL CHECK(rule_material_hash ~ '^[0-9a-f]{64}$'),
    semantic_fingerprint char(64) NOT NULL CHECK(semantic_fingerprint ~ '^[0-9a-f]{64}$'),
    predecessor_activation_id uuid REFERENCES normative.knowledge_layer_rule_activation(id) ON DELETE RESTRICT,
    compatibility_hash char(64) NOT NULL CHECK(compatibility_hash ~ '^[0-9a-f]{64}$'),
    actor_external_id uuid NOT NULL,
    authority_context_version varchar(160) NOT NULL,
    authority_decision_reference varchar(255) NOT NULL,
    governance_policy_version varchar(160) NOT NULL,
    authorized_at timestamptz NOT NULL,
    reason varchar(500) NOT NULL CHECK(btrim(reason)<>''),
    idempotency_key_hash char(64) NOT NULL UNIQUE CHECK(idempotency_key_hash ~ '^[0-9a-f]{64}$'),
    operation_material_hash char(64) NOT NULL CHECK(operation_material_hash ~ '^[0-9a-f]{64}$'),
    claim_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule_governance_claim(id) ON DELETE RESTRICT,
    event_id uuid NOT NULL UNIQUE,
    outbox_id uuid NOT NULL UNIQUE,
    audit_id uuid NOT NULL UNIQUE,
    trace_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    UNIQUE NULLS NOT DISTINCT(lineage_id,predecessor_activation_id)
  );

  CREATE TABLE normative.knowledge_layer_rule_runtime_adoption (
    id uuid PRIMARY KEY,
    adoption_kind varchar(32) NOT NULL CHECK(adoption_kind IN ('NATIVE','LEGACY_BOOTSTRAP')),
    activation_id uuid REFERENCES normative.knowledge_layer_rule_activation(id) ON DELETE RESTRICT,
    publication_id uuid REFERENCES normative.knowledge_layer_rule_publication(id) ON DELETE RESTRICT,
    knowledge_layer_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    knowledge_layer_id uuid NOT NULL REFERENCES normative.knowledge_layer(id) ON DELETE RESTRICT,
    lineage_id uuid NOT NULL,
    rule_version varchar(120) NOT NULL,
    rule_material_hash char(64) NOT NULL CHECK(rule_material_hash ~ '^[0-9a-f]{64}$'),
    semantic_fingerprint char(64) NOT NULL CHECK(semantic_fingerprint ~ '^[0-9a-f]{64}$'),
    predecessor_adoption_id uuid REFERENCES normative.knowledge_layer_rule_runtime_adoption(id) ON DELETE RESTRICT,
    release_configuration_reference varchar(500) NOT NULL CHECK(btrim(release_configuration_reference)<>''),
    release_configuration_hash char(64) NOT NULL CHECK(release_configuration_hash ~ '^[0-9a-f]{64}$'),
    historical_activation_claim boolean NOT NULL DEFAULT false CHECK(NOT historical_activation_claim),
    asserted_historical_effective_at timestamptz,
    bootstrap_imported_at timestamptz,
    actor_external_id uuid NOT NULL,
    authority_context_version varchar(160) NOT NULL,
    authority_decision_reference varchar(255) NOT NULL,
    governance_policy_version varchar(160) NOT NULL,
    authorized_at timestamptz NOT NULL,
    reason varchar(500) NOT NULL CHECK(btrim(reason)<>''),
    idempotency_key_hash char(64) NOT NULL UNIQUE CHECK(idempotency_key_hash ~ '^[0-9a-f]{64}$'),
    operation_material_hash char(64) NOT NULL CHECK(operation_material_hash ~ '^[0-9a-f]{64}$'),
    claim_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule_governance_claim(id) ON DELETE RESTRICT,
    event_id uuid NOT NULL UNIQUE,
    outbox_id uuid NOT NULL UNIQUE,
    audit_id uuid NOT NULL UNIQUE,
    trace_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    UNIQUE NULLS NOT DISTINCT(lineage_id,predecessor_adoption_id),
    CHECK((adoption_kind='NATIVE' AND activation_id IS NOT NULL AND publication_id IS NOT NULL AND
           bootstrap_imported_at IS NULL AND asserted_historical_effective_at IS NULL) OR
          (adoption_kind='LEGACY_BOOTSTRAP' AND activation_id IS NULL AND publication_id IS NULL AND
           bootstrap_imported_at IS NOT NULL AND asserted_historical_effective_at IS NULL))
  );

  CREATE TABLE normative.knowledge_layer_rule_governance_event (
    id uuid PRIMARY KEY,
    event_type varchar(180) NOT NULL CHECK(event_type IN
      ('knowledge_layer_rule.published','knowledge_layer_rule.publication_evidence_imported',
       'knowledge_layer_rule.activation_recorded','knowledge_layer_rule.runtime_adopted',
       'knowledge_layer_rule.legacy_runtime_bootstrapped')),
    schema_version integer NOT NULL CHECK(schema_version=1),
    operation_kind varchar(32) NOT NULL,
    artifact_id uuid NOT NULL UNIQUE,
    target_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    payload jsonb NOT NULL CHECK(jsonb_typeof(payload)='object'),
    payload_hash char(64) NOT NULL CHECK(payload_hash ~ '^[0-9a-f]{64}$'),
    trace_id uuid NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );

  CREATE TABLE eventing.knowledge_layer_rule_governance_outbox (
    id uuid PRIMARY KEY,
    event_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule_governance_event(id) ON DELETE RESTRICT,
    destination varchar(180) NOT NULL CHECK(destination='platform.knowledge-layer-rule-governance'),
    status varchar(24) NOT NULL DEFAULT 'pending' CHECK(status='pending'),
    available_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );

  CREATE TABLE audit.knowledge_layer_rule_governance_audit (
    id uuid PRIMARY KEY,
    operation_kind varchar(32) NOT NULL,
    artifact_id uuid NOT NULL UNIQUE,
    target_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    actor_external_id uuid NOT NULL,
    authority_context_version varchar(160) NOT NULL,
    authority_decision_reference varchar(255) NOT NULL,
    governance_policy_version varchar(160) NOT NULL,
    operation_material_hash char(64) NOT NULL,
    trace_id uuid NOT NULL,
    payload_hash char(64) NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );

  CREATE TABLE normative.knowledge_layer_rule_governance_disposition (
    id uuid PRIMARY KEY,
    claim_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule_governance_claim(id) ON DELETE RESTRICT,
    disposition varchar(24) NOT NULL CHECK(disposition='ABANDONED'),
    actor_external_id uuid NOT NULL,
    authority_context_version varchar(160) NOT NULL,
    authority_decision_reference varchar(255) NOT NULL,
    governance_policy_version varchar(160) NOT NULL,
    reason varchar(500) NOT NULL CHECK(btrim(reason)<>''),
    trace_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );

  CREATE TABLE normative.knowledge_layer_rule_capability_decision (
    id uuid PRIMARY KEY,
    capability varchar(32) NOT NULL CHECK(capability IN ('PUBLICATION','ACTIVATION','RUNTIME_ADOPTION')),
    enabled boolean NOT NULL,
    predecessor_decision_id uuid REFERENCES normative.knowledge_layer_rule_capability_decision(id) ON DELETE RESTRICT,
    actor_external_id uuid NOT NULL,
    authority_context_version varchar(160) NOT NULL,
    authority_decision_reference varchar(255) NOT NULL,
    governance_policy_version varchar(160) NOT NULL,
    reason varchar(500) NOT NULL CHECK(btrim(reason)<>''),
    trace_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    UNIQUE NULLS NOT DISTINCT(capability,predecessor_decision_id)
  );

  CREATE FUNCTION normative.foundation_0022_reject_mutation()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
  BEGIN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Phase 27.2 governance history is immutable'; END $fn$;

  CREATE TRIGGER klr_claim_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_governance_claim FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_publication_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_publication FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_activation_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_activation FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_adoption_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_runtime_adoption FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_governance_event_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_governance_event FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_governance_outbox_immutable BEFORE UPDATE OR DELETE ON eventing.knowledge_layer_rule_governance_outbox FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_governance_audit_immutable BEFORE UPDATE OR DELETE ON audit.knowledge_layer_rule_governance_audit FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_disposition_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_governance_disposition FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();
  CREATE TRIGGER klr_capability_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_capability_decision FOR EACH ROW EXECUTE FUNCTION normative.foundation_0022_reject_mutation();

  CREATE FUNCTION normative.foundation_0022_commit_window()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
  BEGIN
    IF current_setting('foundation.phase272_commit_delay',true)='true' THEN
      PERFORM pg_catalog.pg_sleep(5);
    END IF;
    RETURN NEW;
  END $fn$;
  CREATE CONSTRAINT TRIGGER klr_governance_commit_window
    AFTER INSERT ON normative.knowledge_layer_rule_governance_claim
    DEFERRABLE INITIALLY DEFERRED FOR EACH ROW
    EXECUTE FUNCTION normative.foundation_0022_commit_window();

  EXECUTE format('GRANT USAGE ON SCHEMA normative,eventing,audit TO %I,%I,%I,%I,%I,%I,%I',owner_role,publisher_role,activator_role,adopter_role,resolver_role,repair_role,controller_role);
  EXECUTE format('GRANT USAGE ON SCHEMA qms TO %I',owner_role);
  EXECUTE format('GRANT CREATE ON SCHEMA normative TO %I',owner_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer_rule_publication TO %I,%I,%I,%I',publisher_role,activator_role,adopter_role,repair_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer_rule_activation TO %I,%I,%I',activator_role,adopter_role,repair_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer_rule_runtime_adoption TO %I,%I,%I',adopter_role,resolver_role,repair_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer_rule_governance_claim,normative.knowledge_layer_rule_governance_event,eventing.knowledge_layer_rule_governance_outbox,audit.knowledge_layer_rule_governance_audit,normative.knowledge_layer_rule_governance_disposition TO %I',repair_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer_rule_capability_decision TO %I,%I',repair_role,controller_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer_rule_governance_claim,normative.knowledge_layer_rule_publication,normative.knowledge_layer_rule_activation,normative.knowledge_layer_rule_runtime_adoption,normative.knowledge_layer_rule_governance_event,normative.knowledge_layer_rule_governance_disposition,normative.knowledge_layer_rule_capability_decision,eventing.knowledge_layer_rule_governance_outbox,audit.knowledge_layer_rule_governance_audit TO %I',owner_role);
  EXECUTE format('GRANT UPDATE ON normative.knowledge_layer_rule_publication,normative.knowledge_layer_rule_activation,normative.knowledge_layer_rule_runtime_adoption,normative.knowledge_layer_rule_capability_decision TO %I',owner_role);
  EXECUTE format('GRANT SELECT,UPDATE ON normative.knowledge_layer_rule TO %I',owner_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer,normative.standard_edition,normative.curation_audit,normative.knowledge_layer_rule_release_foundation,qms.learning_target_application_receipt TO %I',owner_role);
  EXECUTE format('GRANT INSERT ON normative.knowledge_layer_rule_governance_claim,normative.knowledge_layer_rule_publication,normative.knowledge_layer_rule_activation,normative.knowledge_layer_rule_runtime_adoption,normative.knowledge_layer_rule_governance_event,normative.knowledge_layer_rule_governance_disposition,normative.knowledge_layer_rule_capability_decision,normative.curation_audit,eventing.knowledge_layer_rule_governance_outbox,audit.knowledge_layer_rule_governance_audit TO %I',owner_role);
  EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0020_canonical_json_value(jsonb) TO %I',owner_role);
END $migration$;

CREATE FUNCTION normative.foundation_0022_uuid(p_id uuid,p_suffix text)
RETURNS uuid LANGUAGE sql IMMUTABLE SET search_path=pg_catalog AS $fn$
 SELECT (substr(md5(p_id::text||':'||p_suffix),1,8)||'-'||substr(md5(p_id::text||':'||p_suffix),9,4)||'-4'||substr(md5(p_id::text||':'||p_suffix),14,3)||'-8'||substr(md5(p_id::text||':'||p_suffix),18,3)||'-'||substr(md5(p_id::text||':'||p_suffix),21,12))::uuid
$fn$;

CREATE FUNCTION normative.foundation_0022_rule_material_hash(p_rule_id uuid)
RETURNS text LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
 SELECT encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(jsonb_build_object(
   'id',r.id::text,'knowledge_layer_id',r.knowledge_layer_id::text,'lineage_id',r.lineage_id::text,
   'rule_key',r.rule_key,'version',r.version,'previous_revision_id',r.previous_revision_id::text,
   'logic_json',r.logic_json,'evidence_expectation',r.evidence_expectation,
   'source_reference',r.source_reference,'certifiability_classification',r.certifiability_classification
 )),'UTF8')),'hex') FROM normative.knowledge_layer_rule r WHERE r.id=p_rule_id
$fn$;

CREATE FUNCTION normative.foundation_0022_rule_semantic_hash(p_rule_id uuid)
RETURNS text LANGUAGE sql STABLE SET search_path=pg_catalog AS $fn$
 SELECT encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(jsonb_build_object(
   'knowledge_layer_id',r.knowledge_layer_id::text,'rule_key',r.rule_key,
   'logic_json',r.logic_json,'evidence_expectation',r.evidence_expectation,
   'certifiability_classification',r.certifiability_classification
 )),'UTF8')),'hex') FROM normative.knowledge_layer_rule r WHERE r.id=p_rule_id
$fn$;

CREATE FUNCTION normative.foundation_0022_fail(p_point text)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
BEGIN
 IF current_setting('foundation.phase272_failure_point',true)=p_point THEN
   RAISE EXCEPTION 'deliberate Phase 27.2 failure at %',p_point;
 END IF;
END $fn$;

CREATE FUNCTION normative.foundation_0022_authorized(p_permission text)
RETURNS void LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
BEGIN
 IF current_setting('app.release_permission',true) IS DISTINCT FROM p_permission OR
    current_setting('app.mfa_verified',true)<>'true' OR current_setting('app.access_active',true)<>'true' OR
    current_setting('app.governance_scope',true)<>'global' OR
    NULLIF(current_setting('app.actor_id',true),'') IS NULL OR
    NULLIF(current_setting('app.trace_id',true),'') IS NULL OR
    NULLIF(current_setting('app.authority_context_version',true),'') IS NULL OR
    NULLIF(current_setting('app.authority_decision_reference',true),'') IS NULL OR
    NULLIF(current_setting('app.governance_policy_version',true),'') IS NULL THEN
   RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='fresh exact global release authority required';
 END IF;
END $fn$;

CREATE FUNCTION normative.foundation_0022_capability_enabled(p_capability text)
RETURNS boolean LANGUAGE sql STABLE SET search_path=pg_catalog AS $fn$
 SELECT COALESCE((SELECT d.enabled FROM normative.knowledge_layer_rule_capability_decision d
   WHERE d.capability=p_capability AND NOT EXISTS(
     SELECT 1 FROM normative.knowledge_layer_rule_capability_decision n
      WHERE n.predecessor_decision_id=d.id)),true)
$fn$;

CREATE FUNCTION normative.foundation_0022_insert_graph(
 p_operation text,p_artifact uuid,p_rule uuid,p_event_type text,p_material text,p_idempotency text,
 p_actor uuid,p_trace uuid,p_payload jsonb)
RETURNS TABLE(event_id uuid,outbox_id uuid,audit_id uuid) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE e uuid:=normative.foundation_0022_uuid(p_artifact,'event'); o uuid:=normative.foundation_0022_uuid(p_artifact,'outbox'); a uuid:=normative.foundation_0022_uuid(p_artifact,'audit');
BEGIN
 INSERT INTO normative.knowledge_layer_rule_governance_claim(id,operation_kind,artifact_id,target_rule_id,
   idempotency_key_hash,operation_material_hash,event_id,outbox_id,audit_id,trace_id,actor_external_id,
   authority_context_version,authority_decision_reference,governance_policy_version)
 VALUES(p_artifact,p_operation,p_artifact,p_rule,p_idempotency,p_material,e,o,a,p_trace,p_actor,
   current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),
   current_setting('app.governance_policy_version',true));
 PERFORM normative.foundation_0022_fail('after_claim');
 INSERT INTO normative.knowledge_layer_rule_governance_event(id,event_type,schema_version,operation_kind,
   artifact_id,target_rule_id,payload,payload_hash,trace_id)
 VALUES(e,p_event_type,1,p_operation,p_artifact,p_rule,p_payload,
   encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(p_payload),'UTF8')),'hex'),p_trace);
 PERFORM normative.foundation_0022_fail('after_event');
 INSERT INTO eventing.knowledge_layer_rule_governance_outbox(id,event_id,destination,status,available_at)
 VALUES(o,e,'platform.knowledge-layer-rule-governance','pending',statement_timestamp());
 PERFORM normative.foundation_0022_fail('after_outbox');
 INSERT INTO audit.knowledge_layer_rule_governance_audit(id,operation_kind,artifact_id,target_rule_id,
   actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,
   operation_material_hash,trace_id,payload_hash)
 VALUES(a,p_operation,p_artifact,p_rule,p_actor,current_setting('app.authority_context_version',true),
   current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),
   p_material,p_trace,encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(p_payload),'UTF8')),'hex'));
 PERFORM normative.foundation_0022_fail('after_audit');
 RETURN QUERY SELECT e,o,a;
END $fn$;

CREATE FUNCTION normative.publish_knowledge_layer_rule_v1(
 p_publication_id uuid,p_rule_id uuid,p_expected_hash text,p_idempotency_hash text,
 p_reason text,p_actor uuid,p_trace uuid)
RETURNS TABLE(artifact_id uuid,replayed boolean) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE r record; prior record; material text; semantic text; op_hash text; ids record; curation uuid:=normative.foundation_0022_uuid(p_publication_id,'curation'); payload jsonb;
BEGIN
 PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.publish');
 IF NOT normative.foundation_0022_capability_enabled('PUBLICATION') THEN RAISE EXCEPTION 'publication capability disabled'; END IF;
 SELECT * INTO prior FROM normative.knowledge_layer_rule_publication WHERE id=p_publication_id OR idempotency_key_hash=p_idempotency_hash;
 op_hash:=encode(sha256(convert_to(p_rule_id::text||':'||p_expected_hash||':'||p_reason,'UTF8')),'hex');
 IF prior.id IS NOT NULL THEN
   IF prior.id=p_publication_id AND prior.knowledge_layer_rule_id=p_rule_id AND prior.operation_material_hash=op_hash THEN RETURN QUERY SELECT prior.id,true; RETURN;
   END IF; RAISE EXCEPTION 'publication identity conflict';
 END IF;
 IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim gc WHERE gc.artifact_id=p_publication_id OR (gc.operation_kind='PUBLICATION' AND gc.idempotency_key_hash=p_idempotency_hash)) THEN RAISE EXCEPTION 'publication identity conflict: existing claim cannot be stolen'; END IF;
 SELECT * INTO r FROM normative.knowledge_layer_rule WHERE id=p_rule_id FOR UPDATE;
 material:=normative.foundation_0022_rule_material_hash(p_rule_id); semantic:=normative.foundation_0022_rule_semantic_hash(p_rule_id);
 IF r.id IS NULL OR r.status<>'draft' OR r.published_at IS NOT NULL OR material IS DISTINCT FROM p_expected_hash OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_publication WHERE knowledge_layer_rule_id=p_rule_id) THEN
   RAISE EXCEPTION 'exact draft rule/hash publication precondition failed';
 END IF;
 INSERT INTO normative.curation_audit(id,action,entity_type,entity_id,actor_id,trace_id,payload_hash,occurred_at)
 VALUES(curation,'knowledge_layer_rule.published','knowledge_layer_rule',p_rule_id,p_actor::text,p_trace,material,statement_timestamp());
 UPDATE normative.knowledge_layer_rule SET status='published',published_at=statement_timestamp() WHERE id=p_rule_id;
 payload:=jsonb_build_object('publication_id',p_publication_id::text,'rule_id',p_rule_id::text,'lineage_id',r.lineage_id::text,'rule_material_hash',material,'semantic_fingerprint',semantic,'evidence_kind','NATIVE','next_stage_requested',false,'runtime_effect_changed',false);
 SELECT * INTO ids FROM normative.foundation_0022_insert_graph('PUBLICATION',p_publication_id,p_rule_id,'knowledge_layer_rule.published',op_hash,p_idempotency_hash,p_actor,p_trace,payload);
 INSERT INTO normative.knowledge_layer_rule_publication(id,evidence_kind,workflow_approved,knowledge_layer_rule_id,
  knowledge_layer_id,lineage_id,rule_version,rule_material_hash,semantic_fingerprint,curation_audit_id,
  historical_published_at,evidence_imported_at,evidence_reference,actor_external_id,authority_context_version,
  authority_decision_reference,governance_policy_version,authorized_at,reason,idempotency_key_hash,
  operation_material_hash,claim_id,event_id,outbox_id,audit_id,trace_id)
 VALUES(p_publication_id,'NATIVE',true,p_rule_id,r.knowledge_layer_id,r.lineage_id,r.version,material,semantic,curation,
  statement_timestamp(),NULL,NULL,p_actor,current_setting('app.authority_context_version',true),
  current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),
  statement_timestamp(),p_reason,p_idempotency_hash,op_hash,p_publication_id,ids.event_id,ids.outbox_id,ids.audit_id,p_trace);
 PERFORM normative.foundation_0022_fail('after_artifact');
 IF normative.foundation_0022_rule_material_hash(p_rule_id) IS DISTINCT FROM material OR NOT normative.foundation_0022_capability_enabled('PUBLICATION') THEN RAISE EXCEPTION 'publication precommit drift'; END IF;
 PERFORM normative.foundation_0022_fail('before_commit');
 RETURN QUERY SELECT p_publication_id,false;
END $fn$;

CREATE FUNCTION normative.import_knowledge_layer_rule_publication_evidence_v1(
 p_publication_id uuid,p_rule_id uuid,p_expected_hash text,p_curation_audit_id uuid,
 p_historical_published_at timestamptz,p_evidence_reference text,p_idempotency_hash text,
 p_reason text,p_actor uuid,p_trace uuid)
RETURNS TABLE(artifact_id uuid,replayed boolean) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE r record; c record; prior record; material text; semantic text; op_hash text; ids record; payload jsonb;
BEGIN
 PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.publish');
 IF NOT normative.foundation_0022_capability_enabled('PUBLICATION') THEN RAISE EXCEPTION 'publication capability disabled'; END IF;
 SELECT * INTO prior FROM normative.knowledge_layer_rule_publication WHERE id=p_publication_id OR idempotency_key_hash=p_idempotency_hash;
 op_hash:=encode(sha256(convert_to(p_rule_id::text||':'||p_expected_hash||':'||p_curation_audit_id::text||':'||coalesce(p_evidence_reference,''),'UTF8')),'hex');
 IF prior.id IS NOT NULL THEN IF prior.id=p_publication_id AND prior.operation_material_hash=op_hash THEN RETURN QUERY SELECT prior.id,true; RETURN; END IF; RAISE EXCEPTION 'publication identity conflict'; END IF;
 IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim gc WHERE gc.artifact_id=p_publication_id OR (gc.operation_kind='PUBLICATION' AND gc.idempotency_key_hash=p_idempotency_hash)) THEN RAISE EXCEPTION 'publication identity conflict: existing claim cannot be stolen'; END IF;
 SELECT * INTO r FROM normative.knowledge_layer_rule WHERE id=p_rule_id FOR SHARE;
 SELECT * INTO c FROM normative.curation_audit WHERE id=p_curation_audit_id;
 material:=normative.foundation_0022_rule_material_hash(p_rule_id); semantic:=normative.foundation_0022_rule_semantic_hash(p_rule_id);
 IF r.id IS NULL OR r.status<>'published' OR r.published_at IS NULL OR r.created_at >= (SELECT installed_at FROM normative.knowledge_layer_rule_release_foundation) OR
    material IS DISTINCT FROM p_expected_hash OR c.id IS NULL OR c.entity_id<>p_rule_id OR c.action<>'knowledge_layer_rule.published' OR
    p_evidence_reference IS NULL OR btrim(p_evidence_reference)='' OR
    (p_historical_published_at IS NOT NULL AND p_historical_published_at IS DISTINCT FROM r.published_at) THEN
   RAISE EXCEPTION 'truthful legacy publication evidence precondition failed';
 END IF;
 payload:=jsonb_build_object('publication_id',p_publication_id::text,'rule_id',p_rule_id::text,'lineage_id',r.lineage_id::text,'rule_material_hash',material,'evidence_kind','LEGACY_EVIDENCE_IMPORT','workflow_approved',false,'next_stage_requested',false);
 SELECT * INTO ids FROM normative.foundation_0022_insert_graph('PUBLICATION',p_publication_id,p_rule_id,'knowledge_layer_rule.publication_evidence_imported',op_hash,p_idempotency_hash,p_actor,p_trace,payload);
 INSERT INTO normative.knowledge_layer_rule_publication(id,evidence_kind,workflow_approved,knowledge_layer_rule_id,knowledge_layer_id,lineage_id,rule_version,rule_material_hash,semantic_fingerprint,curation_audit_id,historical_published_at,evidence_imported_at,evidence_reference,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,authorized_at,reason,idempotency_key_hash,operation_material_hash,claim_id,event_id,outbox_id,audit_id,trace_id)
 VALUES(p_publication_id,'LEGACY_EVIDENCE_IMPORT',false,p_rule_id,r.knowledge_layer_id,r.lineage_id,r.version,material,semantic,p_curation_audit_id,p_historical_published_at,statement_timestamp(),p_evidence_reference,p_actor,current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),statement_timestamp(),p_reason,p_idempotency_hash,op_hash,p_publication_id,ids.event_id,ids.outbox_id,ids.audit_id,p_trace);
 PERFORM normative.foundation_0022_fail('after_artifact'); PERFORM normative.foundation_0022_fail('before_commit');
 RETURN QUERY SELECT p_publication_id,false;
END $fn$;

CREATE FUNCTION normative.activate_knowledge_layer_rule_v1(
 p_activation_id uuid,p_publication_id uuid,p_expected_hash text,p_expected_predecessor uuid,
 p_compatibility_hash text,p_idempotency_hash text,p_reason text,p_actor uuid,p_trace uuid)
RETURNS TABLE(artifact_id uuid,replayed boolean) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE p record; pred record; prior record; material text; op_hash text; ids record; payload jsonb;
BEGIN
 PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.activate');
 IF NOT normative.foundation_0022_capability_enabled('ACTIVATION') THEN RAISE EXCEPTION 'activation capability disabled'; END IF;
 SELECT * INTO prior FROM normative.knowledge_layer_rule_activation WHERE id=p_activation_id OR idempotency_key_hash=p_idempotency_hash;
 op_hash:=encode(sha256(convert_to(p_publication_id::text||':'||p_expected_hash||':'||coalesce(p_expected_predecessor::text,'ROOT')||':'||p_compatibility_hash||':'||p_reason,'UTF8')),'hex');
 IF prior.id IS NOT NULL THEN IF prior.id=p_activation_id AND prior.operation_material_hash=op_hash THEN RETURN QUERY SELECT prior.id,true; RETURN; END IF; RAISE EXCEPTION 'activation identity conflict'; END IF;
 IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim gc WHERE gc.artifact_id=p_activation_id OR (gc.operation_kind='ACTIVATION' AND gc.idempotency_key_hash=p_idempotency_hash)) THEN RAISE EXCEPTION 'activation identity conflict: existing claim cannot be stolen'; END IF;
 SELECT * INTO p FROM normative.knowledge_layer_rule_publication WHERE id=p_publication_id FOR SHARE;
 material:=normative.foundation_0022_rule_material_hash(p.knowledge_layer_rule_id);
 IF p.id IS NULL OR material IS DISTINCT FROM p.rule_material_hash OR material IS DISTINCT FROM p_expected_hash OR p.actor_external_id=p_actor THEN RAISE EXCEPTION 'exact publication/hash or separation-of-duty activation precondition failed'; END IF;
 IF p_expected_predecessor IS NULL THEN
   IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_activation WHERE lineage_id=p.lineage_id) THEN RAISE EXCEPTION 'activation predecessor is stale'; END IF;
 ELSE
   SELECT * INTO pred FROM normative.knowledge_layer_rule_activation WHERE id=p_expected_predecessor FOR SHARE;
   IF pred.id IS NULL OR pred.lineage_id<>p.lineage_id OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_activation WHERE predecessor_activation_id=pred.id) THEN RAISE EXCEPTION 'activation predecessor is not the exact leaf'; END IF;
 END IF;
 payload:=jsonb_build_object('activation_id',p_activation_id::text,'publication_id',p.id::text,'rule_id',p.knowledge_layer_rule_id::text,'lineage_id',p.lineage_id::text,'rule_material_hash',material,'predecessor_activation_id',p_expected_predecessor::text,'next_stage_requested',false,'runtime_effect_changed',false);
 SELECT * INTO ids FROM normative.foundation_0022_insert_graph('ACTIVATION',p_activation_id,p.knowledge_layer_rule_id,'knowledge_layer_rule.activation_recorded',op_hash,p_idempotency_hash,p_actor,p_trace,payload);
 INSERT INTO normative.knowledge_layer_rule_activation(id,publication_id,knowledge_layer_rule_id,knowledge_layer_id,lineage_id,rule_version,rule_material_hash,semantic_fingerprint,predecessor_activation_id,compatibility_hash,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,authorized_at,reason,idempotency_key_hash,operation_material_hash,claim_id,event_id,outbox_id,audit_id,trace_id)
 VALUES(p_activation_id,p.id,p.knowledge_layer_rule_id,p.knowledge_layer_id,p.lineage_id,p.rule_version,material,p.semantic_fingerprint,p_expected_predecessor,p_compatibility_hash,p_actor,current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),statement_timestamp(),p_reason,p_idempotency_hash,op_hash,p_activation_id,ids.event_id,ids.outbox_id,ids.audit_id,p_trace);
 PERFORM normative.foundation_0022_fail('after_artifact');
 IF normative.foundation_0022_rule_material_hash(p.knowledge_layer_rule_id) IS DISTINCT FROM material OR NOT normative.foundation_0022_capability_enabled('ACTIVATION') THEN RAISE EXCEPTION 'activation precommit drift'; END IF;
 PERFORM normative.foundation_0022_fail('before_commit'); RETURN QUERY SELECT p_activation_id,false;
END $fn$;

CREATE FUNCTION normative.adopt_knowledge_layer_rule_runtime_v1(
 p_adoption_id uuid,p_activation_id uuid,p_expected_hash text,p_expected_predecessor uuid,
 p_config_ref text,p_config_hash text,p_idempotency_hash text,p_reason text,p_actor uuid,p_trace uuid)
RETURNS TABLE(artifact_id uuid,replayed boolean) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE a record; p record; pred record; prior record; material text; op_hash text; ids record; payload jsonb;
BEGIN
 PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.runtime_adopt');
 IF NOT normative.foundation_0022_capability_enabled('RUNTIME_ADOPTION') THEN RAISE EXCEPTION 'runtime adoption capability disabled'; END IF;
 SELECT * INTO prior FROM normative.knowledge_layer_rule_runtime_adoption WHERE id=p_adoption_id OR idempotency_key_hash=p_idempotency_hash;
 op_hash:=encode(sha256(convert_to(p_activation_id::text||':'||p_expected_hash||':'||coalesce(p_expected_predecessor::text,'ROOT')||':'||p_config_ref||':'||p_config_hash||':'||p_reason,'UTF8')),'hex');
 IF prior.id IS NOT NULL THEN IF prior.id=p_adoption_id AND prior.operation_material_hash=op_hash THEN RETURN QUERY SELECT prior.id,true; RETURN; END IF; RAISE EXCEPTION 'runtime adoption identity conflict'; END IF;
 IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim gc WHERE gc.artifact_id=p_adoption_id OR (gc.operation_kind='RUNTIME_ADOPTION' AND gc.idempotency_key_hash=p_idempotency_hash)) THEN RAISE EXCEPTION 'runtime adoption identity conflict: existing claim cannot be stolen'; END IF;
 SELECT * INTO a FROM normative.knowledge_layer_rule_activation WHERE id=p_activation_id FOR SHARE;
 SELECT * INTO p FROM normative.knowledge_layer_rule_publication WHERE id=a.publication_id FOR SHARE;
 material:=normative.foundation_0022_rule_material_hash(a.knowledge_layer_rule_id);
 IF a.id IS NULL OR p.id IS NULL OR a.publication_id<>p.id OR a.knowledge_layer_rule_id<>p.knowledge_layer_rule_id OR
    a.rule_material_hash<>p.rule_material_hash OR material IS DISTINCT FROM a.rule_material_hash OR
    material IS DISTINCT FROM p_expected_hash OR a.actor_external_id=p_actor OR p.actor_external_id=p_actor THEN
   RAISE EXCEPTION 'exact activation/publication/hash or separation-of-duty adoption precondition failed';
 END IF;
 IF p_expected_predecessor IS NULL THEN
   IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption WHERE lineage_id=a.lineage_id) THEN RAISE EXCEPTION 'adoption predecessor is stale'; END IF;
 ELSE
   SELECT * INTO pred FROM normative.knowledge_layer_rule_runtime_adoption WHERE id=p_expected_predecessor FOR SHARE;
   IF pred.id IS NULL OR pred.lineage_id<>a.lineage_id OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption WHERE predecessor_adoption_id=pred.id) THEN RAISE EXCEPTION 'adoption predecessor is not the exact leaf'; END IF;
 END IF;
 payload:=jsonb_build_object('runtime_adoption_id',p_adoption_id::text,'activation_id',a.id::text,'publication_id',p.id::text,'rule_id',a.knowledge_layer_rule_id::text,'lineage_id',a.lineage_id::text,'rule_material_hash',material,'predecessor_adoption_id',p_expected_predecessor::text,'release_configuration_hash',p_config_hash,'deployment_requested',false,'automatic_learning',false);
 SELECT * INTO ids FROM normative.foundation_0022_insert_graph('RUNTIME_ADOPTION',p_adoption_id,a.knowledge_layer_rule_id,'knowledge_layer_rule.runtime_adopted',op_hash,p_idempotency_hash,p_actor,p_trace,payload);
 INSERT INTO normative.knowledge_layer_rule_runtime_adoption(id,adoption_kind,activation_id,publication_id,knowledge_layer_rule_id,knowledge_layer_id,lineage_id,rule_version,rule_material_hash,semantic_fingerprint,predecessor_adoption_id,release_configuration_reference,release_configuration_hash,historical_activation_claim,asserted_historical_effective_at,bootstrap_imported_at,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,authorized_at,reason,idempotency_key_hash,operation_material_hash,claim_id,event_id,outbox_id,audit_id,trace_id)
 VALUES(p_adoption_id,'NATIVE',a.id,p.id,a.knowledge_layer_rule_id,a.knowledge_layer_id,a.lineage_id,a.rule_version,material,a.semantic_fingerprint,p_expected_predecessor,p_config_ref,p_config_hash,false,NULL,NULL,p_actor,current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),statement_timestamp(),p_reason,p_idempotency_hash,op_hash,p_adoption_id,ids.event_id,ids.outbox_id,ids.audit_id,p_trace);
 PERFORM normative.foundation_0022_fail('after_artifact');
 IF normative.foundation_0022_rule_material_hash(a.knowledge_layer_rule_id) IS DISTINCT FROM material OR NOT normative.foundation_0022_capability_enabled('RUNTIME_ADOPTION') THEN RAISE EXCEPTION 'adoption precommit drift'; END IF;
 PERFORM normative.foundation_0022_fail('before_commit'); RETURN QUERY SELECT p_adoption_id,false;
END $fn$;

CREATE FUNCTION normative.bootstrap_legacy_knowledge_layer_rule_runtime_v1(
 p_adoption_id uuid,p_rule_id uuid,p_expected_hash text,p_config_ref text,p_config_hash text,
 p_idempotency_hash text,p_reason text,p_actor uuid,p_trace uuid)
RETURNS TABLE(artifact_id uuid,replayed boolean) LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE r record; prior record; material text; semantic text; op_hash text; ids record; payload jsonb;
BEGIN
 PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.runtime_adopt');
 IF NOT normative.foundation_0022_capability_enabled('RUNTIME_ADOPTION') THEN RAISE EXCEPTION 'runtime adoption capability disabled'; END IF;
 SELECT * INTO prior FROM normative.knowledge_layer_rule_runtime_adoption WHERE id=p_adoption_id OR idempotency_key_hash=p_idempotency_hash;
 op_hash:=encode(sha256(convert_to(p_rule_id::text||':'||p_expected_hash||':'||p_config_ref||':'||p_config_hash||':'||p_reason,'UTF8')),'hex');
 IF prior.id IS NOT NULL THEN IF prior.id=p_adoption_id AND prior.operation_material_hash=op_hash THEN RETURN QUERY SELECT prior.id,true; RETURN; END IF; RAISE EXCEPTION 'runtime adoption identity conflict'; END IF;
 IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim gc WHERE gc.artifact_id=p_adoption_id OR (gc.operation_kind='RUNTIME_ADOPTION' AND gc.idempotency_key_hash=p_idempotency_hash)) THEN RAISE EXCEPTION 'runtime adoption identity conflict: existing claim cannot be stolen'; END IF;
 SELECT * INTO r FROM normative.knowledge_layer_rule WHERE id=p_rule_id FOR SHARE;
 material:=normative.foundation_0022_rule_material_hash(p_rule_id); semantic:=normative.foundation_0022_rule_semantic_hash(p_rule_id);
 IF r.id IS NULL OR r.status<>'published' OR r.created_at >= (SELECT installed_at FROM normative.knowledge_layer_rule_release_foundation) OR
    material IS DISTINCT FROM p_expected_hash OR EXISTS(SELECT 1 FROM qms.learning_target_application_receipt WHERE after_rule_id=p_rule_id) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption WHERE lineage_id=r.lineage_id) THEN
   RAISE EXCEPTION 'truthful legacy bootstrap precondition failed';
 END IF;
 payload:=jsonb_build_object('runtime_adoption_id',p_adoption_id::text,'rule_id',p_rule_id::text,'lineage_id',r.lineage_id::text,'rule_material_hash',material,'adoption_kind','LEGACY_BOOTSTRAP','historical_activation_claim',false,'historical_runtime_time_claim',false,'deployment_requested',false);
 SELECT * INTO ids FROM normative.foundation_0022_insert_graph('RUNTIME_ADOPTION',p_adoption_id,p_rule_id,'knowledge_layer_rule.legacy_runtime_bootstrapped',op_hash,p_idempotency_hash,p_actor,p_trace,payload);
 INSERT INTO normative.knowledge_layer_rule_runtime_adoption(id,adoption_kind,activation_id,publication_id,knowledge_layer_rule_id,knowledge_layer_id,lineage_id,rule_version,rule_material_hash,semantic_fingerprint,predecessor_adoption_id,release_configuration_reference,release_configuration_hash,historical_activation_claim,asserted_historical_effective_at,bootstrap_imported_at,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,authorized_at,reason,idempotency_key_hash,operation_material_hash,claim_id,event_id,outbox_id,audit_id,trace_id)
 VALUES(p_adoption_id,'LEGACY_BOOTSTRAP',NULL,NULL,p_rule_id,r.knowledge_layer_id,r.lineage_id,r.version,material,semantic,NULL,p_config_ref,p_config_hash,false,NULL,statement_timestamp(),p_actor,current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),statement_timestamp(),p_reason,p_idempotency_hash,op_hash,p_adoption_id,ids.event_id,ids.outbox_id,ids.audit_id,p_trace);
 PERFORM normative.foundation_0022_fail('after_artifact'); PERFORM normative.foundation_0022_fail('before_commit'); RETURN QUERY SELECT p_adoption_id,false;
END $fn$;

CREATE FUNCTION normative.resolve_knowledge_layer_rule_runtime_adoption_v1(p_runtime_adoption_id uuid)
RETURNS TABLE(runtime_adoption_id uuid,activation_id uuid,publication_id uuid,knowledge_layer_rule_id uuid,lineage_id uuid,rule_version text,rule_material_hash text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
 SELECT a.id,a.activation_id,a.publication_id,a.knowledge_layer_rule_id,a.lineage_id,a.rule_version,a.rule_material_hash
 FROM normative.knowledge_layer_rule_runtime_adoption a
 JOIN normative.knowledge_layer_rule_activation x ON x.id=a.activation_id AND x.publication_id=a.publication_id AND x.knowledge_layer_rule_id=a.knowledge_layer_rule_id AND x.rule_material_hash=a.rule_material_hash
 JOIN normative.knowledge_layer_rule_publication p ON p.id=a.publication_id AND p.knowledge_layer_rule_id=a.knowledge_layer_rule_id AND p.rule_material_hash=a.rule_material_hash
 JOIN normative.knowledge_layer_rule r ON r.id=a.knowledge_layer_rule_id AND r.lineage_id=a.lineage_id AND r.version=a.rule_version
 WHERE a.id=p_runtime_adoption_id AND a.adoption_kind='NATIVE' AND r.status='published'
   AND normative.foundation_0022_rule_material_hash(r.id)=a.rule_material_hash
$fn$;

CREATE FUNCTION normative.record_rule_governance_capability_decision_v1(p_id uuid,p_capability text,p_enabled boolean,p_predecessor uuid,p_reason text,p_actor uuid,p_trace uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE pred record;
BEGIN
 PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.release_capability_admin');
 IF p_predecessor IS NULL THEN
   IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_capability_decision WHERE capability=p_capability) THEN RAISE EXCEPTION 'capability predecessor required'; END IF;
 ELSE
   SELECT * INTO pred FROM normative.knowledge_layer_rule_capability_decision WHERE id=p_predecessor FOR SHARE;
   IF pred.id IS NULL OR pred.capability<>p_capability OR pred.enabled=p_enabled OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_capability_decision WHERE predecessor_decision_id=pred.id) THEN RAISE EXCEPTION 'exact alternating capability predecessor required'; END IF;
 END IF;
 INSERT INTO normative.knowledge_layer_rule_capability_decision(id,capability,enabled,predecessor_decision_id,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,reason,trace_id)
 VALUES(p_id,p_capability,p_enabled,p_predecessor,p_actor,current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),p_reason,p_trace);
 RETURN p_id;
END $fn$;

CREATE FUNCTION normative.record_abandoned_rule_governance_operation_v1(p_kind text,p_artifact uuid,p_material text,p_reason text,p_actor uuid,p_trace uuid)
RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
DECLARE d uuid:=normative.foundation_0022_uuid(p_artifact,'disposition');
BEGIN
 PERFORM normative.foundation_0022_authorized('qms.knowledge_layer_rule.release_repair');
 IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim WHERE artifact_id=p_artifact) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_publication WHERE id=p_artifact) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_activation WHERE id=p_artifact) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption WHERE id=p_artifact) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_event WHERE artifact_id=p_artifact) THEN
   RAISE EXCEPTION 'durable operation evidence forbids abandonment';
 END IF;
 INSERT INTO normative.knowledge_layer_rule_governance_claim(id,operation_kind,artifact_id,target_rule_id,idempotency_key_hash,operation_material_hash,event_id,outbox_id,audit_id,trace_id,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version)
 VALUES(p_artifact,p_kind,p_artifact,NULL,p_material,p_material,NULL,NULL,NULL,p_trace,p_actor,current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true));
 INSERT INTO normative.knowledge_layer_rule_governance_disposition(id,claim_id,disposition,actor_external_id,authority_context_version,authority_decision_reference,governance_policy_version,reason,trace_id)
 VALUES(d,p_artifact,'ABANDONED',p_actor,current_setting('app.authority_context_version',true),current_setting('app.authority_decision_reference',true),current_setting('app.governance_policy_version',true),p_reason,p_trace);
 RETURN d;
END $fn$;

CREATE FUNCTION normative.reconcile_knowledge_layer_rule_publication_v1(p_id uuid)
RETURNS TABLE(outcome text,detail text) LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
 WITH g AS (SELECT c.id cid,p.id aid,e.id eid,o.id oid,a.id uid,d.id did,
   c.operation_material_hash cm,p.operation_material_hash am,c.event_id ce,p.event_id ae,c.outbox_id co,p.outbox_id ao,c.audit_id ca,p.audit_id aa,c.trace_id ct,p.trace_id at
  FROM (SELECT 1) z LEFT JOIN normative.knowledge_layer_rule_governance_claim c ON c.artifact_id=p_id AND c.operation_kind='PUBLICATION'
  LEFT JOIN normative.knowledge_layer_rule_publication p ON p.id=p_id
  LEFT JOIN normative.knowledge_layer_rule_governance_event e ON e.artifact_id=p_id
  LEFT JOIN eventing.knowledge_layer_rule_governance_outbox o ON o.id=c.outbox_id AND o.event_id=e.id
  LEFT JOIN audit.knowledge_layer_rule_governance_audit a ON a.artifact_id=p_id
  LEFT JOIN normative.knowledge_layer_rule_governance_disposition d ON d.claim_id=c.id)
 SELECT CASE WHEN cid IS NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL AND did IS NULL THEN 'NOT_COMMITTED'
  WHEN cid IS NOT NULL AND did IS NOT NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL THEN 'ABANDONED'
  WHEN cid IS NOT NULL AND aid IS NOT NULL AND eid IS NOT NULL AND oid IS NOT NULL AND uid IS NOT NULL AND did IS NULL AND cm=am AND ce=ae AND co=ao AND ca=aa AND ct=at THEN 'COMMITTED'
  ELSE 'INCONSISTENT' END,
  CASE WHEN cid IS NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL AND did IS NULL THEN 'no durable governed operation evidence'
  WHEN cid IS NOT NULL AND did IS NOT NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL THEN 'explicit append-only abandonment disposition'
  WHEN cid IS NOT NULL AND aid IS NOT NULL AND eid IS NOT NULL AND oid IS NOT NULL AND uid IS NOT NULL AND did IS NULL AND cm=am AND ce=ae AND co=ao AND ca=aa AND ct=at THEN 'complete exact publication graph'
  ELSE 'partial or mismatched durable publication evidence' END FROM g
$fn$;

CREATE FUNCTION normative.reconcile_knowledge_layer_rule_activation_v1(p_id uuid)
RETURNS TABLE(outcome text,detail text) LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
 WITH g AS (SELECT c.id cid,p.id aid,e.id eid,o.id oid,a.id uid,d.id did,c.operation_material_hash cm,p.operation_material_hash am,c.event_id ce,p.event_id ae,c.outbox_id co,p.outbox_id ao,c.audit_id ca,p.audit_id aa,c.trace_id ct,p.trace_id at
 FROM (SELECT 1) z LEFT JOIN normative.knowledge_layer_rule_governance_claim c ON c.artifact_id=p_id AND c.operation_kind='ACTIVATION' LEFT JOIN normative.knowledge_layer_rule_activation p ON p.id=p_id LEFT JOIN normative.knowledge_layer_rule_governance_event e ON e.artifact_id=p_id LEFT JOIN eventing.knowledge_layer_rule_governance_outbox o ON o.id=c.outbox_id AND o.event_id=e.id LEFT JOIN audit.knowledge_layer_rule_governance_audit a ON a.artifact_id=p_id LEFT JOIN normative.knowledge_layer_rule_governance_disposition d ON d.claim_id=c.id)
 SELECT CASE WHEN cid IS NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL AND did IS NULL THEN 'NOT_COMMITTED' WHEN cid IS NOT NULL AND did IS NOT NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL THEN 'ABANDONED' WHEN cid IS NOT NULL AND aid IS NOT NULL AND eid IS NOT NULL AND oid IS NOT NULL AND uid IS NOT NULL AND did IS NULL AND cm=am AND ce=ae AND co=ao AND ca=aa AND ct=at THEN 'COMMITTED' ELSE 'INCONSISTENT' END,
 CASE WHEN cid IS NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL AND did IS NULL THEN 'no durable governed operation evidence' WHEN cid IS NOT NULL AND did IS NOT NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL THEN 'explicit append-only abandonment disposition' WHEN cid IS NOT NULL AND aid IS NOT NULL AND eid IS NOT NULL AND oid IS NOT NULL AND uid IS NOT NULL AND did IS NULL AND cm=am AND ce=ae AND co=ao AND ca=aa AND ct=at THEN 'complete exact activation graph' ELSE 'partial or mismatched durable activation evidence' END FROM g
$fn$;

CREATE FUNCTION normative.reconcile_knowledge_layer_rule_runtime_adoption_v1(p_id uuid)
RETURNS TABLE(outcome text,detail text) LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
 WITH g AS (SELECT c.id cid,p.id aid,e.id eid,o.id oid,a.id uid,d.id did,c.operation_material_hash cm,p.operation_material_hash am,c.event_id ce,p.event_id ae,c.outbox_id co,p.outbox_id ao,c.audit_id ca,p.audit_id aa,c.trace_id ct,p.trace_id at
 FROM (SELECT 1) z LEFT JOIN normative.knowledge_layer_rule_governance_claim c ON c.artifact_id=p_id AND c.operation_kind='RUNTIME_ADOPTION' LEFT JOIN normative.knowledge_layer_rule_runtime_adoption p ON p.id=p_id LEFT JOIN normative.knowledge_layer_rule_governance_event e ON e.artifact_id=p_id LEFT JOIN eventing.knowledge_layer_rule_governance_outbox o ON o.id=c.outbox_id AND o.event_id=e.id LEFT JOIN audit.knowledge_layer_rule_governance_audit a ON a.artifact_id=p_id LEFT JOIN normative.knowledge_layer_rule_governance_disposition d ON d.claim_id=c.id)
 SELECT CASE WHEN cid IS NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL AND did IS NULL THEN 'NOT_COMMITTED' WHEN cid IS NOT NULL AND did IS NOT NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL THEN 'ABANDONED' WHEN cid IS NOT NULL AND aid IS NOT NULL AND eid IS NOT NULL AND oid IS NOT NULL AND uid IS NOT NULL AND did IS NULL AND cm=am AND ce=ae AND co=ao AND ca=aa AND ct=at THEN 'COMMITTED' ELSE 'INCONSISTENT' END,
 CASE WHEN cid IS NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL AND did IS NULL THEN 'no durable governed operation evidence' WHEN cid IS NOT NULL AND did IS NOT NULL AND aid IS NULL AND eid IS NULL AND oid IS NULL AND uid IS NULL THEN 'explicit append-only abandonment disposition' WHEN cid IS NOT NULL AND aid IS NOT NULL AND eid IS NOT NULL AND oid IS NOT NULL AND uid IS NOT NULL AND did IS NULL AND cm=am AND ce=ae AND co=ao AND ca=aa AND ct=at THEN 'complete exact adoption graph' ELSE 'partial or mismatched durable adoption evidence' END FROM g
$fn$;

DO $acl$
DECLARE owner_role text:=current_setting('foundation.rule_governance_owner_role',true); publisher_role text:=current_setting('foundation.rule_publisher_role',true); activator_role text:=current_setting('foundation.rule_activator_role',true); adopter_role text:=current_setting('foundation.rule_adopter_role',true); resolver_role text:=current_setting('foundation.rule_resolver_role',true); repair_role text:=current_setting('foundation.release_repair_role',true); controller_role text:=current_setting('foundation.release_controller_role',true);
BEGIN
 REVOKE ALL ON TABLE normative.knowledge_layer_rule_release_foundation,normative.knowledge_layer_rule_governance_claim,normative.knowledge_layer_rule_publication,normative.knowledge_layer_rule_activation,normative.knowledge_layer_rule_runtime_adoption,normative.knowledge_layer_rule_governance_event,normative.knowledge_layer_rule_governance_disposition,normative.knowledge_layer_rule_capability_decision,eventing.knowledge_layer_rule_governance_outbox,audit.knowledge_layer_rule_governance_audit FROM PUBLIC;
 REVOKE ALL ON FUNCTION normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid),normative.import_knowledge_layer_rule_publication_evidence_v1(uuid,uuid,text,uuid,timestamptz,text,text,text,uuid,uuid),normative.activate_knowledge_layer_rule_v1(uuid,uuid,text,uuid,text,text,text,uuid,uuid),normative.adopt_knowledge_layer_rule_runtime_v1(uuid,uuid,text,uuid,text,text,text,text,uuid,uuid),normative.bootstrap_legacy_knowledge_layer_rule_runtime_v1(uuid,uuid,text,text,text,text,text,uuid,uuid),normative.resolve_knowledge_layer_rule_runtime_adoption_v1(uuid),normative.record_rule_governance_capability_decision_v1(uuid,text,boolean,uuid,text,uuid,uuid),normative.record_abandoned_rule_governance_operation_v1(text,uuid,text,text,uuid,uuid),normative.reconcile_knowledge_layer_rule_publication_v1(uuid),normative.reconcile_knowledge_layer_rule_activation_v1(uuid),normative.reconcile_knowledge_layer_rule_runtime_adoption_v1(uuid) FROM PUBLIC;
 EXECUTE format('GRANT EXECUTE ON FUNCTION normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid),normative.import_knowledge_layer_rule_publication_evidence_v1(uuid,uuid,text,uuid,timestamptz,text,text,text,uuid,uuid) TO %I',publisher_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION normative.activate_knowledge_layer_rule_v1(uuid,uuid,text,uuid,text,text,text,uuid,uuid) TO %I',activator_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION normative.adopt_knowledge_layer_rule_runtime_v1(uuid,uuid,text,uuid,text,text,text,text,uuid,uuid),normative.bootstrap_legacy_knowledge_layer_rule_runtime_v1(uuid,uuid,text,text,text,text,text,uuid,uuid) TO %I',adopter_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION normative.resolve_knowledge_layer_rule_runtime_adoption_v1(uuid) TO %I',resolver_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION normative.reconcile_knowledge_layer_rule_publication_v1(uuid),normative.reconcile_knowledge_layer_rule_activation_v1(uuid),normative.reconcile_knowledge_layer_rule_runtime_adoption_v1(uuid),normative.record_abandoned_rule_governance_operation_v1(text,uuid,text,text,uuid,uuid) TO %I',repair_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION normative.record_rule_governance_capability_decision_v1(uuid,text,boolean,uuid,text,uuid,uuid) TO %I',controller_role);
 FOR controller_role IN SELECT unnest(ARRAY['foundation_0022_uuid(uuid,text)','foundation_0022_rule_material_hash(uuid)','foundation_0022_rule_semantic_hash(uuid)','foundation_0022_fail(text)','foundation_0022_authorized(text)','foundation_0022_capability_enabled(text)','foundation_0022_insert_graph(text,uuid,uuid,text,text,text,uuid,uuid,jsonb)']) LOOP
   EXECUTE format('REVOKE ALL ON FUNCTION normative.%s FROM PUBLIC',controller_role);
 END LOOP;
 GRANT EXECUTE ON FUNCTION normative.foundation_0022_rule_material_hash(uuid),normative.foundation_0022_rule_semantic_hash(uuid) TO CURRENT_USER;
 EXECUTE format('GRANT EXECUTE ON FUNCTION normative.foundation_0022_rule_material_hash(uuid) TO %I',publisher_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_uuid(uuid,text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_rule_material_hash(uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_rule_semantic_hash(uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_fail(text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_authorized(text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_capability_enabled(text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_insert_graph(text,uuid,uuid,text,text,text,uuid,uuid,jsonb) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.import_knowledge_layer_rule_publication_evidence_v1(uuid,uuid,text,uuid,timestamptz,text,text,text,uuid,uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.activate_knowledge_layer_rule_v1(uuid,uuid,text,uuid,text,text,text,uuid,uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.adopt_knowledge_layer_rule_runtime_v1(uuid,uuid,text,uuid,text,text,text,text,uuid,uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.bootstrap_legacy_knowledge_layer_rule_runtime_v1(uuid,uuid,text,text,text,text,text,uuid,uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.resolve_knowledge_layer_rule_runtime_adoption_v1(uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.record_rule_governance_capability_decision_v1(uuid,text,boolean,uuid,text,uuid,uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.record_abandoned_rule_governance_operation_v1(text,uuid,text,text,uuid,uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.reconcile_knowledge_layer_rule_publication_v1(uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.reconcile_knowledge_layer_rule_activation_v1(uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.reconcile_knowledge_layer_rule_runtime_adoption_v1(uuid) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_reject_mutation() OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION normative.foundation_0022_commit_window() OWNER TO %I',owner_role);
 REVOKE ALL ON FUNCTION normative.foundation_0022_commit_window() FROM PUBLIC;
 EXECUTE format('REVOKE CREATE ON SCHEMA normative FROM %I',owner_role);
END $acl$;
"""


REVERSE_SQL = r"""
DO $reverse$
BEGIN
 IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_claim) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_publication) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_activation) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_runtime_adoption) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_event) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_governance_disposition) OR
    EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_capability_decision) THEN
   RAISE EXCEPTION '0022 is operationally forward-only after retained governance history exists';
 END IF;
END $reverse$;
DROP FUNCTION normative.reconcile_knowledge_layer_rule_runtime_adoption_v1(uuid);
DROP FUNCTION normative.reconcile_knowledge_layer_rule_activation_v1(uuid);
DROP FUNCTION normative.reconcile_knowledge_layer_rule_publication_v1(uuid);
DROP FUNCTION normative.record_abandoned_rule_governance_operation_v1(text,uuid,text,text,uuid,uuid);
DROP FUNCTION normative.record_rule_governance_capability_decision_v1(uuid,text,boolean,uuid,text,uuid,uuid);
DROP FUNCTION normative.resolve_knowledge_layer_rule_runtime_adoption_v1(uuid);
DROP FUNCTION normative.bootstrap_legacy_knowledge_layer_rule_runtime_v1(uuid,uuid,text,text,text,text,text,uuid,uuid);
DROP FUNCTION normative.adopt_knowledge_layer_rule_runtime_v1(uuid,uuid,text,uuid,text,text,text,text,uuid,uuid);
DROP FUNCTION normative.activate_knowledge_layer_rule_v1(uuid,uuid,text,uuid,text,text,text,uuid,uuid);
DROP FUNCTION normative.import_knowledge_layer_rule_publication_evidence_v1(uuid,uuid,text,uuid,timestamptz,text,text,text,uuid,uuid);
DROP FUNCTION normative.publish_knowledge_layer_rule_v1(uuid,uuid,text,text,text,uuid,uuid);
DROP FUNCTION normative.foundation_0022_insert_graph(text,uuid,uuid,text,text,text,uuid,uuid,jsonb);
DROP FUNCTION normative.foundation_0022_capability_enabled(text);
DROP FUNCTION normative.foundation_0022_authorized(text);
DROP FUNCTION normative.foundation_0022_fail(text);
DROP FUNCTION normative.foundation_0022_rule_semantic_hash(uuid);
DROP FUNCTION normative.foundation_0022_rule_material_hash(uuid);
DROP FUNCTION normative.foundation_0022_uuid(uuid,text);
DROP TRIGGER klr_governance_commit_window ON normative.knowledge_layer_rule_governance_claim;
DROP FUNCTION normative.foundation_0022_commit_window();
DROP TABLE normative.knowledge_layer_rule_capability_decision;
DROP TABLE normative.knowledge_layer_rule_governance_disposition;
DROP TABLE audit.knowledge_layer_rule_governance_audit;
DROP TABLE eventing.knowledge_layer_rule_governance_outbox;
DROP TABLE normative.knowledge_layer_rule_governance_event;
DROP TABLE normative.knowledge_layer_rule_runtime_adoption;
DROP TABLE normative.knowledge_layer_rule_activation;
DROP TABLE normative.knowledge_layer_rule_publication;
DROP TABLE normative.knowledge_layer_rule_governance_claim;
DROP FUNCTION normative.foundation_0022_reject_mutation();
DROP TABLE normative.knowledge_layer_rule_release_foundation;
"""


def forward(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0021_first_governed_knowledge_rule_application_poc")]
    operations = [migrations.RunPython(forward, reverse)]
