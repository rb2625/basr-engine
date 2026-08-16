"""Adapter contract shared by every data source.

The contract is the platform's immune system: if a source breaks or disappears,
we swap its adapter and the rest of the pipeline never notices.
"""

from __future__ import annotations

import asyncio
import hashlib
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx


@dataclass
class RawDoc:
    """One normalized document emitted by any source adapter.

    Fields map 1:1 onto the ``raw_docs`` table in the schema.
    """

    source: str                      # adapter name, e.g. "reddit_pullpush"
    external_id: str                 # id as given by the source
    text: str                        # the payload (body / description / comment)
    url: str = ""                    # canonical link back to the source
    title: str | None = None
    author_hash: str | None = None   # privacy: sha256 prefix, never a raw username
    published_at: datetime | None = None
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    lang: str | None = None          # detected later in the NLP layer
    location_hint: str | None = None # free-text place name if the source provides one
    media_links: list[str] = field(default_factory=list)
    meta: dict = field(default_factory=dict)  # source-specific extras (jsonb)

    def dedupe_key(self) -> str:
        return f"{self.source}:{self.external_id}"


def hash_author(author: str | None) -> str | None:
    """Hash a username so raw identities are never persisted.

    A 16-hex-char prefix keeps ~2^64 space — enough to fingerprint an author for
    trend analysis while making de-anonymization impractical.
    """
    if not author:
        return None
    return hashlib.sha256(author.encode("utf-8")).hexdigest()[:16]


def is_removed(text: str) -> bool:
    """True if a Reddit-style placeholder is all that remains of a document."""
    return text.strip().lower() in {"[removed]", "[deleted]", ""}


class SourceAdapter(ABC):
    """Base class for all source adapters.

    Subclasses implement :meth:`fetch`; the base class provides retry/backoff
    for HTTP calls so every adapter behaves gracefully under rate limits.
    """

    name: str = "base"

    def __init__(self, timeout: float = 30.0, max_retries: int = 4, user_agent: str | None = None) -> None:
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or "BASR-Intelligence/2.0"
        self._client: httpx.AsyncClient | None = None

    async def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "application/json, application/rss+xml, application/xml, text/xml, */*",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def get_with_retry(self, url: str, *, params: dict | None = None) -> httpx.Response:
        """GET with exponential backoff + jitter on transient failures.

        Respects Retry-After when the server provides it. Raises on 4xx client
        errors other than 429 (those are permanent and retrying is pointless).
        """
        client = await self.client()
        base_delay = 1.5
        attempt = 0
        while True:
            try:
                resp = await client.get(url, params=params)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                if attempt >= self.max_retries:
                    raise
                attempt += 1
                delay = self._backoff(base_delay, attempt, retry_after=None)
                print(f"    [retry] {self.name}: network error ({exc.__class__.__name__}), "
                      f"retry {attempt}/{self.max_retries} in {delay:.1f}s")
                await asyncio.sleep(delay)
                continue

            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt >= self.max_retries:
                    raise RuntimeError(f"{self.name}: {url} failed after retries with status {resp.status_code}")
                retry_after = resp.headers.get("Retry-After")
                attempt += 1
                delay = self._backoff(base_delay, attempt, retry_after)
                print(f"    [retry] {self.name}: status {resp.status_code}, retry {attempt}/"
                      f"{self.max_retries} in {delay:.1f}s")
                await asyncio.sleep(delay)
                continue

            resp.raise_for_status()
            return resp

    @staticmethod
    def _backoff(base: float, attempt: int, retry_after: str | None) -> float:
        if retry_after:
            try:
                return min(float(retry_after), 60.0)
            except ValueError:
                pass
        # exponential backoff with jitter: base * 2^(attempt-1) * [0.5, 1.5)
        delay = base * (2 ** (attempt - 1))
        return delay * (0.5 + random.random())

    @abstractmethod
    async def fetch(self, since: datetime | None = None, limit: int = 100) -> list[RawDoc]:
        """Fetch documents newer than ``since`` (or a sensible default), up to ``limit``."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
