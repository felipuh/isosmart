from django.db import migrations, models
import django.db.models.deletion
import uuid


FORWARD_SQL = r"""
ALTER TABLE qms.question_bank
  ADD COLUMN question_key uuid NOT NULL DEFAULT gen_random_uuid(),
  ADD COLUMN version integer NOT NULL DEFAULT 1,
  ADD COLUMN publication_state varchar(16) NOT NULL DEFAULT 'draft',
  ADD COLUMN effective_from timestamptz,
  ADD COLUMN effective_to timestamptz,
  ADD COLUMN provenance_hash char(64),
  ADD COLUMN published_at timestamptz,
  ADD COLUMN retired_at timestamptz;
ALTER TABLE qms.question_bank
  ADD CONSTRAINT qms_question_bank_version CHECK(version > 0),
  ADD CONSTRAINT qms_question_bank_state CHECK(publication_state IN ('draft','published','retired')),
  ADD CONSTRAINT qms_question_bank_dates CHECK(effective_to IS NULL OR effective_from IS NULL OR effective_to > effective_from),
  ADD CONSTRAINT qms_question_bank_provenance CHECK(provenance_hash IS NULL OR provenance_hash ~ '^[0-9a-f]{64}$'),
  ADD CONSTRAINT qms_question_bank_version_unique UNIQUE(learning_path_id, question_key, version);
CREATE INDEX qms_question_bank_published_idx
  ON qms.question_bank(learning_path_id, publication_state, version);
ALTER TABLE qms.quiz_attempt
  ADD COLUMN question_bank_version integer NOT NULL DEFAULT 1,
  ADD CONSTRAINT qms_quiz_attempt_bank_version CHECK(question_bank_version > 0);
"""

REVERSE_SQL = r"""
ALTER TABLE qms.quiz_attempt
  DROP CONSTRAINT qms_quiz_attempt_bank_version,
  DROP COLUMN question_bank_version;
DROP INDEX qms.question_bank_published_idx;
ALTER TABLE qms.question_bank
  DROP CONSTRAINT qms_question_bank_version_unique,
  DROP CONSTRAINT qms_question_bank_provenance,
  DROP CONSTRAINT qms_question_bank_dates,
  DROP CONSTRAINT qms_question_bank_state,
  DROP CONSTRAINT qms_question_bank_version,
  DROP COLUMN retired_at,
  DROP COLUMN published_at,
  DROP COLUMN provenance_hash,
  DROP COLUMN effective_to,
  DROP COLUMN effective_from,
  DROP COLUMN publication_state,
  DROP COLUMN version,
  DROP COLUMN question_key;
"""


class Migration(migrations.Migration):
    dependencies = [("foundation", "0025_iso9000_foundation_gate")]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(FORWARD_SQL, REVERSE_SQL)],
            state_operations=[
                migrations.AddField(
                    model_name="questionbank",
                    name="question_key",
                    field=models.UUIDField(default=uuid.uuid4, editable=False),
                ),
                migrations.AddField(
                    model_name="questionbank",
                    name="version",
                    field=models.PositiveIntegerField(default=1),
                ),
                migrations.AddField(
                    model_name="questionbank",
                    name="publication_state",
                    field=models.CharField(default="draft", max_length=16),
                ),
                migrations.AddField(
                    model_name="questionbank",
                    name="effective_from",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="questionbank",
                    name="effective_to",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="questionbank",
                    name="provenance_hash",
                    field=models.CharField(blank=True, max_length=64, null=True),
                ),
                migrations.AddField(
                    model_name="questionbank",
                    name="published_at",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="questionbank",
                    name="retired_at",
                    field=models.DateTimeField(blank=True, null=True),
                ),
                migrations.AddField(
                    model_name="quizattempt",
                    name="question_bank_version",
                    field=models.PositiveIntegerField(default=1),
                ),
            ],
        ),
    ]
