from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_init_telemetry"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("""
    CREATE TABLE IF NOT EXISTS classification (
      classification_id UUID PRIMARY KEY,
      ts_utc            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      model_version     TEXT        NOT NULL,
      embedding_model   TEXT        NOT NULL,
      threshold_used    NUMERIC(5,4) NOT NULL CHECK (threshold_used > 0 AND threshold_used <= 1),
      label             TEXT        NOT NULL CHECK (label IN ('Produtivo','Improdutivo')),
      score_produtivo   NUMERIC(5,4) NOT NULL CHECK (score_produtivo >= 0 AND score_produtivo <= 1),
      template_code     TEXT        NOT NULL CHECK (template_code IN ('status','error','access','pwd','attach','generic','ooo')),
      text_length_chars INT         NOT NULL CHECK (text_length_chars >= 0),
      latency_ms        INT         NOT NULL CHECK (latency_ms >= 0),
      language          TEXT        NOT NULL
    );
    """)
    op.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
      feedback_id       UUID PRIMARY KEY,
      ts_utc            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      classification_id UUID UNIQUE NOT NULL REFERENCES classification(classification_id),
      helpful           BOOLEAN     NOT NULL,
      reason_code       TEXT NULL
    );
    """)

def downgrade():
    op.execute("DROP TABLE IF EXISTS feedback;")
    op.execute("DROP TABLE IF EXISTS classification;")
