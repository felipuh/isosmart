"""Phase 17 controlled-execution recovery and least-privilege hardening.

This migration adds no business action and no EffectivenessCheck schema.  It
serializes the existing tenant/idempotency claim before Phase 15's durable row
lookup, installs exact read/reconcile capabilities for the forward action and
its separately governed compensation, and removes three unused owner reads.
"""

from django.db import migrations


FORWARD_SQL = r"""
CREATE FUNCTION qms.foundation_0016_serialized_controlled_opportunity_execution(
 p_authorization_id uuid,p_idempotency_key text,p_action_type text
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
DECLARE v_tenant uuid:=NULLIF(current_setting('app.tenant_id',true),'')::uuid;
BEGIN
 IF v_tenant IS NULL OR p_idempotency_key IS NULL OR btrim(p_idempotency_key)='' OR
    p_action_type NOT IN ('opportunity.defer_evaluation','opportunity.resume_evaluation') THEN
  RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='controlled execution context denied';
 END IF;
 -- The durable owner remains qms.action_execution.  This transaction lock only
 -- closes the pre-row race so one first caller creates it and waiters then see
 -- the committed row.  The table UNIQUE(tenant_id,idempotency_key) remains the
 -- independent durable constraint.
 PERFORM pg_advisory_xact_lock(hashtextextended(
   v_tenant::text||':controlled-execution-claim:'||p_idempotency_key,0));
 RETURN qms.foundation_0015_controlled_opportunity_execution(
   p_authorization_id,p_idempotency_key,p_action_type);
END $fn$;

CREATE FUNCTION qms.defer_opportunity_evaluation_recoverable(
 p_authorization_id uuid,p_idempotency_key text
) RETURNS jsonb LANGUAGE sql SECURITY DEFINER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
 SELECT qms.foundation_0016_serialized_controlled_opportunity_execution(
  p_authorization_id,p_idempotency_key,'opportunity.defer_evaluation')
$fn$;

CREATE FUNCTION qms.resume_opportunity_evaluation_recoverable(
 p_authorization_id uuid,p_idempotency_key text
) RETURNS jsonb LANGUAGE sql SECURITY DEFINER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
 SELECT qms.foundation_0016_serialized_controlled_opportunity_execution(
  p_authorization_id,p_idempotency_key,'opportunity.resume_evaluation')
$fn$;

CREATE FUNCTION qms.foundation_0016_reconcile_controlled_opportunity_execution(
 p_authorization_id uuid,p_idempotency_key text,p_action_type text
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
DECLARE v_tenant uuid:=NULLIF(current_setting('app.tenant_id',true),'')::uuid;
 a qms.execution_authorization%ROWTYPE; p qms.action_plan%ROWTYPE;
 e qms.action_execution%ROWTYPE; r qms.action_execution_receipt%ROWTYPE;
 prior qms.opportunity%ROWTYPE; after_row qms.opportunity%ROWTYPE;
 v_expected_source text; v_expected_destination text; v_expected_outcome text;
 v_outcome text:='INCONSISTENT'; v_reason text:='durable_provenance_mismatch';
 v_domain_events integer:=0; v_domain_outbox integer:=0; v_domain_audit integer:=0;
 v_execution_events integer:=0; v_execution_outbox integer:=0; v_execution_audit integer:=0;
 v_receipts integer:=0; v_revisions integer:=0; v_audit_id uuid;
 v_idempotency_hash text; v_result jsonb; v_observed jsonb; v_trace uuid;
BEGIN
 IF v_tenant IS NULL OR p_idempotency_key IS NULL OR btrim(p_idempotency_key)='' OR
    p_action_type NOT IN ('opportunity.defer_evaluation','opportunity.resume_evaluation') THEN
  RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='controlled reconciliation context denied';
 END IF;
 v_idempotency_hash:=encode(sha256(convert_to(p_idempotency_key,'UTF8')),'hex');
 SELECT * INTO STRICT a FROM qms.execution_authorization
  WHERE id=p_authorization_id AND tenant_id=v_tenant;
 SELECT * INTO STRICT p FROM qms.action_plan WHERE id=a.action_plan_id;
 v_trace:=a.trace_id;
 IF p_action_type='opportunity.defer_evaluation' THEN
  v_expected_source:='under_evaluation'; v_expected_destination:='deferred';
  v_expected_outcome:='opportunity_deferred';
 ELSE
  v_expected_source:='deferred'; v_expected_destination:='under_evaluation';
  v_expected_outcome:='opportunity_evaluation_resumed';
 END IF;

 IF p.action_type<>p_action_type OR p.target_type<>'Opportunity' OR
    p.action_plan_hash<>a.action_plan_hash OR p.organization_id<>a.organization_id OR
    p.parameters->>'policy_id'<>'controlled-qms-action-policy/v1' OR
    p.parameters->>'expected_current_state'<>v_expected_source OR
    p.parameters->>'desired_state'<>v_expected_destination THEN
  v_reason:='authorization_plan_provenance_conflict';
 ELSE
  SELECT * INTO e FROM qms.action_execution
   WHERE tenant_id=v_tenant AND idempotency_key=p_idempotency_key;
  IF NOT FOUND THEN
   SELECT * INTO prior FROM qms.opportunity
    WHERE id=(p.parameters->>'expected_revision_id')::uuid
      AND tenant_id=v_tenant AND organization_id=p.organization_id
      AND lineage_id=p.target_id::uuid;
   IF FOUND AND prior.revision=(p.parameters->>'expected_revision')::integer
      AND prior.status=v_expected_source
      AND qms.foundation_0015_opportunity_state_hash(
        prior.tenant_id,prior.organization_id,prior.lineage_id,prior.id,prior.revision,
        prior.process_id,prior.hypothesis,prior.benefit,prior.feasibility,prior.status
      )=p.parameters->>'expected_state_hash'
      AND NOT EXISTS(SELECT 1 FROM qms.opportunity WHERE previous_revision_id=prior.id) THEN
    v_outcome:='NOT_COMMITTED'; v_reason:='no_claim_and_target_still_exact';
   ELSE
    v_reason:='no_claim_but_target_is_not_safe_to_retry';
   END IF;
  ELSIF e.execution_authorization_id<>a.id OR e.action_plan_id<>p.id OR
        e.action_plan_hash<>p.action_plan_hash OR e.executor_type<>'controlled_opportunity' OR
        e.organization_id<>p.organization_id THEN
   v_reason:='idempotency_claim_provenance_conflict';
  ELSIF e.status<>'succeeded' OR e.completed_at IS NULL THEN
   v_reason:='nonterminal_or_abandoned_claim';
  ELSE
   SELECT count(*) INTO v_receipts FROM qms.action_execution_receipt
    WHERE action_execution_id=e.id;
   IF v_receipts=1 THEN
    SELECT * INTO STRICT r FROM qms.action_execution_receipt WHERE action_execution_id=e.id;
    IF r.executor_type='controlled_opportunity' AND r.outcome=v_expected_outcome AND
       r.action_plan_hash=p.action_plan_hash AND r.trace_id=e.trace_id AND
       r.result_hash=qms.foundation_0015_canonical_hash(r.result) AND
       r.result->>'execution_id'=e.id::text AND
       r.result->>'action_plan_hash'=p.action_plan_hash AND
       r.result->>'action_type'=p_action_type AND
       r.result->>'policy_id'='controlled-qms-action-policy/v1' AND
       r.result->>'before_revision_id'=p.parameters->>'expected_revision_id' AND
       r.result->>'opportunity_lineage_id'=p.target_id AND
       r.result->>'before_status'=v_expected_source AND
       r.result->>'after_status'=v_expected_destination AND
       r.result->>'effectiveness_claimed'='false' THEN
     SELECT count(*) INTO v_revisions FROM qms.opportunity
      WHERE id=(r.result->>'after_revision_id')::uuid
        AND previous_revision_id=(r.result->>'before_revision_id')::uuid
        AND lineage_id=(r.result->>'opportunity_lineage_id')::uuid
        AND tenant_id=v_tenant AND organization_id=p.organization_id
        AND status=v_expected_destination;
     SELECT * INTO after_row FROM qms.opportunity
      WHERE id=(r.result->>'after_revision_id')::uuid;
     SELECT count(*) INTO v_domain_events FROM eventing.domain_event
      WHERE event_id=(r.result->>'domain_event_id')::uuid
        AND tenant_id=v_tenant AND event_type='opportunity.status_changed'
        AND aggregate_type='opportunity'
        AND aggregate_id=(r.result->>'opportunity_lineage_id')::uuid
        AND trace_id=e.trace_id
        AND payload->>'previous_revision_id'=r.result->>'before_revision_id'
        AND payload->>'revision_id'=r.result->>'after_revision_id';
     SELECT count(*) INTO v_domain_outbox FROM eventing.transactional_outbox
      WHERE domain_event_id=(r.result->>'domain_event_id')::uuid AND tenant_id=v_tenant;
     SELECT count(*) INTO v_domain_audit FROM audit.immutable_audit_log
      WHERE tenant_id=v_tenant AND stream_type='opportunity'
        AND stream_id=(r.result->>'opportunity_lineage_id')::uuid
        AND action='opportunity.status_changed' AND trace_id=e.trace_id
        AND occurred_at>=e.started_at AND occurred_at<=e.completed_at;
     SELECT count(*) INTO v_execution_events FROM eventing.domain_event
      WHERE tenant_id=v_tenant AND event_type='action_execution.succeeded'
        AND aggregate_type='action_execution' AND aggregate_id=e.id
        AND trace_id=e.trace_id AND payload->>'execution_id'=e.id::text;
     SELECT count(*) INTO v_execution_outbox FROM eventing.transactional_outbox o
      JOIN eventing.domain_event de ON de.event_id=o.domain_event_id
      WHERE o.tenant_id=v_tenant AND de.aggregate_type='action_execution'
        AND de.aggregate_id=e.id AND de.event_type='action_execution.succeeded';
     SELECT count(*) INTO v_execution_audit FROM audit.immutable_audit_log
      WHERE tenant_id=v_tenant AND stream_type='action_execution' AND stream_id=e.id
        AND action='action_execution.succeeded' AND trace_id=e.trace_id;
     IF ROW(v_revisions,v_domain_events,v_domain_outbox,v_domain_audit,
            v_receipts,v_execution_events,v_execution_outbox,v_execution_audit)
        = ROW(1,1,1,1,1,1,1,1) THEN
      v_outcome:='COMMITTED'; v_reason:='exact_durable_provenance_complete';
      v_result:=r.result||jsonb_build_object('replayed',true);
     END IF;
    END IF;
   ELSE
    v_reason:='terminal_execution_without_exactly_one_receipt';
   END IF;
  END IF;
 END IF;

 v_observed:=jsonb_build_object(
  'opportunity_revisions',v_revisions,'opportunity_events',v_domain_events,
  'opportunity_outbox',v_domain_outbox,'opportunity_audit',v_domain_audit,
  'receipts',v_receipts,'execution_events',v_execution_events,
  'execution_outbox',v_execution_outbox,'execution_audit',v_execution_audit);
 SELECT audit.append_immutable_audit(
  v_tenant,'execution_reconciliation',COALESCE(e.id,a.id),'system',
  'controlled-execution-reconciler','controlled_execution.reconciled',
  'action_execution',COALESCE(e.id,a.id),v_trace,statement_timestamp(),NULL,
  qms.foundation_0015_canonical_hash(jsonb_build_object(
    'outcome',v_outcome,'reason',v_reason,'observed',v_observed)),
  '{"canonicalization":"iso-smart-canonical-json-v1","value":'||
    qms.foundation_0015_canonical_json_value(jsonb_build_object(
      'governance_artifact_id',a.id::text,'action_plan_id',p.id::text,
      'action_plan_hash',p.action_plan_hash,'action_type',p_action_type,
      'idempotency_hash',v_idempotency_hash,'tenant_id',v_tenant::text,
      'organization_id',p.organization_id::text,'trace_id',v_trace::text,
      'outcome',v_outcome,'reason',v_reason,'observed',v_observed))||'}'
 ) INTO v_audit_id;
 RETURN jsonb_build_object(
  'outcome',v_outcome,'reason',v_reason,'authorization_id',a.id::text,
  'action_plan_id',p.id::text,'action_plan_hash',p.action_plan_hash,
  'action_type',p_action_type,'idempotency_hash',v_idempotency_hash,
  'tenant_id',v_tenant::text,'organization_id',p.organization_id::text,
  'trace_id',v_trace::text,'execution_id',CASE WHEN e.id IS NULL THEN NULL ELSE e.id::text END,
  'observed',v_observed,'reconciliation_audit_id',v_audit_id::text,'receipt',v_result);
END $fn$;

CREATE FUNCTION qms.reconcile_defer_opportunity_evaluation(
 p_authorization_id uuid,p_idempotency_key text
) RETURNS jsonb LANGUAGE sql SECURITY DEFINER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
 SELECT qms.foundation_0016_reconcile_controlled_opportunity_execution(
  p_authorization_id,p_idempotency_key,'opportunity.defer_evaluation')
$fn$;

CREATE FUNCTION qms.reconcile_resume_opportunity_evaluation(
 p_authorization_id uuid,p_idempotency_key text
) RETURNS jsonb LANGUAGE sql SECURITY DEFINER VOLATILE
SET search_path=pg_catalog,pg_temp AS $fn$
 SELECT qms.foundation_0016_reconcile_controlled_opportunity_execution(
  p_authorization_id,p_idempotency_key,'opportunity.resume_evaluation')
$fn$;

REVOKE ALL ON FUNCTION qms.foundation_0016_serialized_controlled_opportunity_execution(uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.foundation_0016_reconcile_controlled_opportunity_execution(uuid,text,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.defer_opportunity_evaluation_recoverable(uuid,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.resume_opportunity_evaluation_recoverable(uuid,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.reconcile_defer_opportunity_evaluation(uuid,text) FROM PUBLIC;
REVOKE ALL ON FUNCTION qms.reconcile_resume_opportunity_evaluation(uuid,text) FROM PUBLIC;

DO $grants$
DECLARE owner_role text:=current_setting('foundation.qms_action_owner_role',true);
        executor_role text:=current_setting('foundation.executor_role',true);
BEGIN
 EXECUTE format('GRANT CREATE ON SCHEMA qms TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION qms.defer_opportunity_evaluation_recoverable(uuid,text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION qms.resume_opportunity_evaluation_recoverable(uuid,text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION qms.reconcile_defer_opportunity_evaluation(uuid,text) OWNER TO %I',owner_role);
 EXECUTE format('ALTER FUNCTION qms.reconcile_resume_opportunity_evaluation(uuid,text) OWNER TO %I',owner_role);
 EXECUTE format('REVOKE CREATE ON SCHEMA qms FROM %I',owner_role);
 EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0016_serialized_controlled_opportunity_execution(uuid,text,text),qms.foundation_0016_reconcile_controlled_opportunity_execution(uuid,text,text) TO %I',owner_role);
 EXECUTE format('GRANT SELECT ON audit.immutable_audit_log TO %I',owner_role);
 EXECUTE format('CREATE POLICY foundation_audit_phase17_owner ON audit.immutable_audit_log FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('REVOKE SELECT ON qms.organization,qms.user_projection,qms.recommendation FROM %I',owner_role);
 EXECUTE format('DROP POLICY foundation_organization_phase16_owner ON qms.organization');
 EXECUTE format('DROP POLICY foundation_user_projection_phase16_owner ON qms.user_projection');
 EXECUTE format('DROP POLICY qms_recommendation_phase16_owner ON qms.recommendation');
END $grants$;
"""


