import logging
import threading

import cv2
from transformers import CLIPModel, CLIPProcessor, pipeline

logger = logging.getLogger(__name__)


class MLService:
    """
    Singleton service to manage heavy ML models.
    Implements Eager Loading with Singleton pattern to ensure Thread Safety.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(MLService, cls).__new__(cls)
                    cls._instance._init_models()
        return cls._instance

    def _init_models(self):
        logger.info("Initializing ML models (Eager Loading)...")

        # SIFT
        logger.info("Loading SIFT...")
        # pyrefly: ignore [missing-attribute]
        self._sift = cv2.SIFT_create()

        # NLP
        logger.info("Loading NLP Pipeline (DistilBART)...")
        # Switched to distilbart for 2x speed and <50% memory usage
        self._nlp_pipe = pipeline(
            "zero-shot-classification", model="valhalla/distilbart-mnli-12-3"
        )

        # CLIP
        logger.info("Loading CLIP Model & Processor...")
        self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self._clip_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )
        logger.info("ML Models initialized successfully.")

    @property
    def sift(self):
        return self._sift

    @property
    def nlp_pipe(self):
        return self._nlp_pipe

    @property
    def clip_model(self):
        return self._clip_model

    @property
    def clip_processor(self):
        return self._clip_processor
