"""Reddit posts + comments via the keyless Arctic Shift archive API.

Why this adapter exists: Reddit's official API requires app registration that is
frequently denied, and PullPush (the older archive) now blocks programmatic
access. Arctic Shift (https://arctic-shift.photon-reddit.com) is the community
standard archive since Pushshift died: free, keyless, and it mirrors public
Reddit posts and comments in near-real-time.

Design notes:
- Fetches both posts and comments per subreddit, paginating backward in time
  with a ``before`` cursor until older than ``since`` or a page cap.
- Degrades gracefully: if Arctic Shift is down, the adapter logs and returns
  what it has; the pipeline still runs on RSS/news sources.
- Authors are hashed before they leave this module (privacy by construction).
- Verified live from a UAE residential IP (2026-08): both endpoints return data.

Endpoints:
    GET /api/posts/search?subreddit=...&limit=100&sort=desc&sort_type=created_utc
    GET /api/comments/search?...same params
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any

from .base import RawDoc, SourceAdapter, hash_author, is_removed

API_BASE = "https://arctic-shift.photon-reddit.com/api"

# endpoint name -> (path, body-or-post flag)
_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("post", "posts/search"),
    ("comment", "comments/search"),
)


class ArcticShiftRedditAdapter(SourceAdapter):
    name = "reddit_arctic"

    def __init__(
        self,
        subreddits: list[str] | None = None,
        *,
        page_size: int = 100,
        max_pages: int = 3,
        request_gap_s: float = 0.8,
        timeout: float = 30.0,
        max_retries: int = 4,
        user_agent: str | None = None,
    ) -> None:
        super().__init__(timeout=timeout, max_retries=max_retries, user_agent=user_agent)
        self.subreddits = subreddits or []
        self.page_size = min(page_size, 100)  # API hard cap is 100
        self.max_pages = max_pages
        self.request_gap_s = request_gap_s

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def fetch(self, since: datetime | None = None, limit: int = 100) -> list[RawDoc]:
        if not self.subreddits:
            return []

        since = since or (datetime.now(timezone.utc) - timedelta(hours=48))
        docs: dict[str, RawDoc] = {}
        try:
            for sub in self.subreddits:
                for kind, path in _ENDPOINTS:
                    if len(docs) >= limit:
                        break
                    await self._fetch_one_stream(
                        sub, kind, path, since, docs, remaining=limit - len(docs)
                    )
        finally:
            await self.close()

        if not docs:
            print(f"[-] {self.name}: no documents collected (archive may be down or empty)")

        return list(docs.values())

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _fetch_one_stream(
        self,
        subreddit: str,
        kind: str,
        path: str,
        since: datetime,
        docs: dict[str, RawDoc],
        remaining: int,
    ) -> None:
        """Paginate one (subreddit, endpoint) stream backward in time."""
        since_epoch = int(since.timestamp())
        before: int | None = None  # cursor: oldest item already seen on previous page
        pages_fetched = 0

        while pages_fetched < self.max_pages and len(docs) < remaining:
            params: dict[str, Any] = {
                "subreddit": subreddit,
                "limit": self.page_size,
                "sort": "desc",
                "sort_type": "created_utc",
            }
            if before is not None:
                params["before"] = before

            try:
                resp = await self.get_with_retry(f"{API_BASE}/{path}", params=params)
                items = (resp.json() or {}).get("data") or []
            except Exception as exc:  # network / retries exhausted
                print(f"[-] {self.name}: {subreddit}/{kind} failed: {exc.__class__.__name__}: {str(exc)[:80]}")
                return

            pages_fetched += 1
            if not items:
                return  # no more data

            # Oldest item on this page becomes the next `before` cursor.
            page_min = min(int(it.get("created_utc") or 0) for it in items)
            before = page_min if page_min > 0 else None

            for it in items:
                if len(docs) >= remaining:
                    return
                doc = self._to_doc(subreddit, kind, it, since_epoch)
                if doc is not None:
                    docs[doc.dedupe_key()] = doc

            # Entire page older than the cutoff -> done with this stream.
            if page_min < since_epoch:
                return

            if pages_fetched < self.max_pages and self.request_gap_s > 0:
                await asyncio.sleep(self.request_gap_s)

    def _to_doc(self, subreddit: str, kind: str, item: dict, since_epoch: int) -> RawDoc | None:
        created = int(item.get("created_utc") or 0)
        if created == 0 or created < since_epoch:
            return None

        text = ""
        title: str | None = None
        if kind == "post":
            text = (item.get("selftext") or "").strip()
            title = (item.get("title") or "").strip()
            if not text:
                text = title or ""
        else:  # comment
            text = (item.get("body") or "").strip()

        if is_removed(text):
            return None

        permalink = item.get("permalink") or ""
        url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else (permalink or "")

        author = item.get("author")
        author_hash = hash_author(author) if author and author != "[deleted]" else None

        return RawDoc(
            source=self.name,
            external_id=f"{subreddit}:{kind}:{item.get('id', '')}",
            text=text[:20000],  # hard ceiling on payload size
            url=url,
            title=title,
            author_hash=author_hash,
            published_at=datetime.fromtimestamp(created, tz=timezone.utc),
            lang=None,
            location_hint=None,
            meta={
                "subreddit": subreddit,
                "kind": kind,
                "score": item.get("score"),
                "num_comments": item.get("num_comments"),
            },
        )


# ----------------------------------------------------------------------
# Standalone smoke test:  python -m basr.adapters.reddit_arctic
# ----------------------------------------------------------------------
async def _smoke_test() -> None:
    adapter = ArcticShiftRedditAdapter(
        subreddits=["dubai", "UAE"],
        max_pages=1,
        page_size=10,
        request_gap_s=1.0,
    )
    docs = await adapter.fetch(limit=20)
    print(f"[+] Collected {len(docs)} docs")
    for d in docs[:5]:
        print(f"  - [{d.meta.get('kind')}] {(d.title or d.text)[:60]!r} ({d.published_at:%Y-%m-%d})")


if __name__ == "__main__":
    asyncio.run(_smoke_test())
