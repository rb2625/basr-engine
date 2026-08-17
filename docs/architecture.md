# BASR architecture

The locked product spec is PLAN.md sec 3; this doc maps it to the code that
implements it today.

## Data flow

```
ADAPTERS (basr/adapters/)                 STORE (Supabase, basr/schema.sql)
  reddit_arctic (posts + comments)   ->   raw_docs (immutable, deduped,
  news (11 feeds + Google News)            hashed authors)
  youtube_comments                    ->   normalized_docs
  apple_reviews                       ->   classifications (sentiment, signal
  bluesky_firehose (live)                   taxonomy, confidence, model_version)
                                           topics / doc_topics (14 topics)
        |                                 entities / doc_entities (gazetteer)
        v
NLP PIPELINE (basr/nlp/)               INTELLIGENCE (basr/intel/)
  normalizer: clean_text + arabizi->   time_series (hourly + daily,
    arabic (digit letters)                global/topic/sector/emirate)
  language ID (heuristic; fasttext     anomaly ensemble: trailing z-score
    when present)                         + statsmodels STL, volume floor,
  lexicon fast path (zero tokens,         severity tiers
    defers ambiguous cases)            alerts: lifecycle + Telegram/email
  LLM classifier (gpt-oss-120b,           delivery, evidence attached
    budget-aware, stops on 429)
  topics: keyword rules (14 topics)    AGENTS (basr/agents/)
  entities: UAE gazetteer + geocoding    severity: impact x urgency x spread
                                           (deterministic, anomaly floor)
        |                                briefs: what/where/who + trajectory
        v                                  + evidence + responses (LLM w/
DELIVERY                                   deterministic fallback)
  dashboard (Next.js, Vercel)          reports: UAE Pulse daily + weekly
  alerts/reports over Telegram/email     sector digest (LLM w/ fallback)

EVAL HARNESS (basr/eval/) - every model scored on labeled sets
  sentiment + signal: 500 items each (datasets.py), lexicon path is free,
  LLM/hybrid paths are single-pass and budget-aware. eval_runs holds only
  fully-measured runs (incomplete runs are never logged).
  agents: severity agreement (15 cases, zero tokens) + brief format and
  grounding (4 cases, small LLM budget). Both logged to eval_runs.
```

## Key invariants (working rules)

1. Every stage degrades gracefully: no single failure kills the platform.
2. Nothing is published as "measured" unless the eval measured it: eval_runs
   only ever records complete runs.
3. The free-tier token budget is a rolling window: the lexicon does the bulk,
   the LLM handles the ambiguous remainder, and the classifier stops honestly
   at the wall (docs left unclassified for the next run).
4. Plain ASCII everywhere except Arabic content (data, not punctuation).

## Stage entry points

- Orchestrator: `basr/orchestrator.py` (`--nlp`, `--intel`, `--agents`)
- NLP: `python -m basr.nlp` (classify + enrich; `--enrich-only` is free)
- Intel: `python -m basr.intel` (`--aggregate`, `--detect`, `--deliver`)
- Agents: `python -m basr.agents` (`--brief`, `--report`, `--deliver`)
- Eval: `python -m basr.eval` (`--path lexicon|hybrid|llm`, `--agents`)
- Dashboard API: `dashboard/app/api/data/route.ts` (view=overview|map|trends|
  topics|feed|alerts|briefs|reports); server-side service-role key only.
