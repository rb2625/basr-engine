# BASR 2.0 (بصيرة)

Multilingual economic intelligence for the UAE. BASR continuously ingests what
people say about the UAE across Reddit, news, YouTube, app reviews, and live
feeds - in Arabic, Arabizi, and English - classifies the signals, detects
emerging issues before they blow up, and produces decision-ready briefings and
scheduled reports. A live public dashboard (dashboard-gamma-roan-31.vercel.app)
is the users layer and the proof of quality; org-facing intelligence is the
product. Full plan: `PLAN.md`.

## Pipeline (one command, twice a day)

```
python -m basr.orchestrator            # ingest all sources (idempotent)
python -m basr.orchestrator --nlp      # + classify + enrich (LLM budget-aware)
python -m basr.orchestrator --intel    # + time series + anomaly + alerts
python -m basr.orchestrator --agents   # + daily/weekly reports + delivery
```

The GitHub cron runs `python -m basr.orchestrator --intel --agents` at 03:00
and 15:00 UTC. Every stage degrades gracefully: one failed source, a missing
table, or an exhausted token budget never kills the platform.

## Architecture (short)

```
ADAPTERS (Reddit Arctic, 11 news feeds, YouTube, Apple reviews, Bluesky)
  -> raw_docs (deduped, hashed authors)
  -> NLP: normalizer (Arabizi->Arabic) + language ID + lexicon fast path
     + LLM classifier (openai/gpt-oss-120b) + topics + entity geocoding
  -> time_series (hourly/daily, global/topic/sector/emirate)
  -> anomalies (rolling z-score + STL) -> alerts -> Telegram/email
  -> agents: severity + briefs + scheduled reports (UAE Pulse, weekly digest)
  -> eval harness: every model scored on labeled sets, scores logged
```

Full detail: `docs/architecture.md`. Data sources: `docs/data-sources.md`.

## Commands

| What | Command |
|---|---|
| Ingest everything | `python -m basr.orchestrator` |
| Early warning (aggregate + detect + deliver) | `python -m basr.intel` |
| Build a brief for alert 10 | `python -m basr.agents --brief 10 --publish` |
| Build + deliver the daily report | `python -m basr.agents --report daily --deliver` |
| Eval the classifier (LLM, budget-aware) | `python -m basr.eval --path hybrid` |
| Eval the agents (severity + brief) | `python -m basr.eval --agents` |
| Run the unit tests | `python -m pytest tests/ -q` |
| Close Phase 2 after a budget reset | `python scripts/close_phase_2.py` |

Set `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GROQ_API_KEY`,
`YOUTUBE_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` in `.env` (or as
GitHub secrets for the cron). Re-run `basr/schema.sql` in the Supabase SQL
editor after any schema amendment.

## The daily token budget (read this)

The Groq free tier caps `openai/gpt-oss-120b` at ~200k tokens/day on a
ROLLING window - it frees gradually as usage ages out, not at midnight.
Everything that matters is designed around this:

- the lexicon fast path classifies the clear-cut majority for zero tokens;
- the classifier stops honestly on the first 429 and leaves docs for retry;
- the eval NEVER logs an incomplete run (the scorecard is always a fully
  measured run - see `scripts/watch_phase_2.sh` and `docs/runbook.md`).

## Repo layout

- `basr/orchestrator.py` - pipeline entry (ingestion + optional stages)
- `basr/adapters/` - one contract per source, graceful failures
- `basr/nlp/` - normalizer, langid, lexicon, classifier, topics, entities
- `basr/intel/` - time series, anomaly ensemble, alerts
- `basr/agents/` - severity, briefs, scheduled reports
- `basr/eval/` - harness + scored sets + benchmark tool
- `basr/schema.sql` - full schema (idempotent; re-run in the SQL editor)
- `dashboard/` - Next.js public dashboard (deployed to Vercel)
- `legacy/` - the frozen v1 pipeline (LinkedIn/Playwright era)
- `docs/` - architecture, runbook, data sources
- `tests/` - pytest suite (zero-token layers, runs in CI)
