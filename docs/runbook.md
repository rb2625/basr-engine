# BASR runbook

Operational playbook for keeping the platform healthy.

## The daily rhythm

1. **03:00 and 15:00 UTC** the GitHub cron runs
   `python -m basr.orchestrator --intel --agents`:
   ingest -> time series -> anomaly scan -> alerts -> daily report (+ weekly
   when none exists for the week) -> delivery over Telegram/email.
   Check the last run under **Actions** on GitHub; run logs are uploaded as
   artifacts (BASR_RUN_LOG_DIR).
2. **Schema amendments** land in `basr/schema.sql` (idempotent). After any
   amendment, paste the file into the Supabase SQL editor and run it.
   Live-verify with `python -m basr.intel --dry-run` and the dashboard.
3. **The token budget** is a rolling window (~200k/day on gpt-oss-120b).
   Heavy manual jobs (the eval, backlog drains) should run when the window
   has room. `scripts/close_phase_2.py` probes and runs the eval; the
   classifier and eval stop honestly at the wall and never write garbage.

## Alert and report delivery (Telegram)

- Create a bot with BotFather, get the chat id from @userinfobot.
- Set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env` (local) and as
  GitHub secrets (cron). Email via Resend uses `RESEND_API_KEY` +
  `ALERT_EMAIL_FROM`/`ALERT_EMAIL_TO`.
- Re-deliver pending alerts/reports: reset `delivery_status` to `pending` in
  the SQL editor, then `python -m basr.intel --deliver` /
  `python -m basr.agents --deliver`.

## Common operations

| Task | Command |
|---|---|
| Full pipeline, one shot | `python -m basr.orchestrator --intel --agents` |
| Classify a batch (budget-aware) | `python -m basr.orchestrator --nlp --nlp-limit 40` |
| Zero-token enrich only | `python -m basr.nlp --enrich-only` |
| Rebuild time series + scan | `python -m basr.intel` |
| Promote an alert into a brief | `python -m basr.agents --brief <alert_id> --publish` |
| Build + deliver a report | `python -m basr.agents --report daily --deliver` |
| Eval the classifier | `python -m basr.eval --path hybrid` |
| Eval the agents | `python -m basr.eval --agents` |
| Unit tests | `python -m pytest tests/ -q` |
| Close Phase 2 (after budget frees) | `python scripts/close_phase_2.py` |
| Watch until Phase 2 lands | `nohup bash scripts/watch_phase_2.sh > /tmp/basr_phase2_watch.log 2>&1 &` |
| Dashboard build | `cd dashboard && npm run build` |
| Dashboard deploy | `cd dashboard && npx vercel --prod --yes` |

## Failure modes and their answers

- **Source fails** -> the source is skipped, others run, the run log records
  it. Check `pipeline_runs` and the Actions log.
- **Token budget exhausted** -> the classifier stops, docs stay unclassified,
  the eval exits 3 without logging. Wait for the window to free; the watcher
  retries automatically.
- **Missing table after a schema change** -> re-run `basr/schema.sql` in the
  SQL editor. The store degrades gracefully meanwhile (e.g. delivery columns
  are probed before use).
- **A bad eval row sneaks in** -> delete it from `eval_runs` (only
  fully-measured runs should ever be published).

## Privacy and compliance (Gate 6)

- Authors are hashed at ingestion (no personal identifiers in raw_docs).
- Sources are public feeds only; no login-walled scraping, no LinkedIn.
- The dashboard publishes aggregated trends, never individual accusations.
- See docs/data-sources.md for per-source terms notes.
