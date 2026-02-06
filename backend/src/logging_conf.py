import sys
from logging.config import dictConfig

# Usage:
# 1. In api.py:
#    from .logging_conf import configure_logging
#    configure_logging()
# 2. In other files:
#    logger = logging.getLogger(__name__)


def configure_logging():
    """
    Configures logging for the application.
    - Sets Uvicorn loggers to use our format.
    - Sets root logger to capture everything.
    - Handles third-party log noise (SQLAlchemy, PIL).
    """
    LOG_CONFIG = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                # Could use python-json-logger here for true JSON
                "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "default",
                "level": "DEBUG",
            },
        },
        "loggers": {
            # Root Logger
            "": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": True,
            },
            # Application Logger
            "src": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": False,  # Prevent double logging if root also captures
            },
            # Uvicorn (Override to match our format)
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.error": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            # Third Party - Reduce Noise
            "PIL": {"level": "WARNING"},
            "urllib3": {"level": "WARNING"},
            "multipart": {"level": "WARNING"},
            "pdfminer": {"level": "WARNING"},  # pdf2image/pymupdf noise
        },
    }

    dictConfig(LOG_CONFIG)
