from fpdf import FPDF
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()


def get_signals_from_db(limit: int = 200) -> list:
    """Pull recent signals from Supabase. Returns empty list on failure."""
    try:
        from supabase import create_client
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            return []
        supabase = create_client(url, key)
        response = supabase.table("economic_signals") \
            .select("*") \
            .order("created_at", desc=True) \
            .limit(limit) \
            .execute()
        # Cast to list of plain dicts so Pylance is happy
        raw = response.data or []
        return [dict(row) if isinstance(row, dict) else {} for row in raw]
    except Exception as e:
        print(f"[-] Could not pull from DB: {str(e)[:80]}")
        return []


def safe_str(value: object, default: str = "") -> str:
    """Safely convert any value to string."""
    if value is None:
        return default
    return str(value)


def safe_int(value: object, default: int = 1) -> int:
    """Safely convert any value to int."""
    try:
        return int(value)  # type: ignore
    except (TypeError, ValueError):
        return default


class BASRReport(FPDF):

    def header(self) -> None:
        self.set_fill_color(26, 82, 118)
        self.rect(0, 0, 210, 18, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(255, 255, 255)
        self.set_y(5)
        self.cell(0, 8, "BASR  |  UAE Economic Pulse Intelligence", align="C")
        self.ln()
        self.set_font("Helvetica", "", 8)
        self.set_y(11)
        self.cell(0, 5, f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}  |  CONFIDENTIAL", align="C")
        self.set_y(22)

    def footer(self) -> None:
        self.set_y(-12)
        self.set_fill_color(26, 82, 118)
        self.rect(0, 285, 210, 15, "F")
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(200, 220, 240)
        self.cell(0, 8, f"BASR Intelligence Engine  |  Page {self.page_no()}  |  Not for redistribution", align="C")

    def section_header(self, text: str) -> None:
        self.set_fill_color(26, 82, 118)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 12)
        self.cell(0, 9, f"  {text}", fill=True)
        self.ln()
        self.set_text_color(30, 30, 30)
        self.ln(3)

    def stat_row(self, label: str, value: str, r: int, g: int, b: int) -> None:
        self.set_fill_color(r, g, b)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 16)
        self.cell(44, 14, value, align="C", fill=True)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(50, 50, 50)
        self.cell(0, 14, f"  {label}")
        self.ln()


