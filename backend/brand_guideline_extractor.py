import pytesseract
from pdf2image import convert_from_path
from pydantic import BaseModel
from typing import List, Optional
import os
import json

# --- Data Models ---


class BrandColor(BaseModel):
    name: str  # e.g. "Aubergine"
    hex: str  # e.g. "#4A154B"
    rgb: Optional[str] = None
    cmyk: Optional[str] = None
    usage: Optional[str] = None  # e.g. "Core", "Secondary"
    text_color_rule: Optional[str] = None  # e.g. "White"


class BrandTypography(BaseModel):
    family: str
    weights: List[str] = []
    use_case: Optional[str] = None  # e.g. "Headlines"


class BrandLogoRule(BaseModel):
    rule: str
    type: str  # "DO" or "DONT"


class ExtractedBrandInfo(BaseModel):
    brand_name: Optional[str] = None
    colors: List[BrandColor] = []
    typography: List[BrandTypography] = []
    logo_rules: List[BrandLogoRule] = []
    forbidden_keywords: List[str] = []


class BrandGuidelineExtractor:
    def __init__(self):
        print("Initializing Brand Guideline Extractor...")
        # In a real app, initialize LLM client here (e.g. OpenAI / Gemini)

    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 20) -> str:
        """Converts PDF pages to text using OCR."""
        try:
            pages = convert_from_path(pdf_path, last_page=max_pages)
            full_text = ""
            for i, page in enumerate(pages):
                text = pytesseract.image_to_string(page)
                full_text += f"\n--- Page {i + 1} ---\n{text}"
            return full_text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""

    def _call_llm(self, text: str) -> ExtractedBrandInfo:
        """
        Uses LiteLLM to call ANY supported LLM (OpenAI, Gemini, Anthropic, etc.)
        Provider is determined by 'LLM_MODEL' env var (default: gpt-3.5-turbo).
        """
        from litellm import completion

        print("Parsing text with LLM (via LiteLLM)...")

        # 1. Define the Schema for the LLM
        # We want strict JSON output matching our Pydantic model
        schema = ExtractedBrandInfo.model_json_schema()

        prompt = f"""
        You are a Brand Identity Expert. Extract specific brand guidelines from the provided PDF text.
        
        I need you to extract:
        1. Brand Name
        2. Colors (Name, Hex, RGB, CMYK, Usage context)
        3. Typography rules (Family, Weights, Use Case)
        4. Logo Usage Rules (Do's and Don'ts)
        5. Negative/Forbidden keywords (e.g. "don't be aggressive")
        
        Return ONLY valid JSON matching this schema:
        {json.dumps(schema)}
        
        --- TEXT START ---
        {text[:15000]} # Truncate to avoid context window limits if too large
        --- TEXT END ---
        """

        try:
            # Drop-in replacement for OpenAI, Gemini, etc.
            # User sets 'LLM_MODEL' in .env (e.g. "gemini/gemini-pro", "gpt-4")
            model = os.getenv("LLM_MODEL", "gpt-3.5-turbo")
            print(f"Using Model: {model}")

            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Fallback to OPENAI_API_KEY if using openai
                api_key = os.getenv("OPENAI_API_KEY")

            response = completion(
                model=model,
                api_key=api_key,
                messages=[{"content": prompt, "role": "user"}],
                response_format={
                    "type": "json_object"
                },  # Ensure JSON mode if supported
                custom_llm_provider="gemini",  # [FIX] Force usage of Google AI Studio
            )

            content = response.choices[0].message.content

            # Parse JSON
            data = json.loads(content)
            return ExtractedBrandInfo(**data)

        except Exception as e:
            print(f"LLM Extraction Failed: {e}")
            print("Falling back to Mock/Empty data.")
            return ExtractedBrandInfo(brand_name="Unknown (Extraction Failed)")

    def extract_guidelines(self, pdf_path: str) -> ExtractedBrandInfo:
        # 1. OCR
        print(f"Extracting text from {pdf_path}...")
        raw_text = self.extract_text_from_pdf(pdf_path)

        if not raw_text:
            return ExtractedBrandInfo(brand_name="Error: No Text Found")

        # 2. LLM Parse
        return self._call_llm(raw_text)
