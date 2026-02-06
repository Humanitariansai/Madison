import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

from PIL import Image
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class LayoutType(str, Enum):
    """
    Standardized layout types for document regions.
    """

    TEXT = "TEXT"
    TITLE = "TITLE"
    SECTION_HEADER = "SECTION_HEADER"
    CAPTION = "CAPTION"
    LIST_ITEM = "LIST_ITEM"
    TABLE = "TABLE"
    FIGURE = "FIGURE"  # Generic image/figure
    LOGO = "LOGO"  # Specific logo (detected by specialized models if possible)
    FORMULA = "FORMULA"
    FOOTER = "FOOTER"
    HEADER = "HEADER"
    PAGE_NUMBER = "PAGE_NUMBER"
    UNKNOWN = "UNKNOWN"


class LayoutRegion(BaseModel):
    """
    A single region detected in a document page.
    """

    id: str | None = None
    type: LayoutType
    bbox: tuple[float, float, float, float]  # (x0, y0, x1, y1)
    confidence: float = 1.0
    content: Any | None = None  # The extracted text or image crop
    page_number: int = 1

    # Optional metadata from specific engines
    metadata: dict[str, Any] = {}

    def get_area(self) -> float:
        return (self.bbox[2] - self.bbox[0]) * (self.bbox[3] - self.bbox[1])


class PageLayout(BaseModel):
    """
    Complete layout analysis for a single page.
    """

    page_number: int
    page_size: tuple[float, float]  # (width, height)
    regions: list[LayoutRegion]

    def get_regions_by_type(self, region_type: LayoutType) -> list[LayoutRegion]:
        return [r for r in self.regions if r.type == region_type]


class LayoutClassifier(ABC):
    """
    Abstract base class for layout classification engines.
    """

    @abstractmethod
    def analyze_page(
        self, page_input: str | Image.Image | int, pdf_path: str | None = None
    ) -> PageLayout:
        """
        Analyze a single page and return its layout regions.

        Args:
            page_input: Can be an image (PIL), path to image, or page number
            (for PDF-based extractors like PyMuPDF)
            pdf_path: Path to the original PDF (required for PyMuPDF,
            optional for Vision models)

        Returns:
            PageLayout containing all detected regions.
        """
        pass


class PyMuPDFLayoutClassifier(LayoutClassifier):
    """
    Layout classifier using PyMuPDF (fitz).
    Fast, heuristic-based, good for digital PDFs.
    """

    # Font size thresholds for layout classification
    TITLE_FONT_SIZE = 20  # Font size above which text is considered a title
    HEADER_FONT_SIZE = 14  # Font size above which text is considered a section header

    # Position-based thresholds (as ratio of page height)
    HEADER_POSITION_RATIO = 0.1  # Top 10% of page
    FOOTER_POSITION_RATIO = 0.9  # Bottom 10% of page
    LOGO_POSITION_RATIO = 0.3  # Top 30% of page for logo detection

    # Text length threshold for logo detection
    LOGO_TEXT_MAX_LENGTH = 50  # Max characters for text to be considered a logo

    def __init__(self) -> None:
        try:
            import pymupdf

            self.pymupdf = pymupdf
        except ImportError:
            raise ImportError(
                "PyMuPDF is not installed. Please run `pip install pymupdf`."
            )

    def analyze_page(
        self, page_input: str | Image.Image | int, pdf_path: str | None = None
    ) -> PageLayout:
        if not pdf_path:
            raise ValueError(
                "PyMuPDFLayoutClassifier requires 'pdf_path' to be provided."
            )

        if not isinstance(page_input, int):
            if isinstance(page_input, str) and page_input.isdigit():
                page_input = int(page_input)
            else:
                logger.warning(
                    "PyMuPDF requires page index. Defaulting to page 0 if not provided."
                )
                page_input = 0

        doc = self.pymupdf.open(pdf_path)
        # 0-indexed page
        if page_input >= len(doc):
            raise ValueError(f"Page {page_input} out of range for {pdf_path}")

        page = doc[page_input]
        rect = page.rect
        width, height = rect.width, rect.height

        # Get text blocks using PyMuPDF's native extraction
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])

        # Try to use PyMuPDF's native OCR for fallback/enhancement
        # This uses Tesseract via PyMuPDF's built-in integration
        textpage_ocr = None
        try:
            textpage_ocr = page.get_textpage_ocr()
            logger.debug(f"OCR textpage created for page {page_input}")
        except Exception as e:
            logger.warning(f"OCR failed for page {page_input}: {e}")

        regions = []

        # Process PyMuPDF blocks
        for i, block in enumerate(blocks):
            # block['bbox'] is (x0, y0, x1, y1)
            bbox = block["bbox"]
            x0, y0, x1, y1 = bbox  # Extract coordinates for use in heuristics

            # Simple heuristic for type
            # 'type' key in PyMuPDF: 0=text, 1=image
            block_type = block.get("type", 0)

            if block_type == 1:
                # Image block - try OCR on this region
                layout_type = LayoutType.FIGURE
                content = block.get("image", b"")  # Image bytes

                # If OCR textpage is available, try to extract text from this region
                if textpage_ocr:
                    try:
                        # Extract text from OCR textpage using the bbox
                        ocr_text = page.get_text(
                            "text", clip=bbox, textpage=textpage_ocr
                        ).strip()
                        if ocr_text:
                            content = ocr_text
                            # Heuristic: if text is short and near top, might be logo
                            if (
                                len(ocr_text) < self.LOGO_TEXT_MAX_LENGTH
                                and y0 < height * self.LOGO_POSITION_RATIO
                            ):
                                layout_type = LayoutType.LOGO
                    except Exception as e:
                        logger.debug(f"OCR on image block failed: {e}")

            else:
                # Text block logic
                # Heuristic: Check font size for Header/Title
                text_content = ""
                max_size = 0.0

                # Iterate lines/spans to find text and max font size
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text_content += span["text"] + " "
                            if span["size"] > max_size:
                                max_size = span["size"]

                text_content = text_content.strip()

                # If PyMuPDF didn't extract text, try OCR textpage fallback
                if not text_content and textpage_ocr:
                    try:
                        text_content = page.get_text(
                            "text", clip=bbox, textpage=textpage_ocr
                        ).strip()
                    except Exception as e:
                        logger.debug(f"OCR fallback failed: {e}")

                # Determine type based on font size/position
                # Enhanced heuristics
                if max_size > self.TITLE_FONT_SIZE:
                    layout_type = LayoutType.TITLE
                elif max_size > self.HEADER_FONT_SIZE:
                    layout_type = LayoutType.SECTION_HEADER
                elif y0 < height * self.HEADER_POSITION_RATIO:  # Top of page
                    layout_type = LayoutType.HEADER
                elif y0 > height * self.FOOTER_POSITION_RATIO:  # Bottom of page
                    layout_type = LayoutType.FOOTER
                else:
                    layout_type = LayoutType.TEXT

                content = text_content

            regions.append(
                LayoutRegion(
                    id=f"block_{i}",
                    type=layout_type,
                    bbox=bbox,
                    confidence=1.0,  # PyMuPDF is deterministic
                    content=content,
                    page_number=page_input + 1,
                )
            )

        doc.close()

        return PageLayout(
            page_number=page_input + 1, page_size=(width, height), regions=regions
        )


