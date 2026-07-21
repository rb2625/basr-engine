# BASR (بصر)

Multilingual economic intelligence engine that tracks the UAE market pulse. It scrapes Reddit, LinkedIn job postings and regional news, classifies every signal with AI, and turns the results into a client-ready PDF report.

## What it does

1. Scrapes Reddit (r/dubai, r/uae, r/DubaiJobs, r/dubaiexpats, r/abudhabi) via RSS, public LinkedIn job listings for Dubai, and a set of Bloomberg and Google News feeds covering UAE business, real estate, jobs, retail and banking.
2. Sends each piece of raw text to Groq (llama-3.3-70b-versatile) with a system prompt built to understand formal Arabic, Gulf dialects, Egyptian and Levantine Arabic, English, and Arabizi. The model classifies each signal as stress, closure, opportunity or neutral, and tags it with a sector, a confidence score and an intensity score from 1 to 5.
3. Stores every classified signal in Supabase and skips duplicates automatically.
4. Builds a branded PDF report using fpdf2: a cover page with summary stats, a page of the top signals ranked by intensity and confidence, then a sector-by-sector breakdown.
5. Runs on its own twice a day through a GitHub Actions cron job, 7am and 7pm Dubai time.

## Stack

Python, Groq API, Supabase, Playwright, httpx, fpdf2, GitHub Actions.

## Files

- `orchestrator.py` runs the full pipeline end to end.
- `scraper_reddit.py` pulls the Reddit and news RSS/Atom feeds.
- `scraper_linkedin.py` scrapes public LinkedIn job postings for Dubai with Playwright.
- `processor.py` sends raw text to Groq and returns structured JSON.
- `database.py` handles reads and writes to Supabase.
- `pdf_generator.py` builds the PDF report.
- `.github/workflows/basr_cron.yml` schedules the automated run.

## Running it

```bash
pip install -r requirements.txt
python -m playwright install chromium
python orchestrator.py
```

You'll need `GROQ_API_KEY`, `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` set in a `.env` file.

## Status

Private repo, still evolving. One of my flagship projects.
