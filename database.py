import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("[-] Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in your .env file")

    return create_client(url, key)


def insert_signals_to_db(processed_signals: list) -> bool:
    """
    Takes a list of processed signal dicts and inserts them into Supabase.
    Skips duplicates based on source_url.
    """
    if not processed_signals:
        print("[-] No signals to insert into database.")
        return False

    supabase = get_supabase_client()
    inserted_count = 0
    skipped_count = 0

    for signal in processed_signals:
        try:
            # Build the exact record matching your Supabase table columns
            record = {
                "source_platform": signal.get("source_platform", "unknown"),
                "source_url": signal.get("source_url", f"unknown_{inserted_count}"),
                "raw_text": signal.get("raw_text", ""),
                "detected_language": signal.get("detected_language", "en"),
                "signal_type": signal.get("signal_type", "neutral"),
                "sector": signal.get("sector", "General"),
                "confidence_score": float(signal.get("confidence_score", 0.5)),
                "extracted_entities": signal.get("extracted_entities", {"companies": [], "locations": []}),
                "summary_en": signal.get("summary_en", "No summary available."),
                "intensity_score": int(signal.get("intensity_score", 1)),
            }

            supabase.table("economic_signals").insert(record).execute()
            inserted_count += 1

        except Exception as e:
            if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                skipped_count += 1  # Already in database, skip silently
            else:
                print(f"[-] Insert error for signal: {str(e)[:100]}")

    print(f"[+] Database: {inserted_count} new records saved, {skipped_count} duplicates skipped")
    return inserted_count > 0


# Test this file alone by running: python database.py
if __name__ == "__main__":
    supabase = get_supabase_client()
    print("[+] Supabase connection successful!")