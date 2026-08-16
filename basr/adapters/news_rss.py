"""UAE news via RSS feeds, refactored from v1 onto the adapter contract.

Covers UAE business/economy via Google News topic queries plus direct publisher
feeds (Khaleej Times, Gulf News, The National, WAM). News feeds do not rate-limit
like Reddit, so they are fetched concurrently.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from .base import RawDoc, SourceAdapter
from .feed_common import parse_feed
from ..config import NEWS_FEEDS


class NewsRSSAdapter(SourceAdapter):
    name = "news_rss"

    def __init__(
        self,
        feeds: list[tuple[str, str]] | None = None,
        *,
        per_feed_limit: int = 30,
        timeout: float = 30.0,
        max_retries: int = 3,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(timeout=timeout, max_retries=max_retries, user_agent=user_agent)
        self.feeds = feeds or NEWS_FEEDS
        self.per_feed_limit = per_feed_limit

    async def _fetch_one(self, name: str, url: str) -> list[RawDoc]:
        try:
            resp = await self.get_with_retry(url)
            docs = parse_feed(resp.content, self.name, name, self.per_feed_limit)
            print(f"    [+] news_rss {name}: {len(docs)} items")
            return docs
        except Exception as exc:
            print(f"    [-] news_rss {name}: {exc.__class__.__name__}: {str(exc)[:80]}")
            return []

    async def fetch(self, since: datetime | None = None, limit: int = 100) -> list[RawDoc]:
        docs: list[RawDoc] = []
        try:
            results = await asyncio.gather(
                *(self._fetch_one(name, url) for name, url in self.feeds),
                return_exceptions=False,
            )
            for batch in results:
                docs.extend(batch)
                if len(docs) >= limit:
                    break
        finally:
            await self.close()
        return docs[:limit]


# ----------------------------------------------------------------------
# Standalone smoke test:  python -m basr.adapters.news_rss
# ----------------------------------------------------------------------
async def _smoke_test() -> None:
    feeds = NEWS_FEEDS[:3]  # keep the test light
    adapter = NewsRSSAdapter(feeds=feeds)
    docs = await adapter.fetch(limit=10)
    print(f"[+] Collected {len(docs)} docs")
    for d in docs[:3]:
        print(f"  - {(d.title or '')[:60]!r}")


if __name__ == "__main__":
    asyncio.run(_smoke_test())
