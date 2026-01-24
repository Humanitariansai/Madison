import sys
from .brand_auditor import IntegratedBrandAuditor

# Mock Data
mock_bible = {
    "rich_colors": [
        {"name": "Core Aubergine", "rgb": [74, 21, 75]}, # Slack Purple
        {"name": "White", "rgb": [255, 255, 255]}
    ],
    "primary_colors": ["#4A154B", "#FFFFFF"], # Fallback
    "brand_voice_attributes": [],
    "frequent_keywords": []
}

mock_assets = [] # Not needed for this unit test

print("Initializing Auditor...")
auditor = IntegratedBrandAuditor(mock_bible, mock_assets)

print("\n--- TEST 1: COMPLIANT COLOR (Near Purple) ---")
# [80, 25, 80] is slightly off [74, 21, 75] but should pass tolerance of 60
status, msg = auditor._check_palette_compliance([[80, 25, 80]])
print(f"Status: {status} | Msg: {msg}")
if status != "PASS":
    print("FAILED: Expected PASS")
    sys.exit(1)

print("\n--- TEST 2: VIOLATION (Neon Green) ---")
# [0, 255, 0] is very far from Purple or White
status, msg = auditor._check_palette_compliance([[0, 255, 0]])
print(f"Status: {status} | Msg: {msg}")
if status != "FAIL":
    print("FAILED: Expected FAIL")
    sys.exit(1)

print("\n--- TEST 3: STRINGS IN RGB (Parsing Logic) ---")
auditor.bible['rich_colors'] = [{"name": "Test", "rgb": "100-100-100"}]
status, msg = auditor._check_palette_compliance([[105, 105, 105]]) # Close to 100
print(f"Status: {status} | Msg: {msg}")
if status != "PASS":
    print("FAILED: Parsing Logic for String RGB failed")
    sys.exit(1)

print("\n>>> ALL TESTS PASSED")
