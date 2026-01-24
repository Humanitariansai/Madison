from typing import Dict

import torch
from PIL import Image, ImageDraw, ImageFont


class FontRenderer:
    """
    Renders glyphs from TTF/OTF files into images for the Siamese Network.
    """

    def __init__(self, glyph_size: int = 64):
        self.glyph_size = glyph_size
        self.chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"

    def render_font_to_embeddings(
        self, font_path: str, model, device
    ) -> Dict[str, torch.Tensor]:
        """
        Renders all supported characters from the font
        returns a dictionary of embeddings.
        { 'A': tensor(...), 'B': tensor(...) }
        """
        try:
            # Load font (try size 48 to fit in 64x64 comfortably)
            font = ImageFont.truetype(font_path, size=48)
        except Exception:
            print(f"Failed to load font {font_path}")
            return {}

        embeddings = {}

        # Preprocess helper
        def preprocess(img):
            import numpy as np

            # Resize to EXACTLY 64x64
            img = img.resize(
                (self.glyph_size, self.glyph_size), Image.Resampling.LANCZOS
            )
            arr = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(arr).unsqueeze(0).unsqueeze(0).float().to(device)

        for char in self.chars:
            try:
                # 1. Get Bounding Box
                bbox = font.getbbox(char)
                if bbox is None:
                    continue

                width = int(bbox[2] - bbox[0] + 10)
                height = int(bbox[3] - bbox[1] + 10)

                if width <= 0 or height <= 0:
                    continue

                # 2. Draw
                img = Image.new("L", (width, height), color=255)  # White bg
                draw = ImageDraw.Draw(img)
                # Offset to center/top-left with padding
                draw.text(
                    (int(-bbox[0] + 5), int(-bbox[1] + 5)), char, font=font, fill=0
                )  # Black text

                # 3. Encode
                with torch.no_grad():
                    tensor = preprocess(img)
                    embedding = model.forward_one(
                        tensor
                    ).cpu()  # Keep embeddings on CPU to save GPU memory

                embeddings[char] = embedding

            except Exception:
                # Skip broken chars
                continue

        return embeddings
