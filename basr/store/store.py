"""Supabase persistence for the BASR pipeline.

Design (matches schema.sql):

- ``raw_docs`` has ``UNIQUE (source, external_id)``; we upsert with
  ``ignore_duplicates=True`` so re-runs are idempotent at the database level.
- Rows are written in batches (default 100) to stay well under PostgREST's
  payload limits, with retry/backoff on transient network / 5xx / 429 errors.
- ``pipeline_runs`` logs every run (status, per-source counts, inserted/skipped,
  failures). If that table is missing (schema not re-run yet), logging degrades
  gracefully - the pipeline never dies because the run log is unavailable.
"""

from __future__ import annotations

import asyncio
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

import httpx

from ..adapters.base import RawDoc
from ..config import get_settings

try:
    from supabase import create_async_client
except ImportError:  # pragma: no cover - dependency is in requirements.txt
    create_async_client = None

try:
    from postgrest.exceptions import APIError as PostgrestAPIError
except ImportError:  # pragma: no cover
    PostgrestAPIError = Exception

BATCH_SIZE = 100
MAX_ATTEMPTS = 4
BASE_DELAY_S = 1.5


@dataclass
class UpsertCounts:
    """Result of a store write: how many rows were actually new vs duplicates."""

    attempted: int = 0
    inserted: int = 0
    skipped: int = 0
    batches: int = 0

    @property
    def ok(self) -> bool:
        return self.batches > 0


def _is_retryable(exc: Exception) -> bool:
    """Transient failures are retried; permanent ones (bad data, auth) are not."""
    if isinstance(exc, (httpx.TransportError, httpx.TimeoutException)):
        return True
    # postgrest APIError and httpx HTTPStatusError both carry a status code.
    status = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(exc, "status", None)
    if isinstance(status, int) and (status >= 500 or status == 429):
        return True
    return False


def _to_row(doc: RawDoc) -> dict[str, Any]:
    """Map a RawDoc onto the raw_docs columns (see schema.sql)."""
    text = (doc.text or "").strip()
    title = (doc.title or "").strip() or None
    return {
        "source": doc.source,
        "external_id": doc.external_id,
        "url": doc.url or "",
        "title": title,
        "text": text[:20000],
        "author_hash": doc.author_hash,
        "published_at": doc.published_at.isoformat() if doc.published_at else None,
        "fetched_at": doc.fetched_at.isoformat(),
        "lang": doc.lang,
        "location_hint": doc.location_hint,
        "media_links": list(doc.media_links),
        "meta": dict(doc.meta),
    }


