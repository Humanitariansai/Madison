import threading
from pathlib import Path
from typing import Any, Dict, List

import torch

from .font_renderer import FontRenderer
from .siamese_model import SiameseFontClassifier, SiameseNetwork

MODELS_DIR = Path(__file__).parent.parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = MODELS_DIR / "siamese_model.pt"


class SiameseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SiameseManager, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        print("Initializing SiameseManager (Eager Loading)...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        # 1. Load Model Eagerly
        print("Loading Siamese Network...")
        self._model = SiameseNetwork().to(self.device)
        self._load_weights()

        # 2. Init Classifier Eagerly
        print("Initializing Classifier...")
        self._classifier = SiameseFontClassifier(self._model)

        # 3. Init Renderer Eagerly
        print("Initializing FontRenderer...")
        self._renderer = FontRenderer()

        print("SiameseManager initialized successfully.")

    @property
    def model(self):
        return self._model

    @property
    def classifier(self):
        return self._classifier

    @property
    def renderer(self):
        return self._renderer

    def _load_weights(self):
        # Try to load weights
        if MODEL_PATH.exists():
            print(f"Loading Siamese model from {MODEL_PATH}...")
            try:
                checkpoint = torch.load(MODEL_PATH, map_location=self.device)
                if "model_state_dict" in checkpoint:
                    self._model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    self._model.load_state_dict(checkpoint)
                print("Model weights loaded successfully.")
            except Exception as e:
                print(f"Failed to load weights: {e}")
                print("WARNING: Using initialized (random) weights")
        else:
            print(
                f"No model found at {MODEL_PATH}. Using initialized (random) weights."
            )

    def _load_model(self):
        print("Lazy loading Siamese Network...")
        self._model = SiameseNetwork().to(self.device)

        # Try to load weights
        if MODEL_PATH.exists():
            print(f"Loading Siamese model from {MODEL_PATH}...")
            try:
                checkpoint = torch.load(MODEL_PATH, map_location=self.device)
                if "model_state_dict" in checkpoint:
                    self._model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    self._model.load_state_dict(checkpoint)
                print("Model weights loaded successfully.")
            except Exception as e:
                print(f"Failed to load weights: {e}")
                print("WARNING: Using initialized (random) weights")
        else:
            print(
                f"No model found at {MODEL_PATH}. Using initialized (random) weights."
            )

    def ingest_new_font(self, font_path: str, font_name: str) -> Dict[str, Any]:
        """
        1. Render glyphs from font_path
        2. Generate embeddings
        3. Return statistics
        """
        print(f"Ingesting font: {font_name} from {font_path}")

        # Generate Embeddings
        embeddings = self.renderer.render_font_to_embeddings(
            font_path, self.model, self.device
        )

        if not embeddings:
            return {"success": False, "error": "No glyphs could be rendered"}

        return {
            "success": True,
            "char_count": len(embeddings),
            "embeddings": embeddings,  # Tensor dictionary
        }

    def save_embeddings(
        self, brand_kit_id: str, font_name: str, embeddings: Dict[str, torch.Tensor]
    ):
        """
        Persist embeddings to disk for this brand kit.
        """
        kit_dir = Path(__file__).parent.parent.parent / "uploads" / brand_kit_id
        kit_dir.mkdir(parents=True, exist_ok=True)

        save_path = kit_dir / f"embeddings_{font_name}.pt"
        torch.save(embeddings, save_path)
        print(f"Saved embeddings to {save_path}")
        return str(save_path)

    def load_kit_embeddings(
        self, brand_kit_id: str, font_names: List[str]
    ) -> Dict[str, Dict[str, torch.Tensor]]:
        """
        Load all embeddings for a brand kit (for inference).
        Returns: { 'Larsseit-Bold': {'A': tensor...} }
        """
        kit_dir = Path(__file__).parent.parent.parent / "uploads" / brand_kit_id
        all_embeddings = {}

        for font in font_names:
            path = kit_dir / f"embeddings_{font}.pt"
            if path.exists():
                try:
                    emb = torch.load(path, map_location=self.device)
                    all_embeddings[font] = emb
                except Exception as e:
                    print(f"Error loading {path}: {e}")

        return all_embeddings
