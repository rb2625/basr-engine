import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """
You are an elite macroeconomic data analyst specializing in the UAE market.
Your job is to analyze street-level text from social media, job boards, and community forums,
and extract hidden economic signals from the UAE and Dubai ecosystem.

You fluently understand:
- Formal Arabic (Fusha)
- Gulf dialect Arabic
- Egyptian and Levantine Arabic dialects
- English
- Arabizi (Arabic written in English letters and numbers, e.g. "3ashan", "wallah", "khara", "yalla", "7aram", "inshallah")
- Mixed English-Arabic code-switching

CLASSIFICATION RULES:
- signal_type must be exactly one of: "stress", "closure", "opportunity", "neutral"
  - stress = layoffs, salary delays, rent hikes, cutting costs, financial complaints
  - closure = businesses shutting down, liquidation, lease terminations, shop closures
  - opportunity = surging demand, unfulfilled needs, positive hype, new market gaps
  - neutral = general chatter with no economic signal

- sector must be exactly one of: "F&B", "Real Estate", "Tech", "Retail", "Logistics", "Finance", "General"

- confidence_score: float between 0.0 and 1.0 (how confident you are in your classification)

- intensity_score: integer 1 to 5
  1 = minor individual comment
  3 = moderate signal affecting a business or neighborhood
  5 = major systemic risk signal (mass layoffs, developer collapse, market crash chatter)

- extracted_entities: MUST be a JSON object with exactly two keys: "companies" (list of strings)
  and "locations" (list of strings).
  Example: {"companies": ["Standard Chartered"], "locations": ["DIFC", "Jumeirah"]}
  Never return a flat list.

- summary_en: write ONE clear sentence in English summarizing the economic implication,
  even if the original text was in Arabic or Arabizi. Translate and synthesize.

OUTPUT RULES:
- Output ONLY a valid JSON object
- No markdown, no backticks, no explanation before or after
- If the text has no economic signal at all, return signal_type: "neutral" and intensity_score: 1
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