from unittest.mock import MagicMock, patch

import pytest

from src.layout_classifier import (
    LayoutClassifierFactory,
    LayoutRegion,
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


def test_scaling():
    # 1. Create a dummy layout (72 DPI)
    # Page size: 8.5 x 11 inches = 612 x 792 points
    page_size = (612, 792)

    # Region: Top header
    # bbox: (10, 10, 100, 50)
    region = LayoutRegion(
        id="r1", type=LayoutType.HEADER, bbox=(10, 10, 100, 50), page_number=1
    )

    layout = PageLayout(page_number=1, page_size=page_size, regions=[region])

    print(f"Original Layout: {layout.page_size}")
    print(f"Original Region: {layout.regions[0].bbox}")

    # 2. Simulate 150 DPI Image (approx 2.08x)
    # 8.5 * 150 = 1275
    # 11 * 150 = 1650
    img_w, img_h = 1275, 1650

    scale_x = img_w / page_size[0]
    scale_y = img_h / page_size[1]

    print(f"\nScaling Factors: {scale_x:.4f}, {scale_y:.4f}")

    # 3. Apply Scale
    layout.scale(scale_x, scale_y)

    # 4. Verify
    print(f"\nScaled Layout: {layout.page_size}")
    print(f"Scaled Region: {layout.regions[0].bbox}")

    # Assertions
    assert abs(layout.page_size[0] - 1275) < 0.1
    assert abs(layout.page_size[1] - 1650) < 0.1

    # Expected bbox: (10*scale, 10*scale, 100*scale, 50*scale)
    expected_bbox = (10 * scale_x, 10 * scale_y, 100 * scale_x, 50 * scale_y)

    r_bbox = layout.regions[0].bbox
    assert abs(r_bbox[0] - expected_bbox[0]) < 0.1
    assert abs(r_bbox[1] - expected_bbox[1]) < 0.1
    assert abs(r_bbox[2] - expected_bbox[2]) < 0.1
    assert abs(r_bbox[3] - expected_bbox[3]) < 0.1

    print("\n✅ Scaling Logic Verified!")
