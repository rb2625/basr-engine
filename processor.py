import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an elite macroeconomic data analyst specializing in the UAE market.
Your job is to extract ONLY genuine economic intelligence signals from text.

You fluently understand formal Arabic, Gulf dialects, Egyptian and Levantine Arabic,
English, and Arabizi (3ashan, wallah, khara, yalla, 7aram, inshallah).

STRICT FILTERING RULES — classify as "neutral" and intensity 1 if the text is:
- International company news with no direct UAE market connection → neutral
- Personal complaints about individual situations unless they reveal 
  a systemic pattern affecting a named company or sector → neutral
- International company news with no direct UAE market connection → neutral
- Any signal where the UAE is not the primary affected market → neutral
- Personal complaints about government services or individual situations → neutral
  unless they reveal a systemic pattern affecting a named company or sector
- Personal social posts (dating, relationships, personal opinions)
- Generic product recommendations with no market implication
- Entertainment news unrelated to UAE economy
- International news with no clear UAE economic connection
- Student questions about education programs
- Individual consumer preference questions (best shawarma, teeth whitening etc.)

Only classify as stress/closure/opportunity if the text contains:
- Specific companies, banks, developers, or sectors experiencing measurable change
- Labor market signals (layoffs, hiring surges, salary trends)
- Real estate market movements (rent changes, closures, demand shifts)
- Financial stress (loan issues, payment failures, bank problems)
- Business closures or openings with named entities
- Supply chain or pricing disruptions affecting UAE market
- Regulatory or policy changes affecting businesses
- Macro indicators (GDP, PMI, trade, inflation signals)

CLASSIFICATION RULES:
- signal_type: "stress", "closure", "opportunity", or "neutral"
- sector: "F&B", "Real Estate", "Tech", "Retail", "Logistics", "Finance", "General"
  Use "General" ONLY for cross-sector macro signals — not for personal posts
- confidence_score: float 0.0 to 1.0
- intensity_score: 1 to 5
  1 = vague individual complaint, no named entity
  2 = named company or location, moderate signal
  3 = multiple reports or clear business impact
  4 = significant named-company or sector-wide impact
  5 = systemic risk, mass layoffs, major market disruption, macro indicator
- extracted_entities: {"companies": ["names"], "locations": ["places"]}
  Only include real company names and real UAE locations
- summary_en: ONE sentence stating the specific economic implication.
  Must name specific companies or locations where available.
  Never write vague summaries like "there is a demand for X services".

OUTPUT: ONLY a valid JSON object. No markdown. No backticks.
If the text has no genuine economic signal, return signal_type "neutral" intensity 1.
"""


def process_raw_signal(raw_signal_text):
    """
    Takes raw scraped text, sends to Groq, returns structured JSON dict.
    Returns None if processing fails.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this text from the UAE digital ecosystem:\n\n{raw_signal_text}"}
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
            max_tokens=400
        )

        response_text = response.choices[0].message.content
        if not response_text:
            return None

        # Clean up in case model adds backticks anyway
        clean_text = response_text.strip().strip("`").replace("json\n", "").strip()
        structured_data = json.loads(clean_text)

        # Validate and fix required fields
        if "detected_language" not in structured_data or not structured_data["detected_language"]:
            structured_data["detected_language"] = "mixed"

        if "signal_type" not in structured_data:
            structured_data["signal_type"] = "neutral"

        if "sector" not in structured_data:
            structured_data["sector"] = "General"

        if "confidence_score" not in structured_data:
            structured_data["confidence_score"] = 0.5

        if "intensity_score" not in structured_data:
            structured_data["intensity_score"] = 1

        if "summary_en" not in structured_data or not structured_data["summary_en"]:
            structured_data["summary_en"] = "No summary available."

        # Fix extracted_entities — Groq sometimes returns a flat list instead of a dict
        entities = structured_data.get("extracted_entities", {})
        if isinstance(entities, list):
            structured_data["extracted_entities"] = {
                "companies": [],
                "locations": entities
            }
        elif not isinstance(entities, dict):
            structured_data["extracted_entities"] = {"companies": [], "locations": []}

        return structured_data

    except json.JSONDecodeError as e:
        print(f"[-] JSON parse error: {str(e)}")
        return None
    except Exception as e:
        print(f"[-] AI Processing Error: {str(e)}")
        return None


# Test this file alone by running: python processor.py
if __name__ == "__main__":
    test_text = "Wallah my favorite cafe in Jumeirah just closed down 3ashan the landlord increased rent by 40%. Everyone I know in tech is getting laid off too. Standard Chartered just cut half their team in DIFC."
    result = process_raw_signal(test_text)
    print(f"\nTest result:\n{json.dumps(result, indent=2)}")