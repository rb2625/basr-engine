import asyncio
import httpx
import xml.etree.ElementTree as ET
import re

# Reddit public RSS feeds - no login or API key needed
REDDIT_FEEDS = [
    ("reddit", "r/dubai",  "https://www.reddit.com/r/dubai/new/.rss"),
    ("reddit", "r/uae",    "https://www.reddit.com/r/uae/new/.rss"),
]

# UAE business news RSS feeds - guaranteed to work, great economic signals
NEWS_FEEDS = [
    ("news", "Arabian Business",   "https://www.arabianbusiness.com/rss"),
    ("news", "Zawya Business",     "https://www.zawya.com/rss/uae-business.xml"),
    ("news", "Gulf Business",      "https://gulfbusiness.com/feed/"),
    ("news", "Wam UAE News",       "https://wam.ae/rss.xml"),
]


def clean_html(text):
    """Strip HTML tags from text."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).strip()


async def fetch_one_feed(client, source_type, name, url):
    """Fetch and parse a single RSS or Atom feed."""
    signals = []
    try:
        response = await client.get(url)

        if response.status_code != 200:
            print(f"[-] {name}: status {response.status_code}")
            return signals

        root = ET.fromstring(response.content)

        # Try Atom format (Reddit uses this)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = root.findall('.//atom:entry', ns)

        if entries:
            for entry in entries[:30]:
                title   = entry.find('atom:title', ns)
                content = entry.find('atom:content', ns)
                if content is None:
                    content = entry.find('atom:summary', ns)
                link    = entry.find('atom:link', ns)

                title_text   = clean_html(title.text   if title   is not None else "")
                content_text = clean_html(content.text if content is not None else "")
                link_url     = link.get('href', '')    if link    is not None else ""

                combined = f"{title_text}\n{content_text}".strip()[:2000]
                if combined:
                    signals.append({
                        "source_platform": source_type,
                        "source_url":      link_url or url,
                        "raw_text":        combined,
                    })

        else:
            # Try RSS 2.0 format (news sites use this)
            items = root.findall('.//item')
            for item in items[:30]:
                title = item.find('title')
                desc  = item.find('description')
                link  = item.find('link')

                title_text = clean_html(title.text if title is not None else "")
                desc_text  = clean_html(desc.text  if desc  is not None else "")
                link_url   = link.text             if link  is not None else ""

                combined = f"{title_text}\n{desc_text}".strip()[:2000]
                if combined:
                    signals.append({
                        "source_platform": source_type,
                        "source_url":      link_url or url,
                        "raw_text":        combined,
                    })

        print(f"[+] {name}: {len(signals)} signals collected")

    except Exception as e:
        print(f"[-] {name}: {str(e)[:80]}")

    return signals


async def fetch_reddit_signals():
    """
    Fetches signals from Reddit RSS + UAE news RSS feeds.
    No API key required. Function name kept the same so orchestrator works unchanged.
    """
    all_signals = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept":     "*/*",
    }

    all_feeds = REDDIT_FEEDS + NEWS_FEEDS

    async with httpx.AsyncClient(headers=headers, timeout=30.0, follow_redirects=True) as client:
        tasks   = [fetch_one_feed(client, s_type, name, url) for s_type, name, url in all_feeds]
        results = await asyncio.gather(*tasks)

        for result in results:
            all_signals.extend(result)

    print(f"\n[+] Grand total: {len(all_signals)} signals from all sources")
    return all_signals


# Test alone: python scraper_reddit.py
if __name__ == "__main__":
    signals = asyncio.run(fetch_reddit_signals())
    if signals:
        print(f"\nSample signal:\n{signals[0]['raw_text'][:300]}")
    else:
        print("No signals — check your internet connection")