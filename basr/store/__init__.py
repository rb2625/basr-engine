"""Persistence layer: dedupe upserts into Supabase.

The store is the only component that talks to the database. It guarantees:

- RawDocs are deduped by ``(source, external_id)`` - re-runs never duplicate rows.
- Inserts are batched (payload size safety) with retry/backoff on transient errors.
- The ``raw_docs`` table stays immutable and source-traceable (see schema.sql).
- Every pipeline run is logged to ``pipeline_runs`` for the run log / dashboard.
"""

from .store import SupabaseStore, UpsertCounts

__all__ = ["SupabaseStore", "UpsertCounts"]
