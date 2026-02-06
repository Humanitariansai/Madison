import pytest

from src.brand_auditor import IntegratedBrandAuditor


@pytest.fixture
def base_auditor():
    """Fixture to provide a configured auditor instance."""
    mock_bible = {
        "rich_colors": [
            {"name": "Core Aubergine", "rgb": [74, 21, 75]},  # Slack Purple
            {"name": "White", "rgb": [255, 255, 255]},
        ],
        "colors": [
            {"name": "Core Aubergine", "rgb": [74, 21, 75], "hex": "#4A154B"},
            {"name": "White", "rgb": [255, 255, 255], "hex": "#FFFFFF"},
        ],
        "primary_colors": ["#4A154B", "#FFFFFF"],
        "brand_voice_attributes": [],
        "frequent_keywords": [],
    }
    mock_assets = []
    return IntegratedBrandAuditor(mock_bible, mock_assets)


def test_compliant_color(base_auditor):
    """Test a color that is within tolerance of the brand palette."""
    # [80, 25, 80] is close to [74, 21, 75]
    status, msg = base_auditor._check_palette_compliance([[80, 25, 80]])
    assert status == "PASS", f"Expected PASS, got {status}: {msg}"


def test_violation_color(base_auditor):
    """Test a color that is clearly outside the brand palette."""
    # Neon Green [0, 255, 0] vs Purple/White
    status, msg = base_auditor._check_palette_compliance([[0, 255, 0]])
    assert status == "FAIL", f"Expected FAIL, got {status}: {msg}"


def test_string_rgb_parsing():
    """Test parsing of non-standard RGB string formats."""
    mock_bible = {
        "rich_colors": [{"name": "Test", "rgb": "100-100-100"}],
        "colors": [{"name": "Test", "rgb": "100-100-100", "hex": "#646464"}],
        "primary_colors": [],
        "brand_voice_attributes": [],
        "frequent_keywords": [],
    }
    auditor = IntegratedBrandAuditor(mock_bible, [])

    # [105, 105, 105] is close to [100, 100, 100]
    status, msg = auditor._check_palette_compliance([[105, 105, 105]])
    assert status == "PASS", "Parsing logic for String RGB failed"
