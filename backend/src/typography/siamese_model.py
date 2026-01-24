from collections import Counter
from typing import Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

# Check for GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class GlyphEncoder(nn.Module):
    """
    CNN encoder that maps a 64x64 glyph image to a 128-dim embedding.
    """

    def __init__(self, embedding_dim: int = 128):
        super().__init__()

        # Convolutional layers
        self.conv = nn.Sequential(
            # 64x64 -> 32x32
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # 32x32 -> 16x16
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # 16x16 -> 8x8
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            # 8x8 -> 4x4
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
        )

        # Fully connected layers
        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 4 * 4, 512),
            nn.ReLU(inplace=True),
            nn.Dropout(0.3),
            nn.Linear(512, embedding_dim),
        )

        self.embedding_dim = embedding_dim

    def forward(self, x):
        x = self.conv(x)
        x = self.fc(x)
        # L2 normalize
        x = F.normalize(x, p=2, dim=1)
        return x


class SiameseNetwork(nn.Module):
    """
    Siamese network that compares two glyphs and outputs similarity score.
    """

    def __init__(self, embedding_dim: int = 128):
        super().__init__()
        self.encoder = GlyphEncoder(embedding_dim)

    def forward_one(self, x):
        """Get embedding for a single image."""
        return self.encoder(x)

    def forward(self, x1, x2):
        """Get embeddings for a pair of images."""
        e1 = self.encoder(x1)
        e2 = self.encoder(x2)
        return e1, e2


class SiameseFontClassifier:
    """Uses trained Siamese network to classify fonts."""

    def __init__(
        self,
        model: SiameseNetwork,
        reference_embeddings: Optional[Dict[str, Dict[str, torch.Tensor]]] = None,
    ):
        self.model = model.to(device)
        self.model.eval()
        self.glyph_size = 64
        self.reference_embeddings = reference_embeddings or {}

    def set_reference_embeddings(self, embeddings: Dict[str, Dict[str, torch.Tensor]]):
        self.reference_embeddings = embeddings

    def _preprocess_glyph(self, image: Image.Image) -> torch.Tensor:
        """Preprocess PIL Image to (1, 1, 64, 64) tensor."""
        # Convert to Grayscale
        if image.mode != "L":
            image = image.convert("L")

        # PADDING CORRECTION:
        # Tesseract returns tight crops. Training data has ~15-20% padding.
        # We must add white padding to match scale and border features.
        w, h = image.size
        # Add ~15% padding on each side (30% total width increase)
        pad_w = max(4, int(w * 0.15))
        pad_h = max(4, int(h * 0.15))

        new_w = w + 2 * pad_w
        new_h = h + 2 * pad_h

        padded = Image.new("L", (new_w, new_h), color=255)  # White BG
        padded.paste(image, (pad_w, pad_h))

        # Resize
        image = padded.resize(
            (self.glyph_size, self.glyph_size), Image.Resampling.LANCZOS
        )

        # Convert to numpy and normalize
        img_arr = np.array(image).astype(np.float32) / 255.0

        # To Tensor (1, 1, H, W)
        tensor = torch.from_numpy(img_arr).unsqueeze(0).unsqueeze(0).float()
        return tensor

    def classify_glyph(
        self, image: Image.Image, char: str, threshold: float = 0.55
    ) -> Tuple[Optional[str], float]:
        """Classify a single glyph. Returns (best_font, similarity)."""

        # Helper to run inference on a tensor
        def get_score(tensor, char_target):
            with torch.no_grad():
                embedding = self.model.forward_one(tensor).cpu()

            best_f = None
            best_s = -1.0

            for font_name, char_embeddings in self.reference_embeddings.items():
                if char_target not in char_embeddings:
                    continue
                ref_embedding = char_embeddings[char_target]
                sim = F.cosine_similarity(embedding, ref_embedding).item()
                if sim > best_s:
                    best_s = sim
                    best_f = font_name
            return best_f, best_s

        # 1. Try Normal
        tensor_normal = self._preprocess_glyph(image).to(device)
        font_normal, score_normal = get_score(tensor_normal, char)

        # 2. Try Inverted (Handle White-on-Black text)
        from PIL import ImageOps

        # Convert to L for inversion if needed
        if image.mode != "L":
            img_for_inv = image.convert("L")
        else:
            img_for_inv = image

        tensor_inverted = self._preprocess_glyph(ImageOps.invert(img_for_inv)).to(
            device
        )
        font_inverted, score_inverted = get_score(tensor_inverted, char)

        # Pick best
        if score_inverted > score_normal:
            best_font = font_inverted
            best_score = score_inverted
        else:
            best_font = font_normal
            best_score = score_normal

        # DEBUG LOG
        # print(f"Char: {char} | Best: {best_font} | Score: {best_score:.4f}")

        # Check threshold
        if best_score < threshold:
            # print(f"Rejected {char} (Score {best_score:.4f} < {threshold})")
            return None, best_score

        return best_font, best_score

    def classify_image_chars(
        self, char_crops: List[Tuple[str, Image.Image]], min_chars: int = 3
    ) -> dict:
        """
        Classify fonts based on a list of (character, crop_image) tuples.
        This expects the OCR step to have already happened.
        """

        if len(char_crops) < min_chars:
            return {
                "detected_font": "unknown",
                "confidence": 0.0,
                "votes": {},
                "matches": [],
                "status": "insufficient_characters",
            }

        votes: Counter = Counter()
        matches = []

        for char, crop_img in char_crops:
            # Check if char exists in any reference
            has_ref = any(
                char in self.reference_embeddings.get(f, {})
                for f in self.reference_embeddings
            )
            if not has_ref:
                continue

            best_font, score = self.classify_glyph(crop_img, char)

            if best_font:
                votes[best_font] += 1
                matches.append((char, best_font, score))
            else:
                # DEBUG: Save rejected crop
                try:
                    import time
                    from pathlib import Path

                    debug_dir = (
                        Path(__file__).parent.parent.parent / "data" / "debug_crops"
                    )
                    debug_dir.mkdir(exist_ok=True, parents=True)
                    crop_img.save(
                        debug_dir / f"rejected_{char}_{score:.2f}_{time.time()}.png"
                    )
                except Exception as e:
                    print(f"Failed to save debug crop: {e}")

        total_chars = len(char_crops)

        if not votes:
            return {
                "detected_font": "unknown",
                "confidence": 0.0,
                "votes": {},
                "matches": matches,
                "status": "no_matches",
            }

        detected_font = votes.most_common(1)[0][0]
        # CONFIDENCE FIX: Divide by TOTAL characters, not just valid votes
        confidence = votes[detected_font] / total_chars

        # If confidence is too low
        # (meaning mostly rejected or split vote), return unknown
        if confidence < 0.5:
            return {
                "detected_font": "unknown",
                "confidence": confidence,
                "votes": dict(votes),
                "matches": matches,
                "status": "low_confidence",
            }

        return {
            "detected_font": detected_font,
            "confidence": confidence,
            "votes": dict(votes),
            "matches": matches,
            "status": "success",
        }
