from unittest.mock import MagicMock, patch

import pytest

from src.layout_classifier import (
    LayoutClassifierFactory,
    LayoutType,
    PageLayout,
    PyMuPDFLayoutClassifier,
)


# --- 1. Factory Tests ---
@patch.dict("sys.modules", {"pymupdf": MagicMock()})
def test_factory_get_pymupdf():
    # We must patch sys.modules so the import inside __init__ works
    classifier = LayoutClassifierFactory.get_classifier("pymupdf")
    assert isinstance(classifier, PyMuPDFLayoutClassifier)


def test_factory_invalid_name():
    with pytest.raises(ValueError):
        LayoutClassifierFactory.get_classifier("invalid_name")


# --- 2. PyMuPDF Tests ---
@patch.dict(
    "sys.modules",
    {
        "pymupdf": MagicMock(),
    },
)
def test_pymupdf_analyze_page():
    # Retrieve the mock that we just injected
    import pymupdf

    mock_pymupdf = pymupdf

    # Setup mock document structure
    mock_doc = MagicMock()
    mock_page = MagicMock()
    mock_pymupdf.open.return_value = mock_doc
    mock_doc.__len__.return_value = 1
    mock_doc.__getitem__.return_value = mock_page

    # Mock page content
    mock_page.rect.width = 100
    mock_page.rect.height = 200

    # Mock OCR (disabled for this test - returns None)
    mock_page.get_textpage_ocr.return_value = None

    # Mock text blocks
    # PyMuPDF "get_text('dict')" structure
    mock_page.get_text.return_value = {
        "blocks": [
            {
                "type": 0,  # Text
                "bbox": (10, 10, 50, 20),
                "lines": [{"spans": [{"text": "Title Text", "size": 25.0}]}],
            },
            {
                "type": 0,  # Text
                "bbox": (10, 30, 50, 40),
                "lines": [{"spans": [{"text": "Body Text", "size": 12.0}]}],
            },
            {
                "type": 1,  # Image
                "bbox": (10, 50, 50, 80),
                "image": b"fake_image_bytes",
            },
        ]
    }

    classifier = PyMuPDFLayoutClassifier()
    result = classifier.analyze_page(0, "dummy.pdf")

    assert isinstance(result, PageLayout)
    assert len(result.regions) == 3

    # Check classification heuristics
    assert result.regions[0].type == LayoutType.TITLE
    assert result.regions[1].type == LayoutType.TEXT
    assert result.regions[2].type == LayoutType.FIGURE


@patch.dict("sys.modules", {"pymupdf": MagicMock()})
def test_pymupdf_invalid_page_index():
    import pymupdf

    mock_pymupdf = pymupdf

    mock_doc = MagicMock()
    mock_pymupdf.open.return_value = mock_doc
    mock_doc.__len__.return_value = 1  # Only 1 page

    classifier = PyMuPDFLayoutClassifier()

    with pytest.raises(ValueError, match="out of range"):
        classifier.analyze_page(5, "dummy.pdf")
