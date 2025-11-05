.PHONY: test test-v test-cov clean

# Default Python interpreter and pytest from virtualenv
PYTHON := /Users/zlatan/Desktop/Work/Madison/.venv/bin/python
PYTEST := /Users/zlatan/Desktop/Work/Madison/.venv/bin/pytest

# Test commands
test:
	$(PYTEST)

test-v:
	$(PYTEST) -v

test-cov:
	$(PYTEST) -v --cov=src

# Run specific test file
test-file:
	pytest $(file) -v

# Clean up Python cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name "*.egg" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".coverage" -delete
	find . -type f -name ".coverage" -delete