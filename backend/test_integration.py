import sys
import os

# Add local directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from brand_guideline_extractor import BrandGuidelineExtractor
from brand_guideline_generator import BrandGuidelineGenerator


def test_integration():
    pdf_path = "/Users/ashishnevan/Downloads/brandguardai/slack_brand_guidelines_september2020.pdf"

    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        # Try to find it in current dir just in case
        if os.path.exists("slack_brand_guidelines_september2020.pdf"):
            pdf_path = "slack_brand_guidelines_september2020.pdf"
        else:
            print("Cannot run test without PDF.")
            return

    print(f"Testing with: {pdf_path}")

    # 1. Extraction
    extractor = BrandGuidelineExtractor()
    extracted_rules = extractor.extract_guidelines(pdf_path)

    print("\n--- Extracted Rules ---")
    print(extracted_rules.model_dump_json(indent=2))

    # 2. Generation (Simulating existing assets as empty for this test)
    assets_for_learning = []

    generator = BrandGuidelineGenerator()
    brand_kit = generator.generate_brand_kit(
        assets_for_learning, extracted_rules=extracted_rules
    )

    print("\n--- Final Brand Kit ---")
    import json

    print(json.dumps(brand_kit, indent=2))

    # Verification assertions
    if "Aubergine" in str(brand_kit) or "#4A154B" in str(brand_kit):
        print("\nSUCCESS: Extracted Slack brand colors found in final Brand Kit!")
    else:
        print("\nFAILURE: Slack brand colors not found.")


if __name__ == "__main__":
    test_integration()
