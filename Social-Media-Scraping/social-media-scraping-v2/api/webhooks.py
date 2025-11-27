from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from typing import Dict

app = FastAPI(title="Webhook System", version="1.0")

# Mock database for demonstration purposes
webhook_events = []

class WebhookEvent(BaseModel):
    event_type: str
    payload: Dict

@app.post("/webhook")
def receive_webhook(event: WebhookEvent):
    """Receive and store webhook events."""
    webhook_events.append(event.dict())
    return {"status": "success", "received_event": event}

@app.get("/webhook/events")
def list_webhook_events():
    """List all received webhook events."""
    return webhook_events

@app.post("/webhook/notify")
def send_webhook_notification(url: str, payload: Dict):
    """Send a webhook notification to a specified URL."""
    import requests
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return {"status": "success", "response": response.json()}
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to send webhook: {str(e)}")