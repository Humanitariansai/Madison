"""
Google Cloud Storage helpers for file upload/download.
Only used when STORAGE_TYPE=gcs (i.e. on Cloud Run).
Falls back gracefully if google-cloud-storage is not installed.
"""
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

GCS_BUCKET = os.getenv("GCS_BUCKET", "")  # e.g. project-id-survey-analysis-files
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "local")

try:
    from google.cloud import storage as gcs
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("google-cloud-storage not installed; GCS upload/download disabled.")


def is_gcs_enabled() -> bool:
    return STORAGE_TYPE == "gcs" and GCS_AVAILABLE and bool(GCS_BUCKET)


def upload_to_gcs(local_path: str, blob_name: str) -> str:
    """
    Upload a local file to GCS.
    Returns the gs:// URI on success, raises on failure.
    """
    client = gcs.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(local_path)
    uri = f"gs://{GCS_BUCKET}/{blob_name}"
    logger.info(f"GCS upload: {local_path} -> {uri}")
    return uri


def download_from_gcs(blob_name: str, local_path: str) -> str:
    """
    Download a GCS blob to a local path.
    Returns local_path on success, raises on failure.
    """
    client = gcs.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    Path(local_path).parent.mkdir(parents=True, exist_ok=True)
    blob.download_to_filename(local_path)
    logger.info(f"GCS download: gs://{GCS_BUCKET}/{blob_name} -> {local_path}")
    return local_path


def delete_from_gcs(blob_name: str) -> None:
    """Delete a blob from GCS. Silently ignores not-found errors."""
    try:
        client = gcs.Client()
        bucket = client.bucket(GCS_BUCKET)
        blob = bucket.blob(blob_name)
        blob.delete()
        logger.info(f"GCS delete: gs://{GCS_BUCKET}/{blob_name}")
    except Exception as e:
        logger.warning(f"GCS delete failed (ignored): {e}")


def gcs_blob_name_for_upload(user_id: int, file_hash: str, filename: str) -> str:
    """Deterministic GCS blob path for an uploaded file."""
    return f"uploads/{user_id}/{file_hash[:8]}_{filename}"
