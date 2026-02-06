import json
import logging
import os
import sys
import time
from typing import List, Optional

import pymupdf
from litellm import completion, get_max_tokens, token_counter
from pydantic import BaseModel

# --- Data Models ---

root_logger = logging.getLogger("src")
root_logger.setLevel(logging.DEBUG)

if not root_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    root_logger.addHandler(handler)
    root_logger.propagate = (
        False  # Prevent double logging if uvicorn captures it too? Try False first.
    )

logger = logging.getLogger(__name__)


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


class ColorUsageRule(BaseModel):
    background_color: str  # e.g., "Aubergine"
    allowed_text_colors: List[str]  # e.g., ["White"]
    forbidden_text_colors: List[str]  # e.g., ["Black", "Secondary Colors"]
    context_description: str  # The extracted text specific to this rule


class BrandVoiceRule(BaseModel):
    attributes: List[str]
    frequent_keywords: List[str]
    forbidden_keywords: List[str]


class ExtractedBrandInfo(BaseModel):
    brand_name: Optional[str] = None
    colors: List[BrandColor] = []
    typography: List[BrandTypography] = []
    logo_rules: List[BrandLogoRule] = []
    color_usage_rules: List[ColorUsageRule] = []  # New Field
    brand_voice: BrandVoiceRule = BrandVoiceRule(
        attributes=[], frequent_keywords=[], forbidden_keywords=[]
    )