class SuryaLayoutClassifier(LayoutClassifier):
    """
    Layout classifier using Surya OCR (segformer-based).

    NOTE: This is a STUB implementation for future development.

    TODO: Complete implementation requires:
    1. Proper surya-layout model integration (not just text detection)
    2. Correct bbox format handling (polygon vs rectangle)
    3. Layout type classification (TITLE, HEADER, TABLE, etc.)
    4. Page number tracking from input
    5. Confidence score extraction
    6. Error handling for various image formats
    7. Caching for PDF page conversions

    References:
    - Surya Layout: https://github.com/VikParuchuri/surya
    - Expected API: batch_layout_detection() for layout analysis
    - Current implementation only has text detection scaffolding
    """

    def __init__(self, device: str = "cpu") -> None:
        """
        Initialize Surya layout classifier.

        Args:
            device: Device to run inference on ("cpu" or "cuda")

        Raises:
            ImportError: If surya-ocr is not installed
        """
        try:
            # Verify surya is available but don't load models yet
            import surya  # noqa: F401

            self.device = device
            self._model = None
            self._processor = None

            logger.info(
                "SuryaLayoutClassifier initialized (stub mode). "
                "Full implementation pending."
            )
        except ImportError:
            raise ImportError(
                "Surya OCR is not installed. Please run `pip install surya-ocr`."
            )

    def analyze_page(
        self, page_input: str | Image.Image | int, pdf_path: str | None = None
    ) -> PageLayout:
        """
        Analyze a single page and return its layout regions.

        NOTE: This is a stub implementation that raises NotImplementedError.

        Args:
            page_input: Can be an image (PIL), path to image, or page number
            pdf_path: Path to the original PDF (required if page_input is int)

        Returns:
            PageLayout containing all detected regions

        Raises:
            NotImplementedError: This implementation is not yet complete

        TODO: Implement the following:
        1. Load image from various input types (int/str/Image)
        2. Run surya.layout.batch_layout_detection()
        3. Parse layout regions with proper types (TITLE, HEADER, TABLE, etc.)
        4. Extract bounding boxes in correct format
        5. Map surya layout types to LayoutType enum
        6. Handle confidence scores
        7. Track actual page numbers
        """
        raise NotImplementedError(
            "SuryaLayoutClassifier is a stub implementation. "
            "To implement:\n"
            "1. Install surya-layout model\n"
            "2. Implement image loading from page_input\n"
            "3. Run batch_layout_detection() with proper model\n"
            "4. Parse results into LayoutRegion objects\n"
            "5. Map surya types to LayoutType enum\n"
            "\n"
            "For now, use PyMuPDFLayoutClassifier instead:\n"
            "  classifier = LayoutClassifierFactory.get_classifier('pymupdf')"
        )


class LayoutClassifierFactory:
    @staticmethod
    def get_classifier(name: str = "pymupdf") -> LayoutClassifier:
        if name.lower() == "pymupdf":
            return PyMuPDFLayoutClassifier()
        elif name.lower() == "surya":
            return SuryaLayoutClassifier()
        else:
            raise ValueError(f"Unknown classifier: {name}")
