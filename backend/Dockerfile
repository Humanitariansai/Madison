# Use an official Python runtime as a parent image
# ARM64 compatible (works on M1/M2/M3 Macs)
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for pdf2image and opencv
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy the project configuration and source code
COPY pyproject.toml .
COPY src/ src/

# Install the dependencies
# using pip to install the package in editable mode or just dependencies
RUN pip install --no-cache-dir .

# Expose the port the app runs on
EXPOSE 8000

ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
