import logging

from pdf2image import convert_from_path

from brand_auditor import IntegratedBrandAuditor

# Configure Logging
logging.basicConfig(level=logging.INFO)

# Mock Brand Kit with Color Usage Rules
SLACK_KIT = {
    "brand_name": "Slack",
    "primary_colors": ["#4A154B", "#FFFFFF", "#000000"],
    "rich_colors": [
        {"name": "Aubergine", "hex": "#4A154B", "rgb": "74, 21, 75"},
        {"name": "White", "hex": "#FFFFFF", "rgb": "255, 255, 255"},
        {"name": "Horchata", "hex": "#F4EDE4", "rgb": "244, 237, 228"},
    ],
    "brand_voice_attributes": ["professional"],
    "forbidden_keywords": [],
    "frequent_keywords": ["professional", "clean"],
    "color_usage_rules": [
        {
            "background_color": "Aubergine",
            "allowed_text_colors": ["White"],
            "forbidden_text_colors": [],
            "context_description": "On Aubergine, use White text.",
        }
    ],
}


def test_smart_audit():
    print("Initializing Smart Auditor...")
    auditor = IntegratedBrandAuditor(SLACK_KIT, [])

    pdf_path = "../../slack_brand_guidelines_september2020.pdf"
    print(f"Loading PDF: {pdf_path}")

    images = convert_from_path(pdf_path, first_page=1, last_page=1)
    if not images:
        print("Failed to load PDF page.")
        return

    page_pil = images[0]
    print("Auditing Page 1...")

    results = auditor.audit_page(page_pil)

    print("\n--- AUDIT RESULTS ---")
    for r in results:
        print(f"[{r['type']}] Status: {r['status']} | Metric: {r['metric']}")

        if r["type"] == "PALETTE":
            # Expect PASS for background if Histogram works (Slack page 1 has colors)
            if r["status"] == "FAIL" and "Off-brand" in r["metric"]:
                print(">> ALERT: Palette check failed (Old K-Means behavior?)")
            elif "Background Compliant" in r["metric"]:
                print(">> SUCCESS: Histogram Logic Active.")

        if r["type"] == "TYPOGRAPHY":
            print(f">> Text Violation: {r['metric']}")


if __name__ == "__main__":
    test_smart_audit()
