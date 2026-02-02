import logging

import cv2
from transformers import CLIPModel, CLIPProcessor, pipeline

logger = logging.getLogger(__name__)


class MLService:
    """
    Singleton service to manage heavy ML models.
    Implements lazy loading to avoid startup bottlenecks.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MLService, cls).__new__(cls)
            cls._instance._init_models()
        return cls._instance

    def _init_models(self):
        self._sift = None
        self._nlp_pipe = None
        self._clip_model = None
        self._clip_processor = None

    @property
    def sift(self):
        if self._sift is None:
            logger.info("Lazy loading SIFT...")
            # pyrefly: ignore [missing-attribute]
            self._sift = cv2.SIFT_create()
        return self._sift

    @property
    def nlp_pipe(self):
        if self._nlp_pipe is None:
            logger.info("Lazy loading NLP Pipeline (DistilBART)...")
            # Switched to distilbart for 2x speed and <50% memory usage
            self._nlp_pipe = pipeline(
                "zero-shot-classification", model="valhalla/distilbart-mnli-12-3"
            )
        return self._nlp_pipe

    @property
    def clip_model(self):
        if self._clip_model is None:
            logger.info("Lazy loading CLIP Model...")
            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        return self._clip_model

    @property
    def clip_processor(self):
        if self._clip_processor is None:
            logger.info("Lazy loading CLIP Processor...")
            self._clip_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
        return self._clip_processor


# Global instance
ml_service = MLService()