REVERSE_SQL = r"""
DO $restore$
DECLARE owner_role text:=current_setting('foundation.qms_action_owner_role',true);
BEGIN
 EXECUTE format('DROP POLICY foundation_audit_phase17_owner ON audit.immutable_audit_log');
 EXECUTE format('REVOKE SELECT ON audit.immutable_audit_log FROM %I',owner_role);
 EXECUTE format('GRANT SELECT ON qms.organization,qms.user_projection,qms.recommendation TO %I',owner_role);
 EXECUTE format('CREATE POLICY foundation_organization_phase16_owner ON qms.organization FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY foundation_user_projection_phase16_owner ON qms.user_projection FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
 EXECUTE format('CREATE POLICY qms_recommendation_phase16_owner ON qms.recommendation FOR SELECT TO %I USING(tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',owner_role);
END $restore$;

DROP FUNCTION qms.reconcile_resume_opportunity_evaluation(uuid,text);
DROP FUNCTION qms.reconcile_defer_opportunity_evaluation(uuid,text);
DROP FUNCTION qms.foundation_0016_reconcile_controlled_opportunity_execution(uuid,text,text);
DROP FUNCTION qms.resume_opportunity_evaluation_recoverable(uuid,text);
DROP FUNCTION qms.defer_opportunity_evaluation_recoverable(uuid,text);
DROP FUNCTION qms.foundation_0016_serialized_controlled_opportunity_execution(uuid,text,text);
"""


