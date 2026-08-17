import asyncio
from dotenv import load_dotenv
from scraper_reddit import fetch_reddit_signals
from scraper_linkedin import fetch_linkedin_signals
from processor import process_raw_signal
from database import insert_signals_to_db
from pdf_generator import create_pdf_report

load_dotenv()


async def run_pipeline(max_to_process: int = 10, generate_pdf: bool = True, client_name: str = "DIFC Client"):
    """
    Full BASR pipeline:
    1. Scrape Reddit + LinkedIn
    2. Process through AI classifier
    3. Save to Supabase
    4. Generate PDF report
    """

    print("\n" + "="*50)
    print("  BASR Intelligence Engine - Starting Pipeline")
    print("="*50 + "\n")

    # STEP 1: Scrape both sources at the same time
    print("[1/4] Fetching signals from Reddit and LinkedIn simultaneously...")
    reddit_results, linkedin_results = await asyncio.gather(
        fetch_reddit_signals(),
        fetch_linkedin_signals()
    )

    raw_payload = reddit_results + linkedin_results
    print(f"\n[+] Total raw signals collected: {len(raw_payload)}")

    if not raw_payload:
        print("[-] No signals collected. Check your internet connection.")
        return []

    # STEP 2: Process through AI (limit to max_to_process to control API costs)
    print(f"\n[2/4] Processing first {max_to_process} signals through AI classifier...")
    print("      (Increase max_to_process in the function call to process more)\n")

    processed_signals = []

    for i, item in enumerate(raw_payload[:max_to_process]):
        print(f"      [{i+1}/{min(max_to_process, len(raw_payload))}] Processing from {item['source_platform']}...", end=" ")

        ai_result = process_raw_signal(item["raw_text"])

        if ai_result:
            final_record = {**item, **ai_result}
            processed_signals.append(final_record)
            signal_type = ai_result.get("signal_type", "?")
            sector = ai_result.get("sector", "?")
            intensity = ai_result.get("intensity_score", "?")
            print(f"-> [{signal_type.upper()}] {sector} | Intensity: {intensity}/5")
        else:
            print("-> [SKIPPED] AI returned no result")

    print(f"\n[+] AI Processing complete: {len(processed_signals)} signals classified")
    reddit_count = sum(1 for s in raw_payload if s.get("source_platform") == "reddit")
    news_count = sum(1 for s in raw_payload if s.get("source_platform") == "news")
    
    print(f"[*] Sources: {reddit_count} Reddit signals, {news_count} news signals")
    
    if reddit_count == 0:
        print("[!] WARNING: No Reddit data collected today.")
        print("[!] Report will be news-only - consider waiting for Reddit recovery before sending to clients.")

    # STEP 3: Save to Supabase
    print(f"\n[3/4] Saving to Supabase database...")
    insert_signals_to_db(processed_signals)

    # STEP 4: Generate PDF report
    if generate_pdf and processed_signals:
        print(f"\n[4/4] Generating PDF intelligence report...")
        filename = create_pdf_report(processed_signals, client_name=client_name)
        print(f"[+] Report ready: {filename}")
    else:
        print("\n[4/4] PDF generation skipped.")

    print("\n" + "="*50)
    print("  Pipeline Complete!")
    print("="*50 + "\n")

    return processed_signals


if __name__ == "__main__":
    # Change max_to_process to process more signals (costs more API credits)
    # Change client_name to your actual client's name for the PDF
    asyncio.run(run_pipeline(
    max_to_process=35,
        generate_pdf=True,
        client_name="clients name here"
    ))

