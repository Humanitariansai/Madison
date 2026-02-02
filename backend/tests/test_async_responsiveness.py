import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from src.api import app


# MOCK PROCESSING FUNCTION
def mock_slow_process(*args, **kwargs):
    """Simulates a heavy blocking task that sleeps for 2 seconds."""
    print("\n[MOCK] Starting slow job (2s)...")
    time.sleep(2)  # BLOCKING sleep (simulates heavy CPU work)
    print("[MOCK] Job finished.")
    return [], 10  # Return empty results, 10 pages


@pytest.mark.asyncio
async def test_endpoint_concurrency():
    """
    Verify that the API can handle a lightweight request
    WHILE a heavy blocking task is running in the background.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        # Let's mock the session dependency to return a fake BrandKit
        with patch("src.api.get_session") as mock_get_session:
            # Mock BrandKit response
            mock_kit = MagicMock()
            mock_kit.id = "test_kit_123"
            mock_kit.brand_name = "Test Brand"
            mock_kit.assets = []
            mock_kit.colors = []
            mock_kit.typography = []
            mock_kit.logo_rules = {}
            mock_kit.brand_voice = {}

            # Setup session mock
            mock_session = MagicMock()
            mock_session.exec.return_value.first.return_value = mock_kit
            # Async mock adjustments
            async_mock = MagicMock()
            async_mock.__aenter__.return_value = mock_session
            mock_get_session.return_value = async_mock

            # 2. Patch the Worker Function to be Slow
            with patch("src.api._process_audit_job", side_effect=mock_slow_process):
                print("\n--> Starting Async Verification Test")

                # Task A: The Heavy Audit (Should take 2s)
                # We need to pass valid-looking form data
                pdf_content = b"%PDF-1.4 mock content"
                audit_task = asyncio.create_task(
                    ac.post(
                        "/project/audit",
                        data={
                            "id": "proj_123",
                            "title": "Concurrency Test",
                            "brand_kit_id": "test_kit_123",
                        },
                        files={"file": ("test.pdf", pdf_content, "application/pdf")},
                    )
                )

                # Give it a tiny moment to start
                await asyncio.sleep(0.1)

                # Task B: The Light Check (Should be instant)
                start_time = time.time()

                await ac.get("/docs")
                duration = time.time() - start_time

                print(f"--> Light Request returned in {duration:.4f} seconds")

                # 3. Assertions
                if duration < 1.0:
                    print("SUCCESS: API responded instantly while audit was running!")
                else:
                    print("FAILURE: API was blocked by the audit task.")

                assert duration < 1.0, f"API blocked for {duration}s (expected < 1s)"

                # Clean up audit task
                try:
                    await audit_task
                except Exception:
                    pass