def apply_phase17(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(FORWARD_SQL, params=None)
        from psycopg2 import sql

        owner_role = schema_editor.connection.settings_dict["OPTIONS"]["options"].split(
            "foundation.qms_action_owner_role=", 1
        )[1].split()[0]
        executor_role = schema_editor.connection.settings_dict["OPTIONS"]["options"].split(
            "foundation.executor_role=", 1
        )[1].split()[0]
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(owner_role)))
            cursor.execute(
                sql.SQL(
                    "REVOKE EXECUTE ON FUNCTION qms.defer_opportunity_evaluation(uuid,text),"
                    "qms.resume_opportunity_evaluation(uuid,text) FROM {}"
                ).format(sql.Identifier(executor_role))
            )
            cursor.execute(
                sql.SQL(
                    "GRANT EXECUTE ON FUNCTION qms.defer_opportunity_evaluation_recoverable(uuid,text),"
                    "qms.resume_opportunity_evaluation_recoverable(uuid,text),"
                    "qms.reconcile_defer_opportunity_evaluation(uuid,text),"
                    "qms.reconcile_resume_opportunity_evaluation(uuid,text) TO {}"
                ).format(sql.Identifier(executor_role))
            )
            cursor.execute("RESET ROLE")


def reverse_phase17(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(REVERSE_SQL, params=None)
        from psycopg2 import sql

        owner_role = schema_editor.connection.settings_dict["OPTIONS"]["options"].split(
            "foundation.qms_action_owner_role=", 1
        )[1].split()[0]
        executor_role = schema_editor.connection.settings_dict["OPTIONS"]["options"].split(
            "foundation.executor_role=", 1
        )[1].split()[0]
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(sql.SQL("SET LOCAL ROLE {}").format(sql.Identifier(owner_role)))
            cursor.execute(
                sql.SQL(
                    "GRANT EXECUTE ON FUNCTION qms.defer_opportunity_evaluation(uuid,text),"
                    "qms.resume_opportunity_evaluation(uuid,text) TO {}"
                ).format(sql.Identifier(executor_role))
            )
            cursor.execute("RESET ROLE")


class Migration(migrations.Migration):
    dependencies = [("foundation", "0015_first_controlled_qms_mutation_poc")]
    operations = [migrations.RunPython(apply_phase17, reverse_phase17)]
