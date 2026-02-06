import logging
import os

import pytest
from pdf2image import convert_from_path

from src.brand_auditor import IntegratedBrandAuditor

# Configure Logging
logging.basicConfig(level=logging.DEBUG)

# Mock Brand Kit
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
    "color_usage_rules": [],
}


@pytest.mark.skipif(
    not os.path.exists("../../slack_brand_guidelines_september2020.pdf"),
    reason="Test PDF not found",
)
def test_smart_audit_integration():
    """Integration test for the full audit pipeline on a single page."""
    print("Initializing Smart Auditor...")
    auditor = IntegratedBrandAuditor(SLACK_KIT, [])

    pdf_path = "../../slack_brand_guidelines_september2020.pdf"

    # Check fallback path
    if not os.path.exists(pdf_path):
        if os.path.exists("slack_brand_guidelines_september2020.pdf"):
            pdf_path = "slack_brand_guidelines_september2020.pdf"

    print(f"Loading PDF: {pdf_path}")

    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
    except Exception as e:
        pytest.fail(f"Failed to load PDF: {e}")

    assert len(images) > 0, "No pages loaded from PDF"

    page_pil = images[0]
    print("Auditing Page 1...")

    results = auditor.audit_page(page_pil)

    assert len(results) > 0, "No results returned from audit"

    # Check for specific expected behavior (Slack Page 1 is usually compliant)
    has_palette_result = any(r["type"] == "PALETTE" for r in results)
    assert has_palette_result, "Missing palette analysis result"