def create_pdf_report(current_signals: list, client_name: str = "Valued Client") -> str | None:
    if not current_signals:
        print("[-] No data to generate PDF.")
        return None

    # Try to enrich with historical DB data
    db_signals = get_signals_from_db()
    all_signals: list = db_signals if len(db_signals) > len(current_signals) else current_signals
    print(f"[*] PDF: using {len(all_signals)} signals ({len(current_signals)} from this run)")

    # ── Pre-compute stats ─────────────────────────────────────────
    total       = len(all_signals)
    stress      = sum(1 for s in all_signals if s.get("signal_type") == "stress")
    closure     = sum(1 for s in all_signals if s.get("signal_type") == "closure")
    opportunity = sum(1 for s in all_signals if s.get("signal_type") == "opportunity")
    high        = sum(1 for s in all_signals if safe_int(s.get("intensity_score"), 0) >= 4)

    sectors: dict[str, int] = {}
    for s in all_signals:
        sec = safe_str(s.get("sector"), "General")
        sectors[sec] = sectors.get(sec, 0) + 1

    type_colors: dict[str, tuple[int, int, int]] = {
        "stress":      (192, 57,  43),
        "closure":     (230, 126, 34),
        "opportunity": (39,  174, 96),
        "neutral":     (149, 165, 166),
    }

    pdf = BASRReport()
    pdf.set_margins(14, 24, 14)
    pdf.set_auto_page_break(auto=True, margin=18)

    # ── COVER PAGE ────────────────────────────────────────────────
    pdf.add_page()
    pdf.ln(20)

    pdf.set_font("Helvetica", "B", 42)
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 18, "BASR", align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 15)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 9, "UAE Economic Pulse Intelligence", align="C")
    pdf.ln()

    pdf.set_draw_color(26, 82, 118)
    pdf.set_line_width(0.8)
    pdf.line(40, pdf.get_y() + 3, 170, pdf.get_y() + 3)
    pdf.ln(10)

    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 8, "Weekly Intelligence Report", align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Period ending {datetime.now().strftime('%B %d, %Y')}", align="C")
    pdf.ln(8)

    pdf.set_font("Helvetica", "I", 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 7, f"Prepared exclusively for: {client_name}", align="C")
    pdf.ln(14)

    # Stats
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 8, "EXECUTIVE SUMMARY", align="C")
    pdf.ln(6)

    pdf.set_x(14)
    pdf.stat_row("Total Signals Analyzed", str(total),        41,  128, 185)
    pdf.set_x(14)
    pdf.stat_row("Stress Signals",          str(stress),      192, 57,  43)
    pdf.set_x(14)
    pdf.stat_row("Business Closures",       str(closure),     230, 126, 34)
    pdf.set_x(14)
    pdf.stat_row("Opportunity Signals",     str(opportunity), 39,  174, 96)
    pdf.set_x(14)
    pdf.stat_row("High Intensity (4-5)",    str(high),        142, 68,  173)

    # Sector bar chart
    pdf.ln(6)
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(26, 82, 118)
    pdf.cell(0, 7, "SIGNALS BY SECTOR", align="C")
    pdf.ln(4)

    for sector, count in sorted(sectors.items(), key=lambda x: -x[1]):
        bar_w = max(2, int((count / total) * 110))
        pdf.set_x(30)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(42, 6, sector)
        pdf.set_fill_color(26, 82, 118)
        pdf.cell(bar_w, 6, "", fill=True)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(20, 6, f"  {count}")
        pdf.ln()

    # ── SIGNAL DETAIL PAGES ───────────────────────────────────────
    sector_order = sorted(
        sectors.keys(),
        key=lambda x: -sectors.get(x, 0)
    )

    for sector in sector_order:
        sector_signals = [
            s for s in all_signals
            if safe_str(s.get("sector"), "General") == sector
            and safe_str(s.get("signal_type"), "neutral") != "neutral"
        ]
        if not sector_signals:
            continue

        pdf.add_page()
        pdf.section_header(f"SECTOR: {sector.upper()}  ({len(sector_signals)} signals)")

        for signal in sector_signals:
            stype     = safe_str(signal.get("signal_type"), "neutral").lower()
            intensity = safe_int(signal.get("intensity_score"), 1)
            platform  = safe_str(signal.get("source_platform"), "unknown").capitalize()
            summary   = safe_str(signal.get("summary_en"), "No summary available.")
            color     = type_colors.get(stype, (149, 165, 166))

            # Entities — handle both dict and list formats
            raw_entities = signal.get("extracted_entities") or {}
            if isinstance(raw_entities, dict):
                companies_list = raw_entities.get("companies") or []
                locations_list = raw_entities.get("locations") or []
            elif isinstance(raw_entities, list):
                companies_list = []
                locations_list = [safe_str(e) for e in raw_entities]
            else:
                companies_list = []
                locations_list = []

            companies = ", ".join(safe_str(c) for c in companies_list if c)
            locations = ", ".join(safe_str(l) for l in locations_list if l)
            dots = "+" * intensity + "-" * (5 - intensity)
            # Signal badge row
            pdf.set_fill_color(*color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(30, 6, f"  {stype.upper()}", fill=True)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_text_color(80, 80, 80)
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(32, 6, f"  {dots}", fill=True)
            pdf.set_text_color(130, 130, 130)
            pdf.cell(0, 6, f"  via {platform}")
            pdf.ln()

            # Summary text
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            pdf.set_x(14)
            pdf.multi_cell(0, 5, summary)

            # Entities
            if companies or locations:
                pdf.set_font("Helvetica", "I", 8)
                pdf.set_text_color(120, 120, 120)
                pdf.set_x(14)
                if companies:
                    pdf.cell(0, 5, f"Companies: {companies}")
                    pdf.ln()
                if locations:
                    pdf.cell(0, 5, f"Locations: {locations}")
                    pdf.ln()

            # Divider
            pdf.set_draw_color(220, 220, 220)
            pdf.set_line_width(0.3)
            y = pdf.get_y() + 2
            pdf.line(14, y, 196, y)
            pdf.ln(6)

    filename = f"BASR_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
    pdf.output(filename)
    print(f"[+] PDF saved: {filename}")
    return filename


if __name__ == "__main__":
    test: list = [
        {"source_platform": "reddit",   "signal_type": "closure",     "sector": "F&B",
         "intensity_score": 4, "summary_en": "Popular Jumeirah cafe closed after 40% rent hike.",
         "extracted_entities": {"companies": [], "locations": ["Jumeirah"]}},
        {"source_platform": "linkedin", "signal_type": "opportunity",  "sector": "Tech",
         "intensity_score": 3, "summary_en": "Surge in AI Engineer postings in DIFC signals growing demand.",
         "extracted_entities": {"companies": ["ADNOC"], "locations": ["DIFC"]}},
        {"source_platform": "news",     "signal_type": "stress",       "sector": "Real Estate",
         "intensity_score": 4, "summary_en": "JVC residents report mass exodus due to 25% service charge hike.",
         "extracted_entities": {"companies": [], "locations": ["JVC", "Dubai"]}},
    ]
    create_pdf_report(test, client_name="Sample DIFC Investment Advisory")
    print("Done — open the PDF in your folder.")