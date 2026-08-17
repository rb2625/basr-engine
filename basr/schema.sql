-- ============================================================================
-- BASR 2.0 - Schema migration
-- Run in the Supabase SQL editor (or via `supabase db push`). Idempotent.
--
-- Design principles:
--   * raw data is immutable and source-traceable (raw_docs)
--   * every derived layer references raw_docs (classifications, topics, entities)
--   * time-series is pre-aggregated for fast dashboards (time_series)
--   * org data is RLS-isolated; public dashboards read through views
-- ============================================================================

-- PostGIS for geo queries on entities (enabled in Supabase by default).
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- 1. RAW INGESTION
-- ============================================================================

CREATE TABLE IF NOT EXISTS raw_docs (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source         TEXT NOT NULL,                    -- adapter name, e.g. 'reddit_arctic'
    external_id    TEXT NOT NULL,                    -- id as given by the source
    url            TEXT NOT NULL DEFAULT '',
    title          TEXT,
    text           TEXT NOT NULL,                    -- body / comment / description
    author_hash    TEXT,                             -- sha256 prefix, never a raw username
    published_at   TIMESTAMPTZ,
    fetched_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    lang           TEXT,                             -- 'ar' | 'arz' | 'en' | 'mixed' (NLP layer)
    location_hint  TEXT,                             -- free-text place name if source provides one
    media_links    JSONB NOT NULL DEFAULT '[]'::jsonb,
    meta           JSONB NOT NULL DEFAULT '{}'::jsonb,  -- source-specific extras
    UNIQUE (source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_docs_published_at ON raw_docs (published_at DESC);
CREATE INDEX IF NOT EXISTS idx_raw_docs_source ON raw_docs (source);
CREATE INDEX IF NOT EXISTS idx_raw_docs_author ON raw_docs (author_hash);
CREATE INDEX IF NOT EXISTS idx_raw_docs_lang ON raw_docs (lang);

-- Enrichment marker (Amendment A8): set once a doc's topics/entities pass has
-- run, so docs with zero topics are not refetched every backfill. Idempotent.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'raw_docs' AND column_name = 'enriched_at'
    ) THEN
        ALTER TABLE raw_docs ADD COLUMN enriched_at TIMESTAMPTZ;
    END IF;
END
$$;

CREATE INDEX IF NOT EXISTS idx_raw_docs_enriched ON raw_docs (enriched_at) WHERE enriched_at IS NULL;

-- ============================================================================
-- 2. NLP OUTPUTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS normalized_docs (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    raw_doc_id  BIGINT NOT NULL REFERENCES raw_docs(id) ON DELETE CASCADE,
    clean_text  TEXT NOT NULL,
    lang        TEXT,
    dialect     TEXT,             -- 'gulf' | 'egyptian' | 'levantine' | 'msa' ...
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (raw_doc_id)
);

CREATE TABLE IF NOT EXISTS classifications (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    raw_doc_id      BIGINT NOT NULL REFERENCES raw_docs(id) ON DELETE CASCADE,
    -- sentiment
    sentiment_score NUMERIC(4,3),          -- -1.0 .. 1.0
    sentiment_label TEXT,                  -- 'positive' | 'negative' | 'neutral' | 'mixed'
    emotion         TEXT,                  -- e.g. 'anger' | 'joy' | 'fear' | 'trust' ...
    sarcasm         BOOLEAN,
    -- economic signal taxonomy (BASR v1 lineage)
    signal_type     TEXT,                  -- 'stress' | 'closure' | 'opportunity' | 'neutral'
    sector          TEXT,                  -- 'F&B' | 'Real Estate' | 'Tech' | ...
    intensity_score SMALLINT CHECK (intensity_score BETWEEN 1 AND 5),
    confidence      NUMERIC(4,3),
    -- provenance
    model_version   TEXT NOT NULL,         -- 'groq-llama-3.3-70b-v1' | 'camembert-ar-sent-v1' ...
    raw             JSONB NOT NULL DEFAULT '{}'::jsonb,  -- full model output for audit
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_classifications_doc ON classifications (raw_doc_id);
CREATE INDEX IF NOT EXISTS idx_classifications_signal ON classifications (signal_type, intensity_score);
CREATE INDEX IF NOT EXISTS idx_classifications_sentiment ON classifications (sentiment_label);

-- One classification per document (idempotent re-runs; Amendment A6 - this
-- constraint was missing in the initial migration, so retried upserts could
-- multiply rows. The DO block keeps the file re-runnable).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'classifications_doc_unique'
    ) THEN
        ALTER TABLE classifications
            ADD CONSTRAINT classifications_doc_unique UNIQUE (raw_doc_id);
    END IF;
END
$$;

-- ----------------------------------------------------------------------------
-- Topics
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS topics (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    key         TEXT NOT NULL UNIQUE,   -- stable slug, e.g. 'rent-increases'
    label_en    TEXT NOT NULL,
    label_ar    TEXT,
    description TEXT
);

CREATE TABLE IF NOT EXISTS doc_topics (
    doc_id      BIGINT NOT NULL REFERENCES raw_docs(id) ON DELETE CASCADE,
    topic_id    BIGINT NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    score       NUMERIC(5,4) NOT NULL DEFAULT 0,
    PRIMARY KEY (doc_id, topic_id)
);

-- ----------------------------------------------------------------------------
-- Entities (locations, authorities, universities, brands, sectors)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS entities (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,          -- 'location' | 'authority' | 'university' | 'brand' | 'sector'
    normalized  TEXT NOT NULL,          -- canonical spelling
    lat         DOUBLE PRECISION,
    lng         DOUBLE PRECISION,
    metadata    JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (type, normalized)
);

CREATE INDEX IF NOT EXISTS idx_entities_geo ON entities USING gist (
    ST_SetSRID(ST_MakePoint(lng, lat), 4326)
) WHERE lat IS NOT NULL AND lng IS NOT NULL;

CREATE TABLE IF NOT EXISTS doc_entities (
    doc_id      BIGINT NOT NULL REFERENCES raw_docs(id) ON DELETE CASCADE,
    entity_id   BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    role        TEXT,                  -- 'subject' | 'mentioned' | 'location_of'
    PRIMARY KEY (doc_id, entity_id)
);

-- ============================================================================
-- 3. TIME SERIES + EARLY WARNING
-- ============================================================================

CREATE TABLE IF NOT EXISTS time_series (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    bucket_start    TIMESTAMPTZ NOT NULL,
    bucket_end      TIMESTAMPTZ NOT NULL,
    granularity     TEXT NOT NULL,          -- 'hour' | 'day'
    dimension_type  TEXT NOT NULL,          -- 'entity' | 'topic' | 'sector' | 'emirate' | 'global'
    dimension_id    BIGINT NOT NULL DEFAULT 0,  -- entities.id / topics.id / 0 = global
                                    -- (0 sentinel, NOT NULL: Postgres UNIQUE
                                    -- treats NULLs as distinct, so NULL would
                                    -- never dedupe global rows on upsert)
    volume          INTEGER NOT NULL DEFAULT 0,
    sentiment_avg   NUMERIC(6,4),
    sentiment_std   NUMERIC(6,4),
    anomaly_score   NUMERIC(8,5),           -- z-score / ensemble deviation
    anomaly_flag    BOOLEAN NOT NULL DEFAULT FALSE,
    UNIQUE (bucket_start, granularity, dimension_type, dimension_id)
);

CREATE INDEX IF NOT EXISTS idx_time_series_dim ON time_series (dimension_type, dimension_id, bucket_start DESC);
CREATE INDEX IF NOT EXISTS idx_time_series_anomaly ON time_series (anomaly_flag, bucket_start DESC);

CREATE TABLE IF NOT EXISTS alerts (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    time_series_id  BIGINT REFERENCES time_series(id) ON DELETE SET NULL,
    title           TEXT NOT NULL,
    severity        TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status          TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'dismissed', 'promoted')),
    evidence        JSONB NOT NULL DEFAULT '[]'::jsonb,   -- top raw_doc ids + snippets
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at     TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts (status, created_at DESC);

