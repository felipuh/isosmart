"""Phase 26 exact governed KnowledgeLayerRule source-reference application POC."""

from django.db import migrations


FORWARD_SQL = r"""
DO $migration$
DECLARE
  executor_role text := current_setting('foundation.learning_application_executor_role',true);
  owner_role text := current_setting('foundation.knowledge_rule_application_owner_role',true);
  curator_role text := current_setting('foundation.normative_curator_role',true);
  learning_role text := current_setting('foundation.learning_governance_role',true);
  reviewer_role text := current_setting('foundation.learning_reviewer_role',true);
  approver_role text := current_setting('foundation.learning_approver_role',true);
  authorizer_role text := current_setting('foundation.learning_authorizer_role',true);
BEGIN
  IF executor_role IS NULL OR executor_role='' OR owner_role IS NULL OR owner_role='' OR
     curator_role IS NULL OR curator_role='' OR learning_role IS NULL OR learning_role='' OR
     reviewer_role IS NULL OR reviewer_role='' OR approver_role IS NULL OR approver_role='' OR
     authorizer_role IS NULL OR authorizer_role='' THEN
    RAISE EXCEPTION 'Phase 26 exact executor, capability owner, and curator roles are required';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=executor_role AND rolcanlogin AND
      NOT rolsuper AND NOT rolbypassrls AND NOT rolinherit) THEN
    RAISE EXCEPTION 'Phase 26 executor role attributes are unsafe';
  END IF;
  IF NOT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=owner_role AND NOT rolcanlogin AND
      NOT rolsuper AND NOT rolbypassrls AND NOT rolinherit) THEN
    RAISE EXCEPTION 'Phase 26 capability owner role attributes are unsafe';
  END IF;

  CREATE TABLE qms.learning_target_application_claim (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    application_identity char(64) NOT NULL UNIQUE CHECK(application_identity ~ '^[0-9a-f]{64}$'),
    material_hash char(64) NOT NULL CHECK(material_hash ~ '^[0-9a-f]{64}$'),
    authorization_id uuid NOT NULL UNIQUE REFERENCES qms.learning_application_authorization(id) ON DELETE RESTRICT,
    forward_receipt_id uuid,
    receipt_id uuid NOT NULL UNIQUE,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_learning_application_claim_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT
  );

  CREATE TABLE normative.knowledge_layer_rule_event (
    id uuid PRIMARY KEY,
    event_type varchar(160) NOT NULL CHECK(event_type='knowledge_layer_rule.source_reference_corrected'),
    schema_version integer NOT NULL CHECK(schema_version=1),
    aggregate_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    aggregate_version varchar(120) NOT NULL CHECK(btrim(aggregate_version)<>''),
    payload jsonb NOT NULL CHECK(jsonb_typeof(payload)='object'),
    payload_hash char(64) NOT NULL CHECK(payload_hash ~ '^[0-9a-f]{64}$'),
    trace_id uuid NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );

  CREATE TABLE eventing.platform_transactional_outbox (
    id uuid PRIMARY KEY,
    event_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule_event(id) ON DELETE RESTRICT,
    destination varchar(160) NOT NULL CHECK(destination='platform.knowledge-layer-rule'),
    status varchar(24) NOT NULL DEFAULT 'pending' CHECK(status='pending'),
    available_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp()
  );

  CREATE TABLE qms.learning_target_application_receipt (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    application_identity char(64) NOT NULL UNIQUE,
    proposal_id uuid NOT NULL REFERENCES qms.learning_proposal(id) ON DELETE RESTRICT,
    review_ids jsonb NOT NULL CHECK(jsonb_typeof(review_ids)='array' AND jsonb_array_length(review_ids)>0),
    decision_id uuid NOT NULL REFERENCES qms.learning_proposal_decision(id) ON DELETE RESTRICT,
    authorization_id uuid NOT NULL UNIQUE REFERENCES qms.learning_application_authorization(id) ON DELETE RESTRICT,
    operation_id varchar(160) NOT NULL CHECK(operation_id='learning.knowledge_layer_rule.source_reference.correct'),
    operation_version varchar(40) NOT NULL CHECK(operation_version='v1'),
    canonicalization_version varchar(80) NOT NULL CHECK(canonicalization_version='iso-smart-learning-delta-canonical-v1'),
    delta_schema_version varchar(120) NOT NULL CHECK(delta_schema_version='learning-knowledge-layer-rule-source-reference-correction-delta-v1'),
    delta_hash char(64) NOT NULL CHECK(delta_hash ~ '^[0-9a-f]{64}$'),
    target_lineage_id uuid NOT NULL,
    before_rule_id uuid NOT NULL REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    before_version varchar(120) NOT NULL,
    before_hash char(64) NOT NULL,
    after_rule_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule(id) ON DELETE RESTRICT,
    after_version varchar(120) NOT NULL,
    after_hash char(64) NOT NULL,
    predecessor_id uuid NOT NULL,
    source_reference_before text NOT NULL,
    source_reference_after text NOT NULL,
    semantic_fingerprint char(64) NOT NULL,
    result_status varchar(24) NOT NULL CHECK(result_status='draft'),
    result_published boolean NOT NULL CHECK(result_published=false),
    runtime_effect_changed boolean NOT NULL CHECK(runtime_effect_changed=false),
    external_effects boolean NOT NULL CHECK(external_effects=false),
    application_actor varchar(255) NOT NULL CHECK(btrim(application_actor)<>''),
    trace_id uuid NOT NULL,
    target_event_id uuid NOT NULL UNIQUE REFERENCES normative.knowledge_layer_rule_event(id) ON DELETE RESTRICT,
    target_outbox_id uuid NOT NULL UNIQUE REFERENCES eventing.platform_transactional_outbox(id) ON DELETE RESTRICT,
    target_curation_audit_id uuid NOT NULL UNIQUE REFERENCES normative.curation_audit(id) ON DELETE RESTRICT,
    application_audit_id uuid NOT NULL UNIQUE,
    forward_receipt_id uuid REFERENCES qms.learning_target_application_receipt(id) ON DELETE RESTRICT,
    compensation_eligible boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_learning_application_receipt_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_learning_application_receipt_predecessor_exact CHECK(predecessor_id=before_rule_id),
    CONSTRAINT qms_learning_application_receipt_direction CHECK(
      (forward_receipt_id IS NULL AND compensation_eligible) OR
      (forward_receipt_id IS NOT NULL AND NOT compensation_eligible))
  );
  ALTER TABLE qms.learning_target_application_claim ADD CONSTRAINT qms_learning_application_claim_forward_fk
    FOREIGN KEY(forward_receipt_id) REFERENCES qms.learning_target_application_receipt(id) ON DELETE RESTRICT;

  CREATE TABLE qms.learning_target_application_audit (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL,
    organization_id uuid NOT NULL,
    receipt_id uuid NOT NULL UNIQUE REFERENCES qms.learning_target_application_receipt(id) ON DELETE RESTRICT,
    authorization_id uuid NOT NULL REFERENCES qms.learning_application_authorization(id) ON DELETE RESTRICT,
    target_before_id uuid NOT NULL,
    target_after_id uuid NOT NULL,
    delta_hash char(64) NOT NULL,
    semantic_hash char(64) NOT NULL,
    actor_id varchar(255) NOT NULL,
    trace_id uuid NOT NULL,
    payload_hash char(64) NOT NULL,
    occurred_at timestamptz NOT NULL DEFAULT statement_timestamp(),
    CONSTRAINT qms_learning_application_audit_org_fk FOREIGN KEY(tenant_id,organization_id)
      REFERENCES qms.organization(tenant_id,id) ON DELETE RESTRICT
  );

  CREATE FUNCTION qms.foundation_0021_reject_application_history_mutation()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
  BEGIN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Phase 26 application history is immutable';
  END $fn$;
  CREATE TRIGGER qms_learning_application_claim_immutable BEFORE UPDATE OR DELETE ON qms.learning_target_application_claim
    FOR EACH ROW EXECUTE FUNCTION qms.foundation_0021_reject_application_history_mutation();
  CREATE TRIGGER qms_learning_application_receipt_immutable BEFORE UPDATE OR DELETE ON qms.learning_target_application_receipt
    FOR EACH ROW EXECUTE FUNCTION qms.foundation_0021_reject_application_history_mutation();
  CREATE TRIGGER qms_learning_application_audit_immutable BEFORE UPDATE OR DELETE ON qms.learning_target_application_audit
    FOR EACH ROW EXECUTE FUNCTION qms.foundation_0021_reject_application_history_mutation();
  CREATE TRIGGER normative_learning_rule_event_immutable BEFORE UPDATE OR DELETE ON normative.knowledge_layer_rule_event
    FOR EACH ROW EXECUTE FUNCTION qms.foundation_0021_reject_application_history_mutation();
  CREATE TRIGGER eventing_platform_outbox_immutable BEFORE UPDATE OR DELETE ON eventing.platform_transactional_outbox
    FOR EACH ROW EXECUTE FUNCTION qms.foundation_0021_reject_application_history_mutation();

  ALTER TABLE qms.learning_target_application_claim ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.learning_target_application_claim FORCE ROW LEVEL SECURITY;
  ALTER TABLE qms.learning_target_application_receipt ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.learning_target_application_receipt FORCE ROW LEVEL SECURITY;
  ALTER TABLE qms.learning_target_application_audit ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.learning_target_application_audit FORCE ROW LEVEL SECURITY;
  CREATE POLICY phase26_claim_migrator ON qms.learning_target_application_claim FOR ALL TO CURRENT_USER USING(true) WITH CHECK(true);
  CREATE POLICY phase26_receipt_migrator ON qms.learning_target_application_receipt FOR ALL TO CURRENT_USER USING(true) WITH CHECK(true);
  CREATE POLICY phase26_audit_migrator ON qms.learning_target_application_audit FOR ALL TO CURRENT_USER USING(true) WITH CHECK(true);
  EXECUTE format('CREATE POLICY phase26_claim_owner ON qms.learning_target_application_claim FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_receipt_owner ON qms.learning_target_application_receipt FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_receipt_learning_governance ON qms.learning_target_application_receipt FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',learning_role);
  EXECUTE format('CREATE POLICY phase26_receipt_learning_reviewer ON qms.learning_target_application_receipt FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',reviewer_role);
  EXECUTE format('CREATE POLICY phase26_receipt_learning_approver ON qms.learning_target_application_receipt FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',approver_role);
  EXECUTE format('CREATE POLICY phase26_receipt_learning_authorizer ON qms.learning_target_application_receipt FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',authorizer_role);
  EXECUTE format('CREATE POLICY phase26_audit_owner ON qms.learning_target_application_audit FOR ALL TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_owner_proposal_read ON qms.learning_proposal FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_owner_delta_read ON qms.learning_proposal_canonical_delta FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_owner_review_read ON qms.learning_proposal_review FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_owner_decision_read ON qms.learning_proposal_decision FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_owner_authorization_read ON qms.learning_application_authorization FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
  EXECUTE format('CREATE POLICY phase26_owner_authorization_lock ON qms.learning_application_authorization FOR UPDATE TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);

  EXECUTE format('GRANT USAGE,CREATE ON SCHEMA qms,normative TO %I',owner_role);
  EXECUTE format('GRANT USAGE ON SCHEMA eventing TO %I',owner_role);
  EXECUTE format('GRANT SELECT ON qms.learning_proposal,qms.learning_proposal_canonical_delta,qms.learning_proposal_review,qms.learning_proposal_decision,qms.learning_application_authorization TO %I',owner_role);
  -- PostgreSQL row-lock clauses require UPDATE privilege. The role is NOLOGIN,
  -- application callers cannot reach raw DML, and existing immutability guards remain authoritative.
  EXECUTE format('GRANT UPDATE ON qms.learning_application_authorization TO %I',owner_role);
  EXECUTE format('GRANT SELECT,UPDATE ON normative.knowledge_layer_rule TO %I',owner_role);
  EXECUTE format('GRANT SELECT ON normative.knowledge_layer,normative.standard_edition,qms.learning_target_application_claim,qms.learning_target_application_receipt TO %I',owner_role);
  EXECUTE format('GRANT SELECT ON normative.standard_edition,qms.learning_target_application_receipt TO %I',learning_role);
  EXECUTE format('GRANT SELECT ON normative.standard_edition,qms.learning_target_application_receipt TO %I,%I,%I',reviewer_role,approver_role,authorizer_role);
  EXECUTE format('GRANT INSERT ON normative.knowledge_layer_rule,normative.curation_audit,normative.knowledge_layer_rule_event,eventing.platform_transactional_outbox,qms.learning_target_application_claim,qms.learning_target_application_receipt,qms.learning_target_application_audit TO %I',owner_role);
  EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0020_canonical_json_value(jsonb) TO %I',owner_role);

  CREATE OR REPLACE FUNCTION qms.foundation_0018_validate_proposal()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $fn$
  DECLARE target jsonb; prior record; u record;
  BEGIN
    IF NEW.tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid OR
       NEW.organization_id IS DISTINCT FROM NULLIF(current_setting('app.organization_id',true),'')::uuid OR
       NEW.actor_external_id_snapshot::text IS DISTINCT FROM current_setting('app.actor_id',true) OR
       current_setting('app.mfa_verified',true)<>'true' OR current_setting('app.access_active',true)<>'true' OR
       position('qms.learning_proposal.create' in current_setting('app.learning_permissions',true))=0 OR
       NEW.authority_context_version IS DISTINCT FROM current_setting('app.authority_context_version',true) OR
       NEW.authority_decision_reference IS DISTINCT FROM current_setting('app.authority_decision_reference',true) THEN
      RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='trusted learning-governance proposal authority required';
    END IF;
    IF NEW.target_type='ModelPolicy' THEN
      SELECT to_jsonb(t) INTO target FROM governance.model_policy t WHERE id=NEW.target_id AND lineage_id=NEW.target_lineage_id AND version=NEW.target_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.model_policy n WHERE n.previous_revision_id=t.id);
    ELSIF NEW.target_type='AgentDefinition' THEN
      SELECT to_jsonb(t) INTO target FROM governance.agent_definition t WHERE id=NEW.target_id AND lineage_id=NEW.target_lineage_id AND version=NEW.target_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.agent_definition n WHERE n.previous_revision_id=t.id);
    ELSIF NEW.target_type='KnowledgeLayerRule' THEN
      SELECT to_jsonb(t) INTO target FROM normative.knowledge_layer_rule t
       WHERE id=NEW.target_id AND lineage_id=NEW.target_lineage_id AND version=NEW.target_version
         AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule n WHERE n.previous_revision_id=t.id)
         AND (t.status='published' OR (t.status='draft' AND t.published_at IS NULL AND EXISTS(
           SELECT 1 FROM qms.learning_target_application_receipt r WHERE r.after_rule_id=t.id
             AND r.forward_receipt_id IS NULL AND r.result_status='draft' AND NOT r.result_published
             AND NOT r.runtime_effect_changed)));
    END IF;
    SELECT * INTO u FROM qms.user_projection WHERE id=NEW.actor_user_projection_id;
    IF target IS NULL THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal target is stale or not an authorized current leaf'; END IF;
    IF target IS DISTINCT FROM NEW.target_snapshot THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal target snapshot is stale or not exact'; END IF;
    IF u.id IS NULL OR u.adminapps_user_id IS DISTINCT FROM NEW.actor_external_id_snapshot THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal actor snapshot is not exact';
    END IF;
    IF NEW.predecessor_id IS NOT NULL THEN
      SELECT * INTO prior FROM qms.learning_proposal WHERE id=NEW.predecessor_id;
      IF prior.id IS NULL OR NEW.revision<>prior.revision+1 OR NEW.target_type<>prior.target_type OR
         NEW.target_id<>prior.target_id OR NEW.target_hash<>prior.target_hash OR
         EXISTS(SELECT 1 FROM qms.learning_proposal WHERE predecessor_id=prior.id) THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal history must be exact and linear';
      END IF;
    END IF;
    RETURN NEW;
  END $fn$;

  CREATE OR REPLACE FUNCTION qms.foundation_0019_current_target(p_type text,p_id uuid,p_lineage uuid,p_version text)
  RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path=pg_catalog AS $fn$
  DECLARE target jsonb;
  BEGIN
    IF p_type='ModelPolicy' THEN
      SELECT to_jsonb(t) INTO target FROM governance.model_policy t WHERE id=p_id AND lineage_id=p_lineage AND version=p_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.model_policy n WHERE n.previous_revision_id=t.id);
    ELSIF p_type='AgentDefinition' THEN
      SELECT to_jsonb(t) INTO target FROM governance.agent_definition t WHERE id=p_id AND lineage_id=p_lineage AND version=p_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.agent_definition n WHERE n.previous_revision_id=t.id);
    ELSIF p_type='KnowledgeLayerRule' THEN
      SELECT to_jsonb(t) INTO target FROM normative.knowledge_layer_rule t
       WHERE id=p_id AND lineage_id=p_lineage AND version=p_version
         AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule n WHERE n.previous_revision_id=t.id)
         AND (t.status='published' OR (t.status='draft' AND t.published_at IS NULL AND EXISTS(
           SELECT 1 FROM qms.learning_target_application_receipt r WHERE r.after_rule_id=t.id
             AND r.forward_receipt_id IS NULL AND r.result_status='draft' AND NOT r.result_published
             AND NOT r.runtime_effect_changed)));
    END IF;
    RETURN target;
  END $fn$;

  EXECUTE format($ddl$
    CREATE OR REPLACE FUNCTION normative.foundation_0009_guard_rule()
    RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog AS $body$
    DECLARE predecessor_status text; predecessor_lineage uuid; edition_status text; cycle_found boolean;
    BEGIN
      IF TG_OP='DELETE' THEN
        IF OLD.status='published' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='published knowledge layer rule is immutable'; END IF;
        RETURN OLD;
      END IF;
      IF TG_OP='UPDATE' THEN
        IF OLD.status='published' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='published knowledge layer rule is immutable'; END IF;
        IF OLD.id IS DISTINCT FROM NEW.id OR OLD.knowledge_layer_id IS DISTINCT FROM NEW.knowledge_layer_id OR
           OLD.lineage_id IS DISTINCT FROM NEW.lineage_id OR OLD.rule_key IS DISTINCT FROM NEW.rule_key OR
           OLD.version IS DISTINCT FROM NEW.version OR OLD.previous_revision_id IS DISTINCT FROM NEW.previous_revision_id OR
           OLD.logic_json IS DISTINCT FROM NEW.logic_json OR OLD.evidence_expectation IS DISTINCT FROM NEW.evidence_expectation OR
           OLD.source_reference IS DISTINCT FROM NEW.source_reference OR OLD.certifiability_classification IS DISTINCT FROM NEW.certifiability_classification OR
           OLD.created_at IS DISTINCT FROM NEW.created_at THEN
          RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='rule material fields are revision-only';
        END IF;
        IF NOT(OLD.status='draft' AND NEW.status='published' AND NEW.published_at IS NOT NULL) THEN
          RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='invalid rule publication transition';
        END IF;
      ELSIF NEW.status<>'draft' OR NEW.published_at IS NOT NULL THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='new rule revisions must start as draft';
      END IF;
      IF NEW.previous_revision_id IS NOT NULL THEN
        SELECT status,lineage_id INTO predecessor_status,predecessor_lineage FROM normative.knowledge_layer_rule WHERE id=NEW.previous_revision_id;
        IF predecessor_lineage IS DISTINCT FROM NEW.lineage_id OR
           (predecessor_status IS DISTINCT FROM 'published' AND NOT(predecessor_status='draft' AND current_user=%L)) THEN
          RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='rule predecessor is not eligible in the exact lineage';
        END IF;
        WITH RECURSIVE ancestors(id,previous_revision_id) AS (
          SELECT id,previous_revision_id FROM normative.knowledge_layer_rule WHERE id=NEW.previous_revision_id
          UNION ALL SELECT r.id,r.previous_revision_id FROM normative.knowledge_layer_rule r JOIN ancestors a ON r.id=a.previous_revision_id
        ) SELECT EXISTS(SELECT 1 FROM ancestors WHERE id=NEW.id) INTO cycle_found;
        IF cycle_found THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='rule revision cycle is forbidden'; END IF;
      END IF;
      IF TG_OP='UPDATE' AND NEW.status='published' THEN
        SELECT se.status INTO edition_status FROM normative.knowledge_layer kl JOIN normative.standard_edition se ON se.id=kl.standard_edition_id WHERE kl.id=NEW.knowledge_layer_id;
        IF edition_status IS DISTINCT FROM 'published' THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='rule publication requires a published source edition'; END IF;
      END IF;
      RETURN NEW;
    END $body$;
  $ddl$,owner_role);

  CREATE FUNCTION normative.foundation_0021_rule_hash(p_rule_id uuid)
  RETURNS text LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
    SELECT encode(sha256(convert_to('{"canonicalization":"iso-smart-canonical-json-v1","value":'||
      qms.foundation_0020_canonical_json_value(to_jsonb(r))||'}','UTF8')),'hex')
      FROM normative.knowledge_layer_rule r WHERE r.id=p_rule_id
  $fn$;

  CREATE FUNCTION normative.foundation_0021_rule_semantic_hash(p_rule_id uuid)
  RETURNS text LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog AS $fn$
    SELECT encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(jsonb_build_object(
      'fingerprint_version','iso-smart-knowledge-layer-rule-substantive-fingerprint-v1',
      'target_type','KnowledgeLayerRule','knowledge_layer_id',r.knowledge_layer_id::text,
      'knowledge_layer_type',kl.layer_type,'standard_id',se.standard_id::text,
      'standard_edition_id',se.id::text,'standard_edition_source_hash',se.source_hash,
      'lineage_id',r.lineage_id::text,'rule_key',r.rule_key,'logic_json',r.logic_json,
      'evidence_expectation',r.evidence_expectation,
      'certifiability_classification',r.certifiability_classification,
      'source_reference_scheme',split_part(r.source_reference,':',1)
    )),'UTF8')),'hex')
    FROM normative.knowledge_layer_rule r
    JOIN normative.knowledge_layer kl ON kl.id=r.knowledge_layer_id
    JOIN normative.standard_edition se ON se.id=kl.standard_edition_id
    WHERE r.id=p_rule_id
  $fn$;

  CREATE FUNCTION normative.foundation_0021_create_rule_successor(
    p_previous uuid,p_version text,p_logic jsonb,p_evidence jsonb,p_source text)
  RETURNS uuid LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
  DECLARE prior normative.knowledge_layer_rule%ROWTYPE; result_id uuid:=uuidv7();
  BEGIN
    IF current_user<>current_setting('foundation.knowledge_rule_application_owner_role',true) THEN
      RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='private successor primitive owner required';
    END IF;
    SELECT * INTO STRICT prior FROM normative.knowledge_layer_rule WHERE id=p_previous FOR UPDATE;
    IF EXISTS(SELECT 1 FROM normative.knowledge_layer_rule WHERE previous_revision_id=prior.id) THEN
      RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='only the current rule lineage head can be revised';
    END IF;
    IF p_version IS NULL OR btrim(p_version)='' OR p_logic IS NULL OR jsonb_typeof(p_logic)<>'object' OR
       p_evidence IS NULL OR jsonb_typeof(p_evidence)<>'object' THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='canonical rule successor material is invalid';
    END IF;
    INSERT INTO normative.knowledge_layer_rule(
      id,knowledge_layer_id,lineage_id,rule_key,version,previous_revision_id,status,
      logic_json,evidence_expectation,source_reference,certifiability_classification,published_at)
    VALUES(result_id,prior.knowledge_layer_id,prior.lineage_id,prior.rule_key,p_version,prior.id,'draft',
      p_logic,p_evidence,p_source,'non_certifiable_guidance',NULL);
    RETURN result_id;
  END $fn$;

  CREATE FUNCTION normative.curator_create_knowledge_layer_rule_successor_v1(
    p_previous uuid,p_version text,p_logic jsonb,p_evidence jsonb,p_source text,p_actor text,p_trace uuid)
  RETURNS TABLE(rule_id uuid,curation_audit_id uuid)
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $fn$
  DECLARE prior_status text; new_id uuid; audit_id uuid:=uuidv7();
  BEGIN
    IF session_user<>current_setting('foundation.normative_curator_role',true) THEN
      RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='normative curator principal required';
    END IF;
    SELECT status INTO STRICT prior_status FROM normative.knowledge_layer_rule WHERE id=p_previous;
    IF prior_status<>'published' THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='only a published rule revision can be revised'; END IF;
    new_id:=normative.foundation_0021_create_rule_successor(p_previous,p_version,p_logic,p_evidence,p_source);
    INSERT INTO normative.curation_audit(id,action,entity_type,entity_id,actor_id,trace_id,payload_hash,occurred_at)
    VALUES(audit_id,'knowledge_layer_rule.revised','knowledge_layer_rule',new_id,p_actor,p_trace,
      normative.foundation_0021_rule_hash(new_id),statement_timestamp());
    RETURN QUERY SELECT new_id,audit_id;
  END $fn$;

  CREATE FUNCTION qms.foundation_0021_fail(p_point text)
  RETURNS void LANGUAGE plpgsql VOLATILE SET search_path=pg_catalog AS $fn$
  BEGIN
    IF current_setting('foundation.phase26_failure_point',true)=p_point THEN
      RAISE EXCEPTION USING ERRCODE='P0001',MESSAGE='deliberate Phase 26 rollback at '||p_point;
    END IF;
  END $fn$;

  EXECUTE format($ddl$
  CREATE FUNCTION normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1(
    p_authorization_id uuid,p_expected_delta_hash text,p_forward_receipt_id uuid,p_actor_id uuid,p_trace_id uuid)
  RETURNS TABLE(receipt_id uuid,result_rule_id uuid,replayed boolean)
  LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog AS $body$
  DECLARE
    a qms.learning_application_authorization%%ROWTYPE; p qms.learning_proposal%%ROWTYPE;
    d qms.learning_proposal_canonical_delta%%ROWTYPE; dec qms.learning_proposal_decision%%ROWTYPE;
    target normative.knowledge_layer_rule%%ROWTYPE; forward qms.learning_target_application_receipt%%ROWTYPE;
    app_identity text; material text; existing qms.learning_target_application_claim%%ROWTYPE;
    new_id uuid; claim_id uuid:=uuidv7(); rec_id uuid:=uuidv7(); event_id uuid:=uuidv7();
    outbox_id uuid:=uuidv7(); curation_id uuid:=uuidv7(); app_audit_id uuid:=uuidv7();
    before_hash text; after_hash text; before_semantic text; after_semantic text;
    new_source text; successor_version text; event_payload jsonb; audit_payload jsonb; review_count integer;
  BEGIN
    IF session_user<>%L THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='dedicated Phase 26 executor required'; END IF;
    IF current_setting('app.learning_application_permission',true)<>'qms.learning_target.knowledge_rule_source_reference.apply' OR
       current_setting('app.mfa_verified',true)<>'true' OR current_setting('app.access_active',true)<>'true' OR
       current_setting('app.governance_scope',true)<>'global' THEN
      RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='trusted exact application authority required';
    END IF;
    IF p_expected_delta_hash !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='expected delta hash is invalid'; END IF;
    SELECT * INTO STRICT a FROM qms.learning_application_authorization WHERE id=p_authorization_id;
    SELECT * INTO STRICT p FROM qms.learning_proposal WHERE id=a.learning_proposal_id;
    SELECT * INTO STRICT d FROM qms.learning_proposal_canonical_delta WHERE id=a.canonical_delta_id;
    SELECT * INTO STRICT dec FROM qms.learning_proposal_decision WHERE id=a.learning_proposal_decision_id;
    IF d.delta_hash<>p_expected_delta_hash OR a.delta_hash<>p_expected_delta_hash THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='expected delta hash does not match the authorized canonical delta';
    END IF;
    app_identity:=encode(sha256(convert_to(concat_ws('|',p.id::text,dec.id::text,a.id::text,a.operation_id,
      a.operation_version,a.delta_hash,a.target_id::text,a.target_version,a.target_hash,coalesce(p_forward_receipt_id::text,'')),'UTF8')),'hex');
    material:=encode(sha256(convert_to(concat_ws('|',app_identity,dec.review_ids_snapshot::text,a.idempotency_hash,p_actor_id::text),'UTF8')),'hex');
    PERFORM pg_advisory_xact_lock(hashtextextended(app_identity,26));
    SELECT * INTO existing FROM qms.learning_target_application_claim WHERE application_identity=app_identity;
    IF FOUND THEN
      IF existing.material_hash<>material OR existing.authorization_id<>a.id OR
         existing.forward_receipt_id IS DISTINCT FROM p_forward_receipt_id THEN
        RAISE EXCEPTION USING ERRCODE='23505',MESSAGE='application identity conflict';
      END IF;
      RETURN QUERY SELECT r.id,r.after_rule_id,true FROM qms.learning_target_application_receipt r WHERE r.id=existing.receipt_id;
      RETURN;
    END IF;
    INSERT INTO qms.learning_target_application_claim(id,tenant_id,organization_id,application_identity,material_hash,
      authorization_id,forward_receipt_id,receipt_id)
    VALUES(claim_id,a.tenant_id,a.organization_id,app_identity,material,a.id,p_forward_receipt_id,rec_id);
    PERFORM qms.foundation_0021_fail('after_claim');

    SELECT * INTO STRICT a FROM qms.learning_application_authorization WHERE id=p_authorization_id FOR UPDATE;
    -- Proposal, canonical delta and decision are append-only immutable history;
    -- the mutable authorization is the single row locked above.
    SELECT * INTO STRICT p FROM qms.learning_proposal WHERE id=a.learning_proposal_id;
    SELECT * INTO STRICT d FROM qms.learning_proposal_canonical_delta WHERE id=a.canonical_delta_id;
    SELECT * INTO STRICT dec FROM qms.learning_proposal_decision WHERE id=a.learning_proposal_decision_id;
    IF a.authorization_status<>'authorized' OR dec.outcome<>'approved_for_application' OR
       EXISTS(SELECT 1 FROM qms.learning_proposal newer WHERE newer.predecessor_id=p.id) OR
       a.proposal_revision_snapshot<>p.revision OR a.proposal_material_hash IS NULL OR
       a.target_type<>'KnowledgeLayerRule' OR a.target_id<>p.target_id OR a.target_lineage_id<>p.target_lineage_id OR
       a.target_version<>p.target_version OR a.target_hash<>p.target_hash OR
       a.canonical_delta_id<>p.canonical_delta_id OR a.canonical_delta_id<>d.id OR
       a.delta_hash<>p.delta_hash OR a.delta_hash<>d.delta_hash OR a.delta_hash<>p_expected_delta_hash OR
       a.operation_id<>'learning.knowledge_layer_rule.source_reference.correct' OR a.operation_version<>'v1' OR
       a.capability_id<>a.operation_id OR a.capability_version<>a.operation_version OR
       a.canonicalization_version<>'iso-smart-learning-delta-canonical-v1' OR
       a.delta_schema_version<>'learning-knowledge-layer-rule-source-reference-correction-delta-v1' OR
       dec.learning_proposal_id<>p.id OR dec.proposal_material_hash<>a.proposal_material_hash OR
       dec.delta_hash<>a.delta_hash OR dec.target_id<>a.target_id OR dec.target_hash<>a.target_hash THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='exact governance chain is incomplete, stale, or mismatched';
    END IF;
    SELECT count(*) INTO review_count FROM qms.learning_proposal_review rv
      WHERE rv.id::text IN(SELECT jsonb_array_elements_text(dec.review_ids_snapshot))
        AND rv.learning_proposal_id=p.id AND rv.proposal_material_hash=a.proposal_material_hash
        AND rv.canonical_delta_id=a.canonical_delta_id AND rv.delta_hash=a.delta_hash
        AND rv.operation_id=a.operation_id AND rv.operation_version=a.operation_version
        AND rv.target_id=a.target_id AND rv.target_hash=a.target_hash AND rv.target_status_snapshot='valid';
    IF jsonb_typeof(dec.review_ids_snapshot)<>'array' OR review_count<>jsonb_array_length(dec.review_ids_snapshot) OR review_count=0 THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='exact selected Review set is missing or mismatched';
    END IF;
    PERFORM qms.foundation_0021_fail('after_governance_validation');

    SELECT * INTO STRICT target FROM normative.knowledge_layer_rule WHERE id=a.target_id FOR UPDATE;
    PERFORM qms.foundation_0021_fail('after_target_lock');
    before_hash:=normative.foundation_0021_rule_hash(target.id);
    IF target.lineage_id<>a.target_lineage_id OR target.version<>a.target_version OR before_hash<>a.target_hash OR
       to_jsonb(target)<>p.target_snapshot OR EXISTS(SELECT 1 FROM normative.knowledge_layer_rule WHERE previous_revision_id=target.id) THEN
      RAISE EXCEPTION USING ERRCODE='40001',MESSAGE='exact target drifted or is no longer the lineage head';
    END IF;
    IF p_forward_receipt_id IS NULL THEN
      IF target.status<>'published' THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='forward target must be published and runtime eligible'; END IF;
    ELSE
      SELECT * INTO STRICT forward FROM qms.learning_target_application_receipt WHERE id=p_forward_receipt_id;
      IF forward.forward_receipt_id IS NOT NULL OR forward.after_rule_id<>target.id OR target.status<>'draft' OR
         target.published_at IS NOT NULL OR forward.after_hash<>before_hash OR
         forward.runtime_effect_changed OR forward.result_published OR
         NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule runtime_rule
                    WHERE runtime_rule.id=forward.before_rule_id AND runtime_rule.status='published') THEN
        RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='compensation does not bind the exact inert forward Receipt and runtime vN';
      END IF;
    END IF;
    PERFORM qms.foundation_0021_fail('after_target_revalidation');

    IF convert_to(qms.foundation_0020_canonical_json_value(d.delta_document),'UTF8')<>d.canonical_bytes OR
       encode(sha256(d.canonical_bytes),'hex')<>d.delta_hash OR
       d.target_id<>target.id OR d.target_hash<>before_hash OR d.target_version<>target.version OR
       d.delta_document->>'canonicalization_version'<>'iso-smart-learning-delta-canonical-v1' OR
       d.delta_document->>'operation_id'<>'learning.knowledge_layer_rule.source_reference.correct' OR
       d.delta_document->>'operation_version'<>'v1' OR
       d.delta_document->>'delta_schema_version'<>'learning-knowledge-layer-rule-source-reference-correction-delta-v1' OR
       d.delta_document->'payload'->>'current_source_reference' IS DISTINCT FROM target.source_reference THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='canonical delta bytes, hash, target, or before reference mismatch';
    END IF;
    new_source:=d.delta_document->'payload'->>'new_source_reference';
    successor_version:=d.delta_document->'payload'->>'successor_version';
    IF p_forward_receipt_id IS NOT NULL AND new_source IS DISTINCT FROM forward.source_reference_before THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='compensation must restore the exact pre-forward source reference';
    END IF;
    IF target.source_reference !~ '^iso-smart-source-ref-v1:[0-9a-f-]{36}:[0-9a-f]{64}:[A-Za-z0-9][A-Za-z0-9._:/#-]{0,255}$' OR
       new_source !~ '^iso-smart-source-ref-v1:[0-9a-f-]{36}:[0-9a-f]{64}:[A-Za-z0-9][A-Za-z0-9._:/#-]{0,255}$' OR
       split_part(target.source_reference,':',2)<>split_part(new_source,':',2) OR
       split_part(target.source_reference,':',3)<>split_part(new_source,':',3) OR
       split_part(target.source_reference,':',4)=split_part(new_source,':',4) OR
       d.delta_document->'payload'->>'standard_edition_id'<>split_part(new_source,':',2) OR
       d.delta_document->'payload'->>'standard_edition_source_hash'<>split_part(new_source,':',3) OR
       NOT EXISTS(SELECT 1 FROM normative.knowledge_layer kl JOIN normative.standard_edition se ON se.id=kl.standard_edition_id
                  WHERE kl.id=target.knowledge_layer_id AND se.id::text=split_part(new_source,':',2)
                    AND se.status='published' AND se.source_hash=split_part(new_source,':',3)) THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='only the validated locator may change';
    END IF;
    PERFORM qms.foundation_0021_fail('after_delta_validation');
    before_semantic:=normative.foundation_0021_rule_semantic_hash(target.id);
    PERFORM qms.foundation_0021_fail('after_semantic_hash_validation');
    PERFORM qms.foundation_0021_fail('before_successor_insert');
    new_id:=normative.foundation_0021_create_rule_successor(target.id,successor_version,target.logic_json,target.evidence_expectation,new_source);
    PERFORM qms.foundation_0021_fail('after_successor_insert');
    after_hash:=normative.foundation_0021_rule_hash(new_id);
    after_semantic:=normative.foundation_0021_rule_semantic_hash(new_id);
    IF before_semantic<>after_semantic THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='semantic fingerprint changed'; END IF;

    event_payload:=jsonb_build_object('scope','global','before_rule_id',target.id::text,'after_rule_id',new_id::text,
      'lineage_id',target.lineage_id::text,'delta_hash',d.delta_hash,'semantic_hash',before_semantic,
      'result_status','draft','result_published',false,'runtime_effect_changed',false,'external_effects',false);
    INSERT INTO normative.knowledge_layer_rule_event(id,event_type,schema_version,aggregate_id,aggregate_version,payload,payload_hash,trace_id)
    VALUES(event_id,'knowledge_layer_rule.source_reference_corrected',1,new_id,successor_version,event_payload,
      encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(event_payload),'UTF8')),'hex'),p_trace_id);
    PERFORM qms.foundation_0021_fail('after_target_event');
    INSERT INTO eventing.platform_transactional_outbox(id,event_id,destination,status,available_at)
    VALUES(outbox_id,event_id,'platform.knowledge-layer-rule','pending',statement_timestamp());
    PERFORM qms.foundation_0021_fail('after_target_outbox');
    INSERT INTO normative.curation_audit(id,action,entity_type,entity_id,actor_id,trace_id,payload_hash,occurred_at)
    VALUES(curation_id,'knowledge_layer_rule.source_reference_corrected','knowledge_layer_rule',new_id,p_actor_id::text,p_trace_id,after_hash,statement_timestamp());
    PERFORM qms.foundation_0021_fail('after_target_audit');
    PERFORM qms.foundation_0021_fail('before_receipt');
    INSERT INTO qms.learning_target_application_receipt(
      id,tenant_id,organization_id,application_identity,proposal_id,review_ids,decision_id,authorization_id,
      operation_id,operation_version,canonicalization_version,delta_schema_version,delta_hash,target_lineage_id,
      before_rule_id,before_version,before_hash,after_rule_id,after_version,after_hash,predecessor_id,
      source_reference_before,source_reference_after,semantic_fingerprint,result_status,result_published,
      runtime_effect_changed,external_effects,application_actor,trace_id,target_event_id,target_outbox_id,
      target_curation_audit_id,application_audit_id,forward_receipt_id,compensation_eligible)
    VALUES(rec_id,a.tenant_id,a.organization_id,app_identity,p.id,dec.review_ids_snapshot,dec.id,a.id,
      a.operation_id,a.operation_version,a.canonicalization_version,a.delta_schema_version,a.delta_hash,target.lineage_id,
      target.id,target.version,before_hash,new_id,successor_version,after_hash,target.id,target.source_reference,new_source,
      before_semantic,'draft',false,false,false,p_actor_id::text,p_trace_id,event_id,outbox_id,curation_id,app_audit_id,
      p_forward_receipt_id,p_forward_receipt_id IS NULL);
    PERFORM qms.foundation_0021_fail('after_receipt');
    PERFORM qms.foundation_0021_fail('after_application_event');
    PERFORM qms.foundation_0021_fail('after_application_outbox');
    audit_payload:=jsonb_build_object('receipt_id',rec_id::text,'proposal_id',p.id::text,'decision_id',dec.id::text,
      'authorization_id',a.id::text,'before_rule_id',target.id::text,'after_rule_id',new_id::text,
      'delta_hash',d.delta_hash,'semantic_hash',before_semantic,'trace_id',p_trace_id::text,
      'runtime_effect_changed',false,'external_effects',false);
    INSERT INTO qms.learning_target_application_audit(id,tenant_id,organization_id,receipt_id,authorization_id,
      target_before_id,target_after_id,delta_hash,semantic_hash,actor_id,trace_id,payload_hash)
    VALUES(app_audit_id,a.tenant_id,a.organization_id,rec_id,a.id,target.id,new_id,d.delta_hash,before_semantic,
      p_actor_id::text,p_trace_id,encode(sha256(convert_to(qms.foundation_0020_canonical_json_value(audit_payload),'UTF8')),'hex'));
    PERFORM qms.foundation_0021_fail('after_application_audit');
    PERFORM qms.foundation_0021_fail('after_final_provenance_verification');
    PERFORM qms.foundation_0021_fail('before_commit');
    RETURN QUERY SELECT rec_id,new_id,false;
  END $body$;
  $ddl$,executor_role);

  REVOKE ALL ON FUNCTION normative.foundation_0021_rule_hash(uuid) FROM PUBLIC;
  REVOKE ALL ON FUNCTION normative.foundation_0021_rule_semantic_hash(uuid) FROM PUBLIC;
  REVOKE ALL ON FUNCTION normative.foundation_0021_create_rule_successor(uuid,text,jsonb,jsonb,text) FROM PUBLIC;
  REVOKE ALL ON FUNCTION normative.curator_create_knowledge_layer_rule_successor_v1(uuid,text,jsonb,jsonb,text,text,uuid) FROM PUBLIC;
  REVOKE ALL ON FUNCTION normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1(uuid,text,uuid,uuid,uuid) FROM PUBLIC;
  REVOKE ALL ON FUNCTION qms.foundation_0021_fail(text) FROM PUBLIC;
  REVOKE ALL ON FUNCTION qms.foundation_0021_reject_application_history_mutation() FROM PUBLIC;
  EXECUTE format('GRANT EXECUTE ON FUNCTION normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1(uuid,text,uuid,uuid,uuid) TO %I',executor_role);
  EXECUTE format('GRANT EXECUTE ON FUNCTION normative.curator_create_knowledge_layer_rule_successor_v1(uuid,text,jsonb,jsonb,text,text,uuid) TO %I',curator_role);
  EXECUTE format('GRANT USAGE ON SCHEMA normative TO %I,%I',executor_role,curator_role);
  EXECUTE format('ALTER FUNCTION normative.foundation_0021_rule_hash(uuid) OWNER TO %I',owner_role);
  EXECUTE format('ALTER FUNCTION normative.foundation_0021_rule_semantic_hash(uuid) OWNER TO %I',owner_role);
  EXECUTE format('ALTER FUNCTION normative.foundation_0021_create_rule_successor(uuid,text,jsonb,jsonb,text) OWNER TO %I',owner_role);
  EXECUTE format('ALTER FUNCTION normative.curator_create_knowledge_layer_rule_successor_v1(uuid,text,jsonb,jsonb,text,text,uuid) OWNER TO %I',owner_role);
  EXECUTE format('ALTER FUNCTION normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1(uuid,text,uuid,uuid,uuid) OWNER TO %I',owner_role);
  EXECUTE format('ALTER FUNCTION qms.foundation_0021_fail(text) OWNER TO %I',owner_role);
  EXECUTE format('ALTER FUNCTION qms.foundation_0021_reject_application_history_mutation() OWNER TO %I',owner_role);
END $migration$;

DO $least_privilege$
DECLARE owner_role text:=current_setting('foundation.knowledge_rule_application_owner_role',true);
BEGIN
  IF owner_role IS NULL OR owner_role='' THEN RAISE EXCEPTION 'missing foundation.knowledge_rule_application_owner_role'; END IF;
  EXECUTE format('REVOKE CREATE ON SCHEMA qms,normative FROM %I',owner_role);
END $least_privilege$;
"""


