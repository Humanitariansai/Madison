# 🚀 Launch Checklist

## Pre-Launch
- [ ] Verify `.env` file contains valid API keys and database credentials.
- [ ] Ensure MongoDB is running and accessible.
- [ ] Run `python tests/test_integration.py` to validate all components.
- [ ] Populate database with sample data (`sample_datasets/sample_posts.csv`).

## Launch
- [ ] Start the API server:
  ```bash
  uvicorn api.main:app --reload
  ```
- [ ] Start the webhook server:
  ```bash
  uvicorn api.webhooks:app --reload
  ```
- [ ] Test API endpoints and webhook flows.

## Post-Launch
- [ ] Monitor logs for errors.
- [ ] Collect user feedback.
- [ ] Plan next sprint for feature enhancements.