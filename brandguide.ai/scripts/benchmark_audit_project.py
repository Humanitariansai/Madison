import requests
import time
from concurrent.futures import ThreadPoolExecutor

MAX_RETRIES = 5  # increased from default 3 just in case

# CONFIGURATION
URL = "http://localhost:8000/project/audit"  # Check your exact URL
PDF_FILENAME = (
    "../slack_brand_guidelines_september2020.pdf"  # The file you want to send
)
VALID_BRAND_KIT_ID = "e6bda711-1649-4676-9eb5-71893909ba37"
CONCURRENT_USERS = 2  # Simulating 20 people at once
TOTAL_REQUESTS = 1  # Total uploads to attempt
try:
    with open(PDF_FILENAME, "rb") as f:
        pdf_bytes = f.read()
    print(f"Loaded {len(pdf_bytes)} bytes from {PDF_FILENAME}")
except FileNotFoundError:
    print(f"Error: Could not find {PDF_FILENAME}. Please create a dummy pdf.")
    exit()


def send_request(i):
    # SCHEMA MAPPING:
    # file -> sent as 'file' param in multipart
    # id, title, brand_kit_id -> sent as form fields
    files = {"file": (PDF_FILENAME, pdf_bytes, "application/pdf")}
    data = {
        "id": f"bench_audit_{i}",
        "title": f"Audit Stress Test {i}",
        "brand_kit_id": str(VALID_BRAND_KIT_ID),
    }

    start = time.time()
    try:
        # Request timeout set to 300s because this endpoint likely blocks
        resp = requests.post(URL, files=files, data=data, timeout=300)
        elapsed = time.time() - start
        if resp.status_code not in [200, 201, 202]:
            print(f"Request {i} failed: {resp.status_code} - {resp.text}")
        return resp.status_code, elapsed
    except Exception as e:
        print(f"Request failed: {e}")
        return 500, 0


print(
    f"Starting Audit benchmark: {TOTAL_REQUESTS} reqs with {CONCURRENT_USERS} concurrency..."
)

# 2. Run the Load Test
with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
    results = list(executor.map(send_request, range(TOTAL_REQUESTS)))

# 3. Calculate Stats
successes = [r for r in results if r[0] in [200, 201, 202]]
avg_time = sum(r[1] for r in results) / len(results) if results else 0

print(f"--- RESULTS ---")
print(f"Success Rate: {len(successes)}/{TOTAL_REQUESTS}")
print(f"Avg Latency: {avg_time:.4f} seconds")