-- Delivery tracking (Phase 4, Amendment A11): which channel an alert was
-- sent on and whether delivery succeeded. Idempotent for re-runs.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'alerts' AND column_name = 'channel'
    ) THEN
        ALTER TABLE alerts
            ADD COLUMN channel TEXT,
            ADD COLUMN delivery_status TEXT NOT NULL DEFAULT 'pending'
                CHECK (delivery_status IN ('pending', 'sent', 'failed', 'skipped')),
            ADD COLUMN delivered_at TIMESTAMPTZ;
    END IF;
END
$$;

-- ============================================================================
-- 4. DECISION SUPPORT (AGENTS)
-- ============================================================================

CREATE TABLE IF NOT EXISTS briefs (
    id                      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    alert_id                BIGINT REFERENCES alerts(id) ON DELETE SET NULL,
    org_id                  BIGINT,                      -- orgs.id (nullable = public briefs)
    title                   TEXT NOT NULL,
    summary                 TEXT NOT NULL,
    severity                TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    recommended_response    JSONB NOT NULL DEFAULT '[]'::jsonb,  -- ordered action options
    evidence                JSONB NOT NULL DEFAULT '[]'::jsonb,
    status                  TEXT NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft', 'published', 'delivered', 'archived')),
    model_version           TEXT NOT NULL,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_briefs_org ON briefs (org_id, created_at DESC);

-- ============================================================================
-- 5. MONETIZATION / ORGS
-- ============================================================================

CREATE TABLE IF NOT EXISTS orgs (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL,
    contact_email TEXT NOT NULL,
    plan        TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS org_trackers (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    org_id          BIGINT NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    entity_id       BIGINT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    alert_threshold TEXT NOT NULL DEFAULT 'medium',
    UNIQUE (org_id, entity_id)
);

CREATE TABLE IF NOT EXISTS org_subscriptions (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    org_id          BIGINT NOT NULL REFERENCES orgs(id) ON DELETE CASCADE,
    plan            TEXT NOT NULL,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    status          TEXT NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 6. EVALUATION (the platform's own scorecard)
-- ============================================================================

CREATE TABLE IF NOT EXISTS eval_datasets (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        TEXT NOT NULL UNIQUE,     -- e.g. 'arabizi-sentiment-v1'
    lang        TEXT NOT NULL,
    task        TEXT NOT NULL,            -- 'sentiment' | 'signal_type' | 'topic'
    items       JSONB NOT NULL,           -- [{text, label, note?}]
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS eval_runs (
    id              BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dataset_id      BIGINT NOT NULL REFERENCES eval_datasets(id) ON DELETE CASCADE,
    model_version   TEXT NOT NULL,
    accuracy        NUMERIC(5,4),
    precision       NUMERIC(5,4),
    recall          NUMERIC(5,4),
    f1              NUMERIC(5,4),
    detail          JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================================
-- 6b. PIPELINE RUNS (operational log - Phase 1 DoD: "cron produces a run log")
-- ============================================================================

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at   TIMESTAMPTZ,
    status        TEXT NOT NULL DEFAULT 'running'
                  CHECK (status IN ('running', 'success', 'partial', 'failed', 'dry_run')),
    source_counts JSONB NOT NULL DEFAULT '{}'::jsonb,   -- {source: docs_fetched}
    inserted      INTEGER NOT NULL DEFAULT 0,
    skipped       INTEGER NOT NULL DEFAULT 0,
    failures      JSONB NOT NULL DEFAULT '[]'::jsonb,   -- [{source: reason}]
    error         TEXT,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started ON pipeline_runs (started_at DESC);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs (status, started_at DESC);

-- ============================================================================
-- 7. TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 8. ROW LEVEL SECURITY
--    Public tables (raw_docs, classifications, ...) are service-role only for
--    writes; the dashboard reads through narrow views we add in a later migration.
--    Org-scoped tables are isolated per organization.
-- ============================================================================

ALTER TABLE orgs               ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_trackers       ENABLE ROW LEVEL SECURITY;
ALTER TABLE org_subscriptions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE briefs             ENABLE ROW LEVEL SECURITY;

-- Default: only the service role can touch org data (policies are added once
-- auth is wired in the dashboard migration).
-- NOTE: `CREATE POLICY` has no IF NOT EXISTS in PostgreSQL, so each policy is
-- dropped first to keep the whole migration idempotent (safe to re-run).
DROP POLICY IF EXISTS "orgs_service_only"    ON orgs;
DROP POLICY IF EXISTS "trackers_service_only" ON org_trackers;
DROP POLICY IF EXISTS "subs_service_only"    ON org_subscriptions;
DROP POLICY IF EXISTS "briefs_service_only"  ON briefs;

CREATE POLICY "orgs_service_only"    ON orgs              FOR ALL USING (false) WITH CHECK (false);
CREATE POLICY "trackers_service_only" ON org_trackers     FOR ALL USING (false) WITH CHECK (false);
CREATE POLICY "subs_service_only"    ON org_subscriptions FOR ALL USING (false) WITH CHECK (false);
CREATE POLICY "briefs_service_only"  ON briefs            FOR ALL USING (false) WITH CHECK (false);

-- ============================================================================
-- 9. BACK-COMPAT NOTE
--    v1's `economic_signals` table is left untouched; a data migration moves
--    its rows into raw_docs + classifications once the new pipeline is live.
--    v1's `orchestrator.py` / `scraper_*.py` remain untouched until Phase 6 cleanup;
--    the new pipeline is `basr/orchestrator.py` (see PLAN.md sec 13).
-- ============================================================================
