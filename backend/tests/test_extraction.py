from src.brand_guideline_extractor import BrandGuidelineExtractor

# Mock the environment to use the user's setup if needed,
# relying on existing .env or environment variables.


def test_extraction():
    extractor = BrandGuidelineExtractor()
    pdf_path = "../../slack_brand_guidelines_september2020.pdf"

    print(f"Running extraction on: {pdf_path}")
    extracted_data = extractor.extract_guidelines(pdf_path)

    print("\n--- Extracted Color Usage Rules ---")
    if extracted_data.color_usage_rules:
        for rule in extracted_data.color_usage_rules:
            print(f"Background: {rule.background_color}")
            print(f"Allowed Text: {rule.allowed_text_colors}")
            print(f"Forbidden Text: {rule.forbidden_text_colors}")
            print(f"Context: {rule.context_description}")
            print("-" * 20)
    else:
        print("No Color Usage Rules found.")


if __name__ == "__main__":
    test_extraction()
