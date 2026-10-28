from django.db import migrations, models
import django.db.models.deletion
import uuid


FORWARD_SQL = r"""
DO $migration$
DECLARE app_role text := current_setting('foundation.app_role', true);
DECLARE worker_role text := current_setting('foundation.worker_role', true);
DECLARE curator_role text := current_setting('foundation.learning_governance_role', true);
BEGIN
  IF app_role IS NULL OR app_role='' OR worker_role IS NULL OR worker_role='' OR
     curator_role IS NULL OR curator_role='' THEN
    RAISE EXCEPTION 'Foundation Gate app, worker, and learning-governance roles are required';
  END IF;

  CREATE TABLE qms.learning_path (
    id uuid PRIMARY KEY,
    edition_id uuid NOT NULL REFERENCES normative.standard_edition(id) ON DELETE RESTRICT,
    role_code varchar(80),
    industry_code varchar(80),
    required_score numeric(5,2) NOT NULL DEFAULT 80,
    active boolean NOT NULL DEFAULT true,
    critical_concepts jsonb NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT qms_learning_path_score CHECK(required_score >= 0 AND required_score <= 100),
    CONSTRAINT qms_learning_path_critical_concepts CHECK(jsonb_typeof(critical_concepts)='array')
  );

  CREATE TABLE qms.question_bank (
    id uuid PRIMARY KEY,
    learning_path_id uuid NOT NULL REFERENCES qms.learning_path(id) ON DELETE RESTRICT,
    concept_key varchar(160) NOT NULL,
    industry_code varchar(80),
    difficulty smallint,
    scenario text NOT NULL,
    options_json jsonb NOT NULL,
    answer_key jsonb NOT NULL,
    explanation text,
    critical boolean NOT NULL DEFAULT false,
    CONSTRAINT qms_question_bank_nonblank CHECK(btrim(concept_key)<>'' AND btrim(scenario)<>''),
    CONSTRAINT qms_question_bank_options CHECK(jsonb_typeof(options_json)='array' AND jsonb_array_length(options_json)>=2),
    CONSTRAINT qms_question_bank_answer CHECK(jsonb_typeof(answer_key)='object' AND jsonb_typeof(answer_key->'option_ids')='array'),
    CONSTRAINT qms_question_bank_difficulty CHECK(difficulty IS NULL OR difficulty BETWEEN 1 AND 5)
  );

  CREATE TABLE qms.quiz_attempt (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL,
    learning_path_id uuid NOT NULL REFERENCES qms.learning_path(id) ON DELETE RESTRICT,
    answers jsonb NOT NULL,
    weak_concepts jsonb NOT NULL DEFAULT '[]'::jsonb,
    score numeric(5,2),
    passed boolean,
    provenance_hash char(64) NOT NULL,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    CONSTRAINT qms_quiz_attempt_user_fk FOREIGN KEY(tenant_id,user_id)
      REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_quiz_attempt_tenant_user_id_unique UNIQUE(tenant_id,user_id,id),
    CONSTRAINT qms_quiz_attempt_score CHECK(score IS NULL OR (score>=0 AND score<=100)),
    CONSTRAINT qms_quiz_attempt_provenance_hash CHECK(provenance_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT qms_quiz_attempt_completion CHECK(
      (score IS NULL AND passed IS NULL AND completed_at IS NULL) OR
      (score IS NOT NULL AND passed IS NOT NULL AND completed_at IS NOT NULL)),
    CONSTRAINT qms_quiz_attempt_json CHECK(jsonb_typeof(answers)='array' AND jsonb_typeof(weak_concepts)='array')
  );

  CREATE TABLE qms.concept_mastery (
    id uuid PRIMARY KEY,
    tenant_id uuid NOT NULL REFERENCES qms.tenant_projection(id) ON DELETE RESTRICT,
    user_id uuid NOT NULL,
    concept_key varchar(160) NOT NULL,
    score numeric(5,2),
    last_assessed_at timestamptz,
    retraining_due_at timestamptz,
    latest_attempt_id uuid NOT NULL,
    CONSTRAINT qms_concept_mastery_user_fk FOREIGN KEY(tenant_id,user_id)
      REFERENCES qms.user_projection(tenant_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_concept_mastery_attempt_fk FOREIGN KEY(tenant_id,user_id,latest_attempt_id)
      REFERENCES qms.quiz_attempt(tenant_id,user_id,id) ON DELETE RESTRICT,
    CONSTRAINT qms_concept_mastery_identity_unique UNIQUE(tenant_id,user_id,concept_key),
    CONSTRAINT qms_concept_mastery_score CHECK(score IS NULL OR (score>=0 AND score<=100)),
    CONSTRAINT qms_concept_mastery_nonblank CHECK(btrim(concept_key)<>'')
  );

  CREATE FUNCTION qms.foundation_0025_resolve_tenant_projection(external_tenant_id uuid)
  RETURNS uuid LANGUAGE sql STABLE SECURITY DEFINER
    SET search_path=pg_catalog,qms AS $fn$
    SELECT id FROM qms.tenant_projection
    WHERE adminapps_tenant_id=external_tenant_id
      AND lifecycle_status='active'
      AND provisioning_status='complete'
      AND reconciliation_status='in_sync'
  $fn$;
  REVOKE ALL ON FUNCTION qms.foundation_0025_resolve_tenant_projection(uuid) FROM PUBLIC;
  EXECUTE format('GRANT EXECUTE ON FUNCTION qms.foundation_0025_resolve_tenant_projection(uuid) TO %I',app_role);

  CREATE INDEX qms_learning_path_selection_idx ON qms.learning_path(active,edition_id,role_code,industry_code);
  CREATE INDEX qms_question_bank_path_concept_idx ON qms.question_bank(learning_path_id,concept_key);
  CREATE INDEX qms_quiz_attempt_user_history_idx ON qms.quiz_attempt(tenant_id,user_id,completed_at DESC);
  CREATE INDEX qms_concept_mastery_due_idx ON qms.concept_mastery(tenant_id,user_id,retraining_due_at);

  CREATE FUNCTION qms.foundation_0025_reject_quiz_attempt_mutation()
  RETURNS trigger LANGUAGE plpgsql SET search_path=pg_catalog,qms AS $fn$
  BEGIN
    RAISE EXCEPTION USING ERRCODE='55000',MESSAGE='Foundation Gate attempts are append-only';
  END $fn$;
  CREATE TRIGGER qms_quiz_attempt_append_only BEFORE UPDATE OR DELETE ON qms.quiz_attempt
    FOR EACH ROW EXECUTE FUNCTION qms.foundation_0025_reject_quiz_attempt_mutation();

  ALTER TABLE qms.quiz_attempt ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.quiz_attempt FORCE ROW LEVEL SECURITY;
  ALTER TABLE qms.concept_mastery ENABLE ROW LEVEL SECURITY;
  ALTER TABLE qms.concept_mastery FORCE ROW LEVEL SECURITY;
  EXECUTE format('CREATE POLICY qms_quiz_attempt_tenant ON qms.quiz_attempt FOR ALL TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);
  EXECUTE format('CREATE POLICY qms_concept_mastery_tenant ON qms.concept_mastery FOR ALL TO %I,%I USING (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid) WITH CHECK (tenant_id=NULLIF(current_setting(''app.tenant_id'',true),'''')::uuid)',app_role,worker_role);

  EXECUTE format('GRANT USAGE ON SCHEMA qms TO %I,%I,%I',app_role,worker_role,curator_role);
  EXECUTE format('GRANT SELECT ON qms.learning_path,qms.question_bank TO %I,%I',app_role,worker_role);
  EXECUTE format('GRANT SELECT,INSERT ON qms.quiz_attempt TO %I',app_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.concept_mastery TO %I',app_role);
  EXECUTE format('GRANT SELECT,INSERT,UPDATE ON qms.learning_path,qms.question_bank TO %I',curator_role);
END
$migration$;
"""