class BrandGuidelineExtractor:
    """
    Extracts brand guidelines from PDF files using OCR + LLM parsing.

    CONTEXT WINDOW CONSIDERATIONS:
    ==============================
    Current implementation is optimized for Gemini Flash (1M token context).

    Limits:
    - Max Pages: 200 (can process most brand guideline PDFs)
    - Max Characters: 500,000 (~750K tokens safe limit for Gemini Flash)

    This works for 99% of brand guideline PDFs. If you encounter limits:

    FUTURE ENHANCEMENT (if needed):
    - Implement page-range chunking (process PDF in chunks of 10-20 pages)
    - Add _merge_extracted_results() to combine results from multiple chunks
    - Deduplicate colors, typography, and rules across chunks
    - See implementation_plan.md in conversation artifacts for full design

    Other Models:
    - GPT-4: 128K tokens (~100K chars) - would need chunking for large PDFs
    - GPT-3.5: 16K tokens (~12K chars) - definitely needs chunking
    """

    def __init__(self):
        logger.info("Initializing BrandGuidelineExtractor service")
        # In a real app, initialize LLM client here (e.g. OpenAI / Gemini)

    def _truncate_to_token_limit(self, text: str, model: str) -> str:
        """
        Truncates text to fit within the model's token limit.

        Args:
            text: Input text to truncate
            model: Model identifier

        Returns:
            Truncated text that fits within token limit
        """

        # Get model's max tokens from LiteLLM (uses their maintained database)
        try:
            max_tokens = get_max_tokens(model)
            # Use 75% for safety margin (prompt overhead, response, etc.)
            token_limit = int(max_tokens * 0.75)
        except Exception as e:
            token_limit = 6000
            max_tokens = 8192  # Approximate default for display
            logger.warning(
                f"Could not get max tokens for {model}: {e}. "
                f"Using default {token_limit} tokens."
            )

        # Count actual tokens
        try:
            actual_tokens = token_counter(model=model, text=text)
            logger.info(
                f"Input text token count: {actual_tokens:,} (limit: {token_limit:,}"
                f" | model max: {max_tokens:,})"
            )

            # If within limit, return as-is
            if actual_tokens <= token_limit:
                return text

            # Truncate to fit (rough estimate: 1 token ≈ 4 chars)
            chars_to_keep = int((token_limit / actual_tokens) * len(text))
            truncated_text = text[:chars_to_keep]

            # Verify truncation worked
            truncated_tokens = token_counter(model=model, text=truncated_text)
            logger.warning(
                f"Truncated input text to {truncated_tokens:,} "
                f"tokens ({len(truncated_text):,} chars)"
            )

            return truncated_text

        except Exception as e:
            # Fallback to character-based truncation if token counting fails
            logger.warning(
                f"Token counting failed: {e}. Using character-based truncation."
            )
            chars_limit = token_limit * 4  # Rough estimate
            return text[:chars_limit]

    def extract_text_from_pdf(self, pdf_path: str, max_pages: int = 200) -> str:
        """
        Extracts text from PDF using PyMuPDF (fitz) for speed and accuracy.

        Args:
            pdf_path: Path to the PDF file
            max_pages: Maximum pages to process (default: 200)

        Returns:
            Concatenated text from all pages with page markers
        """
        try:
            full_text = ""
            doc = pymupdf.open(pdf_path)
            # Iterate through pages (up to max_pages)
            for i, page in enumerate(doc.pages(stop=max_pages)):
                # 1. Try Native Extraction first (Fast)
                text = page.get_text()

                # 2. If mostly empty, fallback to OCR (Slow)
                if len(text.strip()) < 50:
                    logger.info(
                        f"Page {i + 1} seems to be an image scan. Running OCR..."
                    )
                    try:
                        # 300 DPI is a good balance for speed/accuracy
                        text = page.get_textpage_ocr(flags=0, dpi=300).extractText()
                    except Exception as e:
                        logger.warning(f"OCR failed for page {i + 1}: {e}")

                full_text += f"\n--- Page {i + 1} ---\n{text}"

            logger.debug(f"Extracted {len(full_text)} chars from PDF")
            return str(full_text)
        except ImportError:
            logger.error("PyMuPDF not installed. Please install it.")
            return ""
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            return ""

    def _call_llm(self, text: str) -> ExtractedBrandInfo:
        """
        Uses LiteLLM to call ANY supported LLM (OpenAI, Gemini, Anthropic, etc.)
        Provider is determined by 'LLM_MODEL' env var (default: gpt-3.5-turbo).

        RATE LIMIT HANDLING:
        - Automatic retries with exponential backoff on rate limits (429 errors)
        - Max 3 retries with 1s, 2s, 4s delays
        - Helps prevent failures during high API usage
        """

        # Get model first (needed for token counting)
        model = os.getenv("LLM_MODEL", "gemini/gemini-2.0-flash")
        logger.info(f"Parsing extracted text with LLM model: {model} (via LiteLLM)")

        # 1. Define the Schema for the LLM
        # We want strict JSON output matching our Pydantic model
        schema = ExtractedBrandInfo.model_json_schema()

        prompt = f"""
        You are a Brand Identity Expert.
        Extract specific brand guidelines from the provided PDF text.

        I need you to extract:
        1. Brand Name
        2. Colors (Name, Hex, RGB, CMYK, Usage context)
        3. Typography rules (Family, Weights, Use Case)
        4. Logo Usage Rules (Do's and Don'ts) - Logic for logo placement.
        5. TYPOGRAPHY COLOR RULES: Crucial. Look for rules specifying which
            TEXT colors (font colors) are allowed on specific background colors.
           - Example: "Use only white text on Aubergine."
           - Example: "Do not use secondary colors for text."
           - Example: "Black text is for light backgrounds."
        6. Brand Voice Rules (Attributes, frequent keywords, forbidden keywords)

        Return ONLY valid JSON matching this schema:
        {json.dumps(schema)}

        --- TEXT START ---
        {self._truncate_to_token_limit(text, model)}
        --- TEXT END ---
        """

        # Retry configuration for rate limits
        max_retries = 3
        base_delay = 1  # seconds

        for attempt in range(max_retries + 1):
            try:
                # Get API key
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    # Fallback to OPENAI_API_KEY if using openai
                    api_key = os.getenv("OPENAI_API_KEY")

                # pyrefly: ignore [not-callable]
                response = completion(
                    model=model,
                    api_key=api_key,
                    messages=[{"content": prompt, "role": "user"}],
                    response_format={
                        "type": "json_object"
                    },  # Ensure JSON mode if supported
                    custom_llm_provider="gemini",
                )

                content = response.choices[0].message.content

                # Parse JSON
                data = json.loads(content)

                # Robustness: Handle list wrapping
                if isinstance(data, list) and len(data) > 0:
                    data = data[0]

                return ExtractedBrandInfo(**data)

            except Exception as e:
                error_str = str(e).lower()

                # Check if it's a rate limit error
                is_rate_limit = (
                    "rate limit" in error_str
                    or "429" in error_str
                    or "quota" in error_str
                    or "too many requests" in error_str
                )

                # If rate limit and we have retries left, wait and retry
                if is_rate_limit and attempt < max_retries:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    logger.warning(
                        f"Rate limit hit. Retrying in {delay}s "
                        f"(Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    continue

                # Otherwise, fail
                logger.error(f"LLM Extraction Failed: {e}")

        # If we exhausted retries or hit a non-retryable error
        raise ValueError("Failed to extract brand guidelines after retries.")

    def extract_guidelines(self, pdf_path: str) -> ExtractedBrandInfo:
        # 1. OCR
        logger.info(f"Extracting text from PDF: {pdf_path}")
        raw_text = self.extract_text_from_pdf(pdf_path)

        if not raw_text:
            return ExtractedBrandInfo(brand_name="Error: No Text Found")

        # 2. LLM Parse
        return self._call_llm(raw_text)
