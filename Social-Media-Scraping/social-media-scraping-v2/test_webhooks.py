#!/usr/bin/env python3
"""
Test script for webhook endpoints
Run webhook server first:
  cd Social-Media-Scraping/social-media-scraping-v2
  uvicorn api.webhooks:app --reload --port 8002
"""
import requests
import json
import sys

# Test webhook server
BASE_URL = "http://127.0.0.1:8002"

print("🔍 Testing Webhook Endpoints\n")
print("=" * 60)
print(f"Webhook server: {BASE_URL}\n")

# Test 1: Send a webhook event
print("\n1. Testing POST /webhook (send event)")
try:
    payload = {
        "event_type": "scraping_completed",
        "payload": {
            "platform": "reddit",
            "posts_scraped": 25,
            "timestamp": "2025-11-18T12:00:00"
        }
    }
    response = requests.post(f"{BASE_URL}/webhook", json=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: List webhook events
print("\n2. Testing GET /webhook/events")
try:
    response = requests.get(f"{BASE_URL}/webhook/events")
    print(f"   Status: {response.status_code}")
    events = response.json()
    print(f"   Total events: {len(events)}")
    if events:
        print(f"   Latest event: {json.dumps(events[-1], indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Send webhook notification
print("\n3. Testing POST /webhook/notify")
try:
    # Using a webhook testing service
    test_url = "https://webhook.site/unique-id"  # Replace with actual test URL
    payload = {
        "url": test_url,
        "payload": {
            "message": "Test notification from Social Media Scraper",
            "status": "success"
        }
    }
    response = requests.post(f"{BASE_URL}/webhook/notify", json=payload)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("✨ Webhook testing complete!")
print("\nNote: Make sure the webhook server is running:")
print("  cd Social-Media-Scraping/social-media-scraping-v2")
print("  uvicorn api.webhooks:app --reload --port 8002")
