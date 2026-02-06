import requests
import time
from concurrent.futures import ThreadPoolExecutor

# CONFIGURATION
URL = "http://localhost:8000/brandkit"  # Check your exact URL
PDF_FILENAME = (
    "../slack_brand_guidelines_september2020.pdf"  # The file you want to send
)
CONCURRENT_USERS = 20  # Simulating 20 people at once
TOTAL_REQUESTS = 100  # Total uploads to attempt

# 1. Load the PDF into memory ONCE (so we test network/API, not your disk speed)
try:
    with open(PDF_FILENAME, "rb") as f:
        pdf_bytes = f.read()
    print(f"Loaded {len(pdf_bytes)} bytes from {PDF_FILENAME}")
except FileNotFoundError:
    print(f"Error: Could not find {PDF_FILENAME}. Please create a dummy pdf.")
    exit()


def send_request(i):
    # We send the cached bytes every time
    # This matches the schema: files, id, title
    files = {"files": (PDF_FILENAME, pdf_bytes, "application/pdf")}
    data = {"id": f"bench_{i}", "title": f"Stress Test {i}"}

    start = time.time()
    try:
        # requests handles the multipart boundaries automatically
        resp = requests.post(URL, files=files, data=data)
        elapsed = time.time() - start
        return resp.status_code, elapsed
    except Exception as e:
        return 500, 0


print(
    f"Starting benchmark: {TOTAL_REQUESTS} reqs with {CONCURRENT_USERS} concurrency..."
)

# 2. Run the Load Test
with ThreadPoolExecutor(max_workers=CONCURRENT_USERS) as executor:
    results = list(executor.map(send_request, range(TOTAL_REQUESTS)))

# 3. Calculate Stats
successes = [r for r in results if r[0] in [200, 201, 202]]
avg_time = sum(r[1] for r in results) / len(results)

print(f"--- RESULTS ---")
print(f"Success Rate: {len(successes)}/{TOTAL_REQUESTS}")
print(f"Avg Latency: {avg_time:.4f} seconds")