REVERSE_SQL = r"""
DROP FUNCTION qms.foundation_0025_resolve_tenant_projection(uuid);
DROP TABLE qms.concept_mastery;
DROP TABLE qms.quiz_attempt;
DROP TABLE qms.question_bank;
DROP TABLE qms.learning_path;
DROP FUNCTION qms.foundation_0025_reject_quiz_attempt_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0024_adminapps_ingress_receipt")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.CreateModel(
                    name="LearningPath",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("role_code", models.CharField(blank=True, max_length=80, null=True)),
                        ("industry_code", models.CharField(blank=True, max_length=80, null=True)),
                        ("required_score", models.DecimalField(decimal_places=2, default=80, max_digits=5)),
                        ("active", models.BooleanField(default=True)),
                        ("critical_concepts", models.JSONField(default=list)),
                        ("standard_edition", models.ForeignKey(db_column="edition_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.standardedition")),
                    ],
                    options={"db_table": 'qms"."learning_path', "managed": False},
                ),
                migrations.CreateModel(
                    name="QuestionBank",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("concept_key", models.CharField(max_length=160)),
                        ("industry_code", models.CharField(blank=True, max_length=80, null=True)),
                        ("difficulty", models.PositiveSmallIntegerField(blank=True, null=True)),
                        ("scenario", models.TextField()),
                        ("options_json", models.JSONField()),
                        ("answer_key", models.JSONField()),
                        ("explanation", models.TextField(blank=True, null=True)),
                        ("critical", models.BooleanField(default=False)),
                        ("learning_path", models.ForeignKey(db_column="learning_path_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.learningpath")),
                    ],
                    options={"db_table": 'qms"."question_bank', "managed": False},
                ),
                migrations.CreateModel(
                    name="QuizAttempt",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("answers", models.JSONField(default=list)),
                        ("weak_concepts", models.JSONField(default=list)),
                        ("score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                        ("passed", models.BooleanField(blank=True, null=True)),
                        ("provenance_hash", models.CharField(max_length=64)),
                        ("started_at", models.DateTimeField()),
                        ("completed_at", models.DateTimeField(blank=True, null=True)),
                        ("learning_path", models.ForeignKey(db_column="learning_path_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.learningpath")),
                        ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                        ("user", models.ForeignKey(db_column="user_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.userprojection")),
                    ],
                    options={"db_table": 'qms"."quiz_attempt', "managed": False},
                ),
                migrations.CreateModel(
                    name="ConceptMastery",
                    fields=[
                        ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                        ("concept_key", models.CharField(max_length=160)),
                        ("score", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                        ("last_assessed_at", models.DateTimeField(blank=True, null=True)),
                        ("retraining_due_at", models.DateTimeField(blank=True, null=True)),
                        ("latest_attempt", models.ForeignKey(db_column="latest_attempt_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.quizattempt")),
                        ("tenant", models.ForeignKey(db_column="tenant_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.tenantprojection")),
                        ("user", models.ForeignKey(db_column="user_id", on_delete=django.db.models.deletion.PROTECT, to="foundation.userprojection")),
                    ],
                    options={"db_table": 'qms"."concept_mastery', "managed": False},
                ),
            ],
        )
    ]