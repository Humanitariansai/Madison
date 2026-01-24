from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from typography.auditor import TypographyAuditor


@pytest.fixture
def mock_manager():
    manager = MagicMock()
    # Mock load_kit_embeddings to return something truthy
    manager.load_kit_embeddings.return_value = {"font": "embedding"}
    return manager


@pytest.fixture
def auditor(mock_manager):
    return TypographyAuditor(mock_manager)


@pytest.fixture
def mock_page_image():
    # Create a dummy image
    return Image.new("RGB", (1000, 1000), color="white")


def test_audit_page_empty(auditor, mock_page_image):
    """Test that an empty page returns no violations."""
    with patch("pytesseract.image_to_data") as mock_ocr:
        # Mock empty OCR result
        mock_ocr.return_value = {
            "level": [],
            "page_num": [],
            "block_num": [],
            "par_num": [],
            "line_num": [],
            "word_num": [],
            "left": [],
            "top": [],
            "width": [],
            "height": [],
            "conf": [],
            "text": [],
        }

        results = auditor.audit_page(mock_page_image, "kit_1", ["Arial"])
        assert len(results) == 0


def test_block_detection_and_hierarchy(auditor, mock_page_image):
    """Test that blocks are detected and classified as Header/Body based on size."""
    with (
        patch("pytesseract.image_to_data") as mock_ocr,
        patch.object(auditor, "_audit_crop") as mock_audit_crop,
    ):
        # Setup OCR data:
        # Block 1: Large text (Height 60) -> Should be HEADER (median is ~20)
        # Block 2: Small text (Height 20) -> Should be BODY
        mock_ocr.return_value = {
            "level": [5, 5],
            "block_num": [1, 2],
            "text": ["Big Title", "Small body"],
            "left": [10, 10],
            "top": [10, 100],
            "width": [200, 200],
            "height": [60, 20],  # Key differentiator
            "conf": [90, 90],
        }

        # Setup Classifier responses
        # Block 1 (Header) -> Returns "Larsseit" (Allowed)
        # Block 2 (Body) -> Returns "Comic Sans" (Not Allowed)
        mock_audit_crop.side_effect = [
            {"detected_font": "Larsseit", "confidence": 0.9},
            {"detected_font": "Comic Sans", "confidence": 0.9},
        ]

        results = auditor.audit_page(mock_page_image, "kit_1", ["Larsseit"])

        assert len(results) == 2

        # Verify Block 1 (Header)
        header_result = results[0]
        assert "HEADER" in header_result["metric"]
        assert header_result["status"] == "PASS"
        assert "Larsseit" in header_result["metric"]

        # Verify Block 2 (Body)
        body_result = results[1]
        assert "BODY" in body_result["metric"]
        assert body_result["status"] == "FAIL"
        assert "Comic Sans" in body_result["metric"]


def test_audit_unknown_font(auditor, mock_page_image):
    """Test behavior when font is unknown."""
    with (
        patch("pytesseract.image_to_data") as mock_ocr,
        patch.object(auditor, "_audit_crop") as mock_audit_crop,
    ):
        # Single block
        mock_ocr.return_value = {
            "level": [5],
            "block_num": [1],
            "text": ["Text"],
            "left": [10],
            "top": [10],
            "width": [100],
            "height": [50],
            "conf": [90],
        }

        # Classifier returns unknown
        mock_audit_crop.return_value = {"detected_font": "unknown", "confidence": 0.0}

        # Run audit
        results = auditor.audit_page(mock_page_image, "kit_1", ["Arial"])

        # Current logic: Unknown is treated as WARNING
        # if it's a Header (size 50 vs median 50?
        # No, median is 50, so 50 is not > 1.3*50. It's BODY)
        # Wait, if only 1 block, median = 50. Threshold = 65. Block is 50.
        # So it is BODY.
        # Logic says: "if role == 'HEADER': warn". Else ignore?
        # Let's verify the code logic. If unknown and BODY, it might return nothing?

        # Actually, let's force it to be a HEADER by adding a small block too.
        mock_ocr.return_value = {
            "level": [5, 5],
            "block_num": [1, 2],
            "text": ["Header", "Small"],
            "left": [10, 10],
            "top": [10, 100],
            "width": [100, 100],
            "height": [
                50,
                10,
            ],  # Median = (50+10)/2 = 30. Threshold = 39. 50 is Header.
            "conf": [90, 90],
        }

        mock_audit_crop.side_effect = [
            {"detected_font": "unknown", "confidence": 0.0},  # Header
            {"detected_font": "Arial", "confidence": 0.9},  # Body
        ]

        results = auditor.audit_page(mock_page_image, "kit_1", ["Arial"])

        # Should have 2 results. Header -> Warning. Body -> Pass.
        assert len(results) == 2
        assert results[0]["status"] == "WARNING"
        assert "Could not identify" in results[0]["metric"]
