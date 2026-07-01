from fpdf import FPDF
from datetime import datetime


class BASRReport(FPDF):

    def header(self):
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(41, 128, 185)
        self.cell(0, 8, "BASR | UAE Economic Pulse Intelligence", ln=True, align="C")
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(130, 130, 130)
        self.cell(0, 6, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Confidential", ln=True, align="C")
        self.set_draw_color(41, 128, 185)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(130, 130, 130)
        self.cell(0, 10, f"BASR Intelligence Engine | Page {self.page_no()}", align="C")


def create_pdf_report(signals_data: list, client_name: str = "Valued Client"):
    """
    Takes a list of processed signal dicts and generates a branded PDF report.
    Saves it in the current directory.
    """
    if not signals_data:
        print("[-] No data to generate PDF report.")
        return None

    pdf = BASRReport()
    pdf.set_margins(15, 15, 15)

    # --- Cover Page ---
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(41, 128, 185)
    pdf.ln(30)
    pdf.cell(0, 15, "BASR", ln=True, align="C")

    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 10, "UAE Economic Pulse Intelligence Report", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, f"Week of {datetime.now().strftime('%B %d, %Y')}", ln=True, align="C")
    pdf.ln(5)

    pdf.set_font("Helvetica", "I", 11)
    pdf.cell(0, 8, f"Prepared exclusively for: {client_name}", ln=True, align="C")
    pdf.ln(20)

    # Summary stats box
    stress_count = sum(1 for s in signals_data if s.get("signal_type") == "stress")
    closure_count = sum(1 for s in signals_data if s.get("signal_type") == "closure")
    opportunity_count = sum(1 for s in signals_data if s.get("signal_type") == "opportunity")
    high_intensity = sum(1 for s in signals_data if int(s.get("intensity_score", 0)) >= 4)

    pdf.set_fill_color(245, 248, 252)
    pdf.set_draw_color(41, 128, 185)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 8, "EXECUTIVE SUMMARY", ln=True, align="C")
    pdf.ln(3)

    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(50, 50, 50)
    pdf.cell(0, 7, f"Total Signals Analyzed:     {len(signals_data)}", ln=True, align="C")
    pdf.cell(0, 7, f"Stress Signals:              {stress_count}", ln=True, align="C")
    pdf.cell(0, 7, f"Closure Indicators:          {closure_count}", ln=True, align="C")
    pdf.cell(0, 7, f"Opportunity Signals:         {opportunity_count}", ln=True, align="C")
    pdf.cell(0, 7, f"High Intensity Alerts (4-5): {high_intensity}", ln=True, align="C")

    # --- Signal Pages by Sector ---
    sectors = sorted(set(s.get("sector", "General") for s in signals_data))

    # Color map for signal types
    type_colors = {
        "stress":      (231, 76,  60),   # Red
        "closure":     (230, 126, 34),   # Orange
        "opportunity": (39,  174, 96),   # Green
        "neutral":     (149, 165, 166),  # Grey
    }

    for sector in sectors:
        sector_signals = [s for s in signals_data if s.get("sector") == sector]

        # Only skip if ALL signals in sector are neutral AND low intensity
        meaningful = [s for s in sector_signals if s.get("signal_type") != "neutral" or int(s.get("intensity_score", 1)) >= 3]
        if not meaningful:
            continue

        pdf.add_page()

        # Sector header bar
        pdf.set_fill_color(52, 73, 94)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"  SECTOR: {sector.upper()}", ln=True, fill=True)
        pdf.ln(4)

        for signal in meaningful:
            signal_type = signal.get("signal_type", "neutral").lower()
            intensity = int(signal.get("intensity_score", 1))
            color = type_colors.get(signal_type, (149, 165, 166))

            # Signal type badge
            pdf.set_fill_color(*color)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(40, 7, f"  {signal_type.upper()}", fill=True)
            pdf.set_fill_color(240, 240, 240)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(40, 7, f"  Intensity: {intensity}/5", fill=True)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 7, f"  Source: {signal.get('source_platform', 'N/A').capitalize()}", ln=True)

            # Summary
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(30, 30, 30)
            summary = signal.get("summary_en", "No summary available.")
            pdf.multi_cell(0, 6, f"Insight: {summary}")

            # Entities
            entities = signal.get("extracted_entities", {})
            companies = ", ".join(entities.get("companies", []))
            locations = ", ".join(entities.get("locations", []))

            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(120, 120, 120)
            if companies:
                pdf.cell(0, 5, f"Companies: {companies}", ln=True)
            if locations:
                pdf.cell(0, 5, f"Locations: {locations}", ln=True)

            pdf.set_draw_color(220, 220, 220)
            pdf.line(15, pdf.get_y() + 2, 195, pdf.get_y() + 2)
            pdf.ln(6)

            # Check if we are near bottom of page
            if pdf.get_y() > 260:
                pdf.add_page()
                pdf.set_fill_color(52, 73, 94)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, f"  SECTOR: {sector.upper()} (continued)", ln=True, fill=True)
                pdf.ln(4)

    # Save the file
    filename = f"BASR_Report_{datetime.now().strftime('%Y-%m-%d_%H-%M')}.pdf"
    pdf.output(filename)
    print(f"[+] PDF report saved: {filename}")
    return filename


# Test this file alone by running: python pdf_generator.py
if __name__ == "__main__":
    # Fake test data to preview the PDF format
    test_signals = [
        {
            "source_platform": "reddit",
            "signal_type": "closure",
            "sector": "F&B",
            "intensity_score": 4,
            "confidence_score": 0.92,
            "summary_en": "Popular Jumeirah cafe closed after landlord raised rent by 40%, owner confirms on Reddit.",
            "extracted_entities": {"companies": [], "locations": ["Jumeirah"]},
        },
        {
            "source_platform": "reddit",
            "signal_type": "stress",
            "sector": "Tech",
            "intensity_score": 4,
            "confidence_score": 0.88,
            "summary_en": "Standard Chartered DIFC reportedly cut half its tech team, multiple sources confirming layoffs.",
            "extracted_entities": {"companies": ["Standard Chartered"], "locations": ["DIFC"]},
        },
        {
            "source_platform": "linkedin",
            "signal_type": "opportunity",
            "sector": "Logistics",
            "intensity_score": 3,
            "confidence_score": 0.75,
            "summary_en": "Surge in last-mile delivery job postings in Dubai indicates growing e-commerce demand.",
            "extracted_entities": {"companies": [], "locations": ["Dubai"]},
        },
    ]

    create_pdf_report(test_signals, client_name="Test Client")
    print("Open the generated PDF in your folder to preview it.")