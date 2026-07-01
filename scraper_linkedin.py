import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def fetch_linkedin_signals():
    all_signals = []

    # Public LinkedIn job search for Dubai - no login needed
    target_url = (
        "https://www.linkedin.com/jobs/search"
        "?keywords=&location=Dubai%2C%20United%20Arab%20Emirates"
        "&geoId=104616061&f_TPR=r86400&sortBy=DD"
    )

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            print("[*] LinkedIn: Opening browser...")
            await page.goto(target_url, timeout=60000)
            await asyncio.sleep(4)  # Wait for dynamic content to load

            # Scroll down to load more listings
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(2)

            # Try to grab job cards - LinkedIn changes these selectors sometimes
            job_cards = await page.locator("div.base-card").all()

            if not job_cards:
                # Fallback selector if LinkedIn updated their layout
                job_cards = await page.locator("li.jobs-search-results__list-item").all()

            print(f"[*] LinkedIn: Found {len(job_cards)} job cards")

            for card in job_cards[:25]:
                try:
                    title_el = card.locator("h3")
                    company_el = card.locator("h4")
                    link_el = card.locator("a").first

                    title = await title_el.inner_text() if await title_el.count() > 0 else "Unknown Role"
                    company = await company_el.inner_text() if await company_el.count() > 0 else "Unknown Company"
                    url = await link_el.get_attribute("href") if await link_el.count() > 0 else "N/A"

                    combined_text = f"NEW JOB POSTING in Dubai: {title.strip()} at {company.strip()}."

                    signal = {
                        "source_platform": "linkedin",
                        "source_url": url.split("?")[0] if url and url != "N/A" else f"linkedin_job_{len(all_signals)}",
                        "raw_text": combined_text,
                    }
                    all_signals.append(signal)

                except Exception:
                    continue  # Skip broken cards

        except Exception as e:
            print(f"[-] LinkedIn scraper error: {str(e)}")
            print("[-] This is common - LinkedIn updates their page layout frequently.")
            print("[-] Reddit data will still be processed.")

        finally:
            await browser.close()

    print(f"[+] LinkedIn total: {len(all_signals)} signals collected")
    return all_signals


# Test this file alone by running: python scraper_linkedin.py
if __name__ == "__main__":
    signals = asyncio.run(fetch_linkedin_signals())
    print(f"\nSample signal:\n{signals[0] if signals else 'No signals found'}")