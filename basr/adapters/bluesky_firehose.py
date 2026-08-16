"""Live Bluesky feed via the public Jetstream v2 firehose (keyless, free, open).

Bluesky's Jetstream is a public websocket stream of network events — no API key,
no approval, no quota. It is the "live" layer of the platform (the X/Twitter
firehose is now paid; this is the open equivalent).

Authoritative spec (verified 2026-08):
- Endpoints: wss://jetstream.us-east.bsky.network / wss://jetstream.us-west.bsky.network
- Live tail path: /xrpc/network.bsky.jetstream.subscribeEvents?collections=...&kinds=commit
- Subprotocol: xrpc.v1.json
- Envelope: {"$type": "message", "payload": {commit event}}
- Commit event fields are TOP-LEVEL in payload (no v1 `commit` nesting):
    {"did", "seq", "time", "operation", "collection", "rkey", "rev", "record"}
- record is already decoded; post text is record.text.

Design:
- Bounded-window collection fits the cron model: connect, listen N seconds,
  collect matching posts, disconnect. Each run captures a live slice.
- Server-side filter: collections=app.bsky.feed.post&kinds=commit.
- Local filter: UAE keywords (EN + AR + Arabizi), case-insensitive.
- Authors identified by DID; we hash it (privacy by construction).
- Delivery is at-least-once; we dedupe by did:rkey.
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime, timezone

import websockets

from .base import RawDoc, hash_author

JETSTREAM_ENDPOINTS: tuple[str, ...] = (
    "wss://jetstream.us-east.bsky.network",
    "wss://jetstream.us-west.bsky.network",
)
JETSTREAM_PATH = "/xrpc/network.bsky.jetstream.subscribeEvents"
SUBPROTOCOL = "xrpc.v1.json"

# UAE keywords: English + Arabic + common Arabizi/latin spellings.
UAE_KEYWORDS: tuple[str, ...] = (
    # English
    "uae", "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah",
    "fujairah", "umm al quwain", "al ain", "deira", "jumeirah", "downtown dubai",
    "difc", "dxb", "emirates",
    # Arabic
    "الإمارات", "دبي", "أبوظبي", "الشارقة", "عجمان", "رأس الخيمة",
    "الفجيرة", "أم القيوين", "العين", "ديرة", "جميرا",
    # Arabizi / latin spellings
    "3al ain", "al3ain",
)

MIN_TEXT_LEN = 12  # skip one-word noise


class BlueskyFirehoseAdapter:
    """Not a SourceAdapter subclass: the firehose is push-based, not request-based.

    It still emits RawDoc and plugs into the same pipeline.
    """

    name = "bluesky_firehose"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        keywords: tuple[str, ...] = UAE_KEYWORDS,
        min_text_len: int = MIN_TEXT_LEN,
    ) -> None:
        self.endpoint = endpoint or JETSTREAM_ENDPOINTS[0]
        self.keywords = keywords
        self.min_text_len = min_text_len
        # Word-boundary matching: 'deira' must not match inside 'choradeira'.
        # Works for Latin and Arabic (both are \w in Unicode mode).
        pattern = r"\b(?:{})\b".format("|".join(re.escape(kw) for kw in keywords))
        self._keyword_re = re.compile(pattern, re.IGNORECASE)

    @property
    def url(self) -> str:
        return f"{self.endpoint}{JETSTREAM_PATH}?collections=app.bsky.feed.post&kinds=commit"

    async def fetch(self, since: datetime | None = None, limit: int = 100, *, duration_s: float = 60.0) -> list[RawDoc]:
        """Listen for ``duration_s`` seconds and return matching posts (up to ``limit``)."""
        docs: list[RawDoc] = []
        seen: set[str] = set()
        loop = asyncio.get_event_loop()
        deadline = loop.time() + duration_s

        try:
            async with websockets.connect(
                self.url, subprotocols=[SUBPROTOCOL], max_size=16 * 1024 * 1024
            ) as ws:
                while loop.time() < deadline and len(docs) < limit:
                    try:
                        frame = await asyncio.wait_for(ws.recv(), timeout=min(10.0, max(1.0, deadline - loop.time())))
                    except asyncio.TimeoutError:
                        continue
                    except websockets.ConnectionClosed as exc:
                        print(f"[-] bluesky_firehose: connection closed ({exc.code}); reconnecting is handled by next cron run")
                        break

                    doc = self._maybe_to_doc(frame)
                    if doc is not None and doc.dedupe_key() not in seen:
                        seen.add(doc.dedupe_key())
                        docs.append(doc)
        except Exception as exc:
            print(f"[-] bluesky_firehose: {exc.__class__.__name__}: {str(exc)[:100]}")

        print(f"[+] bluesky_firehose: {len(docs)} UAE-matching posts in {duration_s:.0f}s window")
        return docs

    def _maybe_to_doc(self, frame: str | bytes) -> RawDoc | None:
        try:
            envelope = json.loads(frame)
        except (json.JSONDecodeError, TypeError):
            return None

        if envelope.get("$type") != "message":
            return None
        event = envelope.get("payload") or {}

        # Only commits for app.bsky.feed.post, operation create.
        if event.get("operation") != "create":
            return None
        if event.get("collection") != "app.bsky.feed.post":
            return None

        record = event.get("record") or {}
        text = (record.get("text") or "").strip()
        if len(text) < self.min_text_len:
            return None

        if self._keyword_re.search(text) is None:
            return None

        did = event.get("did") or ""
        rkey = event.get("rkey") or ""
        created_raw = record.get("createdAt") or event.get("time")

        published: datetime | None = None
        if created_raw:
            try:
                published = datetime.fromisoformat(created_raw.replace("Z", "+00:00"))
            except ValueError:
                published = None

        return RawDoc(
            source=self.name,
            external_id=f"{did}:{rkey}",
            text=text[:20000],
            url=f"https://bsky.app/profile/{did}/post/{rkey}" if did and rkey else "",
            title=None,
            author_hash=hash_author(did),
            published_at=published,
            lang=None,
            meta={
                "seq": event.get("seq"),
                "langs": record.get("langs") or [],
                "reply_parent": (record.get("reply") or {}).get("parent", {}).get("uri"),
            },
        )

    async def close(self) -> None:
        # websocket context manager handles cleanup per connection
        return None


# ----------------------------------------------------------------------
# Standalone smoke test:  python -m basr.adapters.bluesky_firehose
# ----------------------------------------------------------------------
async def _smoke_test() -> None:
    adapter = BlueskyFirehoseAdapter()
    # Keyword-boundary sanity checks (no network needed).
    pos = ["go to deira market today", "traffic in dubai is bad", "دبي اليوم", "#UAE life"]
    neg = ["choradeira de sempre", "deiramento artificial"]
    for t in pos:
        assert adapter._keyword_re.search(t) is not None, f"should match: {t!r}"
    for t in neg:
        assert adapter._keyword_re.search(t) is None, f"should NOT match: {t!r}"
    print("[+] keyword boundary checks passed")

    docs = await adapter.fetch(duration_s=25, limit=10)
    for d in docs[:5]:
        shown = d.text[:90].replace("\n", " ")
        print(f"  - {shown!r} ({d.published_at:%H:%M} UTC)" if d.published_at else f"  - {shown!r}")


if __name__ == "__main__":
    asyncio.run(_smoke_test())