class SupabaseStore:
    """Async Supabase client wrapper with batching, retry, and run logging."""

    def __init__(
        self,
        url: str | None = None,
        service_role_key: str | None = None,
        *,
        batch_size: int = BATCH_SIZE,
        max_attempts: int = MAX_ATTEMPTS,
        base_delay_s: float = BASE_DELAY_S,
    ) -> None:
        settings = get_settings()
        self.url = url or settings.supabase_url
        self.service_role_key = service_role_key or settings.supabase_service_role_key
        self.batch_size = batch_size
        self.max_attempts = max_attempts
        self.base_delay_s = base_delay_s
        self._client = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def open(self) -> "SupabaseStore":
        if self._client is not None:
            return self
        if not self.url or not self.service_role_key:
            raise RuntimeError(
                "SupabaseStore: missing SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY in .env"
            )
        if create_async_client is None:
            raise RuntimeError("SupabaseStore: supabase package not installed")
        self._client = await create_async_client(self.url, self.service_role_key)
        return self

    async def close(self) -> None:
        """Release the client. Defensive across supabase-py versions: some
        versions expose ``aclose``, others ``close``, some neither (the async
        client closes its lazy httpx clients on GC). Never raises."""
        if self._client is not None:
            try:
                closer = getattr(self._client, "aclose", None) or getattr(
                    self._client, "close", None
                )
                if closer is not None:
                    result = closer()
                    if asyncio.iscoroutine(result):
                        await result
            finally:
                self._client = None

    async def __aenter__(self) -> "SupabaseStore":
        return await self.open()

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Raw docs
    # ------------------------------------------------------------------

    async def upsert_raw_docs(self, docs: list[RawDoc]) -> UpsertCounts:
        """Idempotently write RawDocs to raw_docs.

        Dedupes in-memory by ``(source, external_id)`` first, then upserts in
        batches with ``ignore_duplicates=True`` so the unique constraint absorbs
        any stragglers. Returns counts; raises only on non-transient errors.
        """
        counts = UpsertCounts()
        if not docs:
            return counts

        # In-run dedupe: same source+id collected twice must only hit the DB once.
        unique: dict[str, RawDoc] = {}
        for doc in docs:
            key = doc.dedupe_key()
            if key not in unique:
                unique[key] = doc
        rows = [r for d in unique.values() if (r := _to_row(d))["text"]]

        counts.attempted = len(rows)
        if not rows:
            return counts

        for start in range(0, len(rows), self.batch_size):
            batch = rows[start : start + self.batch_size]
            resp = await self._with_retry(
                lambda b=batch: self._client.table("raw_docs")
                .upsert(b, ignore_duplicates=True, on_conflict="source,external_id")
                .execute()
            )
            counts.batches += 1
            inserted = len(resp.data or [])
            counts.inserted += inserted
            counts.skipped += len(batch) - inserted

        return counts

    # ------------------------------------------------------------------
    # NLP outputs (Phase 2)
    # ------------------------------------------------------------------

    async def fetch_unclassified_docs(self, limit: int = 100) -> list[dict]:
        """Return raw_docs that have no classification yet (id, text, title).

        Two PostgREST queries: the classified ids first, then the unclassified
        rows via ``id=not.in.(...)``. Returns [] when everything is classified.
        """
        if self._client is None:
            return []
        classified = await self._with_retry(
            lambda: self._client.table("classifications")
            .select("raw_doc_id")
            .limit(100000)
            .execute()
        )
        done = {r["raw_doc_id"] for r in (classified.data or [])}

        query = self._client.table("raw_docs").select("id,text,title")
        if done:
            query = query.not_.in_("id", sorted(done))
        resp = await self._with_retry(
            lambda: query.order("published_at", desc=True).limit(limit).execute()
        )
        return resp.data or []

    async def upsert_nlp_rows(
        self,
        normalized_rows: list[dict],
        classification_rows: list[dict],
        lang_pairs: list[tuple[int, str]],
    ) -> tuple[int, int]:
        """Write normalized_docs + classifications (batched, idempotent) and
        backfill raw_docs.lang. Returns (normalized_written, classifications_written)."""
        n_written = c_written = 0
        if self._client is None:
            return 0, 0

        if normalized_rows:
            for start in range(0, len(normalized_rows), self.batch_size):
                batch = normalized_rows[start : start + self.batch_size]
                resp = await self._upsert_any(
                    "normalized_docs", batch, on_conflict="raw_doc_id"
                )
                n_written += len(resp.data or [])

        if classification_rows:
            for start in range(0, len(classification_rows), self.batch_size):
                batch = classification_rows[start : start + self.batch_size]
                resp = await self._upsert_any(
                    "classifications", batch, on_conflict="raw_doc_id"
                )
                c_written += len(resp.data or [])

        for doc_id, lang in lang_pairs:
            if not lang:
                continue
            await self._with_retry(
                lambda d=doc_id, l=lang: self._client.table("raw_docs")
                .update({"lang": l})
                .eq("id", d)
                .execute()
            )
        return n_written, c_written

    # ------------------------------------------------------------------
    # Run log
    # ------------------------------------------------------------------

    async def log_run(
        self,
        *,
        status: str,
        source_counts: dict[str, int],
        inserted: int,
        skipped: int,
        failures: list[str],
        error: str | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> bool:
        """Record a pipeline run in ``pipeline_runs``.

        Returns True on success, False when the table is missing or the log
        write fails - callers must never treat run logging as fatal.
        """
        if self._client is None:
            return False
        now = datetime.now(timezone.utc)
        row = {
            "started_at": (started_at or now).isoformat(),
            "finished_at": (finished_at or now).isoformat(),
            "status": status,
            "source_counts": dict(source_counts),
            "inserted": inserted,
            "skipped": skipped,
            "failures": list(failures),
            "error": error,
        }
        try:
            await self._client.table("pipeline_runs").insert(row).execute()
            return True
        except Exception as exc:
            print(f"    [-] run log unavailable (table missing?): {str(exc)[:120]}")
            return False

    # ------------------------------------------------------------------
    # Eval
    # ------------------------------------------------------------------

    async def upsert_eval_dataset(self, name: str, lang: str, task: str, items: list) -> bool:
        """Insert or replace an eval dataset (idempotent on name)."""
        if self._client is None:
            return False
        try:
            await self._with_retry(
                lambda: self._client.table("eval_datasets")
                .upsert(
                    {"name": name, "lang": lang, "task": task, "items": items},
                    on_conflict="name",
                )
                .execute()
            )
            return True
        except Exception as exc:
            print(f"    [-] eval dataset write failed: {str(exc)[:120]}")
            return False

    async def log_eval_run(
        self,
        *,
        dataset_name: str,
        model_version: str,
        accuracy: float,
        precision: float,
        recall: float,
        f1: float,
        detail: dict,
    ) -> bool:
        """Record one eval run in eval_runs (graceful on failure)."""
        if self._client is None:
            return False
        try:
            ds = await self._with_retry(
                lambda: self._client.table("eval_datasets")
                .select("id")
                .eq("name", dataset_name)
                .limit(1)
                .execute()
            )
            if not (ds.data or []):
                return False
            await self._with_retry(
                lambda: self._client.table("eval_runs")
                .insert(
                    {
                        "dataset_id": ds.data[0]["id"],
                        "model_version": model_version,
                        "accuracy": round(accuracy, 4),
                        "precision": round(precision, 4),
                        "recall": round(recall, 4),
                        "f1": round(f1, 4),
                        "detail": detail,
                    }
                )
                .execute()
            )
            return True
        except Exception as exc:
            print(f"    [-] eval run write failed: {str(exc)[:120]}")
            return False

    async def _upsert_any(
        self, table: str, rows: list[dict], *, on_conflict: str
    ) -> Any:
        """Upsert with on_conflict, degrading to a plain insert when the
        table lacks the unique constraint (schema.sql not re-run yet, e.g.
        classifications before Amendment A6 lands). A plain insert is safe for
        the single-process cron because fetch_unclassified_docs already filters
        classified docs - the DB constraint removes the race entirely once the
        schema is re-applied. Never retries 42P10 (permanent, not transient)."""
        try:
            return await self._with_retry(
                lambda: self._client.table(table)
                .upsert(rows, ignore_duplicates=True, on_conflict=on_conflict)
                .execute()
            )
        except PostgrestAPIError as exc:
            if getattr(exc, "code", "") != "42P10":
                raise
            print(f"    [-] {table}: no UNIQUE({on_conflict}) constraint - "
                  f"degrading to plain insert (re-run schema.sql for the "
                  f"permanent dedupe guarantee)")
            return await self._with_retry(
                lambda: self._client.table(table).insert(rows).execute()
            )

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    async def _with_retry(
        self, call: Callable[[], Coroutine[Any, Any, Any]]
    ) -> Any:
        """Run ``call`` with exponential backoff + jitter on transient failures."""
        # A no-op client guard: some methods below call _with_retry directly.
        if self._client is None:
            raise RuntimeError("SupabaseStore: store is not open")
        attempt = 0
        while True:
            try:
                return await call()
            except Exception as exc:
                if not _is_retryable(exc) or attempt >= self.max_attempts:
                    raise
                attempt += 1
                delay = self.base_delay_s * (2 ** (attempt - 1)) * (0.5 + random.random())
                print(
                    f"    [retry] store: {exc.__class__.__name__}, "
                    f"attempt {attempt}/{self.max_attempts} in {delay:.1f}s"
                )
                await asyncio.sleep(delay)


# ----------------------------------------------------------------------
# Standalone smoke test:  python -m basr.store.store
# ----------------------------------------------------------------------
async def _smoke_test() -> None:
    from ..adapters.base import hash_author

    docs = [
        RawDoc(
            source="smoke_test",
            external_id="1",
            text="hello basr",
            title="t",
            author_hash=hash_author("someone"),
            published_at=datetime.now(timezone.utc),
        ),
        RawDoc(source="smoke_test", external_id="1", text="duplicate - must be skipped"),
    ]
    async with SupabaseStore() as store:
        counts = await store.upsert_raw_docs(docs)
        print(f"[+] upsert: attempted={counts.attempted} inserted={counts.inserted} "
              f"skipped={counts.skipped} batches={counts.batches}")
        ok = await store.log_run(
            status="smoke_test",
            source_counts={"smoke_test": 1},
            inserted=counts.inserted,
            skipped=counts.skipped,
            failures=[],
        )
        print(f"[+] run log written: {ok}")


if __name__ == "__main__":
    asyncio.run(_smoke_test())