REVERSE_SQL = r"""
DO $migration$
BEGIN
  IF EXISTS(SELECT 1 FROM qms.learning_target_application_claim) OR
     EXISTS(SELECT 1 FROM qms.learning_target_application_receipt) OR
     EXISTS(SELECT 1 FROM qms.learning_target_application_audit) OR
     EXISTS(SELECT 1 FROM normative.knowledge_layer_rule_event) OR
     EXISTS(SELECT 1 FROM eventing.platform_transactional_outbox) THEN
    RAISE EXCEPTION '0021 is forward-only after governed target application history exists';
  END IF;
END $migration$;
DROP FUNCTION normative.apply_validated_knowledge_layer_rule_source_reference_correction_v1(uuid,text,uuid,uuid,uuid);
DROP FUNCTION normative.curator_create_knowledge_layer_rule_successor_v1(uuid,text,jsonb,jsonb,text,text,uuid);
DROP FUNCTION normative.foundation_0021_create_rule_successor(uuid,text,jsonb,jsonb,text);
DROP FUNCTION normative.foundation_0021_rule_semantic_hash(uuid);
DROP FUNCTION normative.foundation_0021_rule_hash(uuid);
DROP FUNCTION qms.foundation_0021_fail(text);
DROP POLICY phase26_owner_authorization_lock ON qms.learning_application_authorization;
DROP POLICY phase26_owner_authorization_read ON qms.learning_application_authorization;
DROP POLICY phase26_owner_decision_read ON qms.learning_proposal_decision;
DROP POLICY phase26_owner_review_read ON qms.learning_proposal_review;
DROP POLICY phase26_owner_delta_read ON qms.learning_proposal_canonical_delta;
DROP POLICY phase26_owner_proposal_read ON qms.learning_proposal;
DROP POLICY phase26_receipt_learning_authorizer ON qms.learning_target_application_receipt;
DROP POLICY phase26_receipt_learning_approver ON qms.learning_target_application_receipt;
DROP POLICY phase26_receipt_learning_reviewer ON qms.learning_target_application_receipt;
DROP POLICY phase26_receipt_learning_governance ON qms.learning_target_application_receipt;
DO $reverse_grant$
DECLARE learning_role text:=current_setting('foundation.learning_governance_role',true);
        reviewer_role text:=current_setting('foundation.learning_reviewer_role',true);
        approver_role text:=current_setting('foundation.learning_approver_role',true);
        authorizer_role text:=current_setting('foundation.learning_authorizer_role',true);
BEGIN
  IF learning_role IS NOT NULL AND learning_role<>'' THEN
    EXECUTE format('REVOKE SELECT ON normative.standard_edition FROM %I',learning_role);
  END IF;
  IF reviewer_role IS NOT NULL AND approver_role IS NOT NULL AND authorizer_role IS NOT NULL THEN
    EXECUTE format('REVOKE SELECT ON normative.standard_edition FROM %I,%I,%I',reviewer_role,approver_role,authorizer_role);
  END IF;
END $reverse_grant$;
DROP TABLE qms.learning_target_application_audit;
ALTER TABLE qms.learning_target_application_claim DROP CONSTRAINT qms_learning_application_claim_forward_fk;
DROP TABLE qms.learning_target_application_receipt;
DROP TABLE qms.learning_target_application_claim;
DROP TABLE eventing.platform_transactional_outbox;
DROP TABLE normative.knowledge_layer_rule_event;
DROP FUNCTION qms.foundation_0021_reject_application_history_mutation();

CREATE OR REPLACE FUNCTION qms.foundation_0018_validate_proposal()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms,governance,normative AS $fn$
DECLARE target jsonb; prior record; u record;
BEGIN
  IF NEW.tenant_id IS DISTINCT FROM NULLIF(current_setting('app.tenant_id',true),'')::uuid OR
     NEW.organization_id IS DISTINCT FROM NULLIF(current_setting('app.organization_id',true),'')::uuid OR
     NEW.actor_external_id_snapshot::text IS DISTINCT FROM current_setting('app.actor_id',true) OR
     current_setting('app.mfa_verified',true)<>'true' OR current_setting('app.access_active',true)<>'true' OR
     position('qms.learning_proposal.create' in current_setting('app.learning_permissions',true))=0 OR
     NEW.authority_context_version IS DISTINCT FROM current_setting('app.authority_context_version',true) OR
     NEW.authority_decision_reference IS DISTINCT FROM current_setting('app.authority_decision_reference',true) THEN
    RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='trusted learning-governance proposal authority required';
  END IF;
  IF NEW.target_type='ModelPolicy' THEN
    SELECT to_jsonb(t) INTO target FROM governance.model_policy t WHERE id=NEW.target_id AND lineage_id=NEW.target_lineage_id AND version=NEW.target_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.model_policy n WHERE n.previous_revision_id=t.id);
  ELSIF NEW.target_type='AgentDefinition' THEN
    SELECT to_jsonb(t) INTO target FROM governance.agent_definition t WHERE id=NEW.target_id AND lineage_id=NEW.target_lineage_id AND version=NEW.target_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.agent_definition n WHERE n.previous_revision_id=t.id);
  ELSIF NEW.target_type='KnowledgeLayerRule' THEN
    SELECT to_jsonb(t) INTO target FROM normative.knowledge_layer_rule t WHERE id=NEW.target_id AND lineage_id=NEW.target_lineage_id AND version=NEW.target_version AND status='published' AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule n WHERE n.previous_revision_id=t.id);
  END IF;
  SELECT * INTO u FROM qms.user_projection WHERE id=NEW.actor_user_projection_id;
  IF target IS NULL THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal target is stale or not a published current leaf'; END IF;
  IF target IS DISTINCT FROM NEW.target_snapshot THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal target snapshot is stale or not exact'; END IF;
  IF u.id IS NULL OR u.adminapps_user_id IS DISTINCT FROM NEW.actor_external_id_snapshot THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal actor snapshot is not exact';
  END IF;
  IF NEW.predecessor_id IS NOT NULL THEN
    SELECT * INTO prior FROM qms.learning_proposal WHERE id=NEW.predecessor_id;
    IF prior.id IS NULL OR NEW.revision<>prior.revision+1 OR NEW.target_type<>prior.target_type OR
       NEW.target_id<>prior.target_id OR NEW.target_hash<>prior.target_hash OR
       EXISTS(SELECT 1 FROM qms.learning_proposal WHERE predecessor_id=prior.id) THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='LearningProposal history must be exact and linear';
    END IF;
  END IF;
  RETURN NEW;
END $fn$;

CREATE OR REPLACE FUNCTION qms.foundation_0019_current_target(p_type text,p_id uuid,p_lineage uuid,p_version text)
RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path=pg_catalog,governance,normative AS $fn$
DECLARE target jsonb;
BEGIN
  IF p_type='ModelPolicy' THEN
    SELECT to_jsonb(t) INTO target FROM governance.model_policy t WHERE id=p_id AND lineage_id=p_lineage AND version=p_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.model_policy n WHERE n.previous_revision_id=t.id);
  ELSIF p_type='AgentDefinition' THEN
    SELECT to_jsonb(t) INTO target FROM governance.agent_definition t WHERE id=p_id AND lineage_id=p_lineage AND version=p_version AND status='published' AND NOT EXISTS(SELECT 1 FROM governance.agent_definition n WHERE n.previous_revision_id=t.id);
  ELSIF p_type='KnowledgeLayerRule' THEN
    SELECT to_jsonb(t) INTO target FROM normative.knowledge_layer_rule t WHERE id=p_id AND lineage_id=p_lineage AND version=p_version AND status='published' AND NOT EXISTS(SELECT 1 FROM normative.knowledge_layer_rule n WHERE n.previous_revision_id=t.id);
  END IF;
  RETURN target;
END $fn$;

CREATE OR REPLACE FUNCTION normative.foundation_0009_guard_rule()
RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,normative AS $fn$
DECLARE predecessor_status text; predecessor_lineage uuid; edition_status text; cycle_found boolean;
BEGIN
  IF TG_OP='DELETE' THEN
    IF OLD.status='published' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='published knowledge layer rule is immutable'; END IF;
    RETURN OLD;
  END IF;
  IF TG_OP='UPDATE' THEN
    IF OLD.status='published' THEN RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='published knowledge layer rule is immutable'; END IF;
    IF OLD.id IS DISTINCT FROM NEW.id OR OLD.knowledge_layer_id IS DISTINCT FROM NEW.knowledge_layer_id OR
       OLD.lineage_id IS DISTINCT FROM NEW.lineage_id OR OLD.rule_key IS DISTINCT FROM NEW.rule_key OR
       OLD.version IS DISTINCT FROM NEW.version OR OLD.previous_revision_id IS DISTINCT FROM NEW.previous_revision_id OR
       OLD.logic_json IS DISTINCT FROM NEW.logic_json OR OLD.evidence_expectation IS DISTINCT FROM NEW.evidence_expectation OR
       OLD.source_reference IS DISTINCT FROM NEW.source_reference OR OLD.certifiability_classification IS DISTINCT FROM NEW.certifiability_classification OR
       OLD.created_at IS DISTINCT FROM NEW.created_at THEN
      RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='rule material fields are revision-only';
    END IF;
    IF NOT(OLD.status='draft' AND NEW.status='published' AND NEW.published_at IS NOT NULL) THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='invalid rule publication transition';
    END IF;
  ELSIF NEW.status<>'draft' OR NEW.published_at IS NOT NULL THEN
    RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='new rule revisions must start as draft';
  END IF;
  IF NEW.previous_revision_id IS NOT NULL THEN
    SELECT status,lineage_id INTO predecessor_status,predecessor_lineage FROM normative.knowledge_layer_rule WHERE id=NEW.previous_revision_id;
    IF predecessor_status IS DISTINCT FROM 'published' OR predecessor_lineage IS DISTINCT FROM NEW.lineage_id THEN
      RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='rule predecessor must be a published revision in the same lineage';
    END IF;
    WITH RECURSIVE ancestors(id,previous_revision_id) AS (
      SELECT id,previous_revision_id FROM normative.knowledge_layer_rule WHERE id=NEW.previous_revision_id
      UNION ALL SELECT r.id,r.previous_revision_id FROM normative.knowledge_layer_rule r JOIN ancestors a ON r.id=a.previous_revision_id
    ) SELECT EXISTS(SELECT 1 FROM ancestors WHERE id=NEW.id) INTO cycle_found;
    IF cycle_found THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='rule revision cycle is forbidden'; END IF;
  END IF;
  IF TG_OP='UPDATE' AND NEW.status='published' THEN
    SELECT se.status INTO edition_status FROM normative.knowledge_layer kl JOIN normative.standard_edition se ON se.id=kl.standard_edition_id WHERE kl.id=NEW.knowledge_layer_id;
    IF edition_status IS DISTINCT FROM 'published' THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='rule publication requires a published source edition'; END IF;
  END IF;
  RETURN NEW;
END $fn$;
"""


def forward(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)


def reverse(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)


class Migration(migrations.Migration):
    dependencies = [("foundation", "0020_exact_learning_delta_target_operation_contract")]
    operations = [migrations.RunPython(forward, reverse)]
