# Backend Logic Report

| Category | Classification (Logic) | Guideline Generation (What is learned) | Auditing (How it is checked) | Gaps / Remaining Work |
| :--- | :--- | :--- | :--- | :--- |
| **1. Logo / Wordmark** | **CLIP**: "logo", "logotype", "plus SVG detection". | **Aspect Ratios**: Extracts w/h ratios.<br>**Variants**: Indexes SIFT features.<br>**Rules**: OCR+LLM extracts Do's/Don'ts text. | **SIFT Matching**: Finds instances via keypoints.<br>**Ratio Check**: ±20% tolerance.<br>**Color Check**: RGB distance avg. | **Clear Space**: Not mathematically enforced.<br>**Text Rules**: We know the rules ("Don't rotate"), but don't visually detect rotation yet. |
| **2. Colors** | N/A (Derived) | **Palette Extraction**: <br>1. **OCR+LLM**: Extracts Exact Hex, CMYK, PMS, and Usage.<br>2. **K-Means**: Fallback pixel clustering. | **None** (Directly).<br>*Current audit checks logo correlation, but not generic shape/text colors against the palette.* | **Enforcement**: We now HAVE the rich data, but the `BrandAuditor` needs to be updated to sample page pixels and validate against the allowed list. |
| **3. Typography** | **CLIP**: "font specimen". | **Font Extraction**: OCR+LLM extracts Family names, Weights, and Usage contexts. | **Visual Font Audit**: Siamese Network (CNN) detects font usage per character.<br>**Tone Check**: Sentiment analysis. | **Granularity**: Currently checks character-level, aggregation to block-level in progress. |
| **4. Imagery** | **CLIP**: "photograph". | **Vibe Keywords**: Extracted from PDF text (e.g. "Humanitarian", "Clean"). | **Vibe Check**: CLIP compares page images against brand keywords.<br>**Quality Check**: Checks against "blurry", "cartoon". | **Object Detection**: No check for specific object usage rules (e.g. "Must include people"). |

## Architecture Summary
*   **Ingestion**: `AssetClassifier` (CLIP) for images, `BrandGuidelineExtractor` (OCR+LLM) for PDFs.
*   **Storage**: `data/store.json` (JSON Persistence).
*   **Audit**: `IntegratedBrandAuditor` (SIFT + CLIP + BART) & `TypographyAuditor` (Siamese Network).
