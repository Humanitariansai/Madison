import numpy as np
from sklearn.cluster import KMeans


class BrandGuidelineGenerator:
    def __init__(self):
        print("Initializing Generator...")

    def _extract_palette(self, images, k=5):
        """Extracts the Master Color Palette from a list of PIL Images"""
        all_pixels = []
        for img in images:
            # Resize to speed up processing
            thumb = img.resize((100, 100))
            # Remove alpha channel if present
            if thumb.mode != "RGB":
                thumb = thumb.convert("RGB")
            all_pixels.append(np.array(thumb).reshape(-1, 3))

        if not all_pixels:
            return []

        # Flatten list of arrays
        pool = np.vstack(all_pixels)

        # K-Means to find dominant colors
        kmeans = KMeans(n_clusters=k, n_init=10)
        kmeans.fit(pool)

        # Convert to Hex
        hex_colors = [
            "#{:02x}{:02x}{:02x}".format(int(c[0]), int(c[1]), int(c[2]))
            for c in kmeans.cluster_centers_
        ]
        return hex_colors

    def _extract_ratios(self, logo_images):
        """Get valid Aspect Ratios from logos"""
        ratios = []
        for img in logo_images:
            w, h = img.size
            ratios.append(round(w / h, 2))
        return sorted(list(set(ratios)))

    def generate_brand_kit(self, classified_assets):
        """
        Input: A list of dicts: {'image': PIL_Obj, 'type': 'LOGO'/'IMAGERY'}
        Output: JSON Dict (Brand Bible)
        """
        logos = [x["image"] for x in classified_assets if x["type"] == "LOGO"]
        imagery = [x["image"] for x in classified_assets if x["type"] == "IMAGERY"]

        # 1. Colors (From all assets)
        print("Extracting Color Palette...")
        master_palette = self._extract_palette(logos + imagery)

        # 2. Geometry (From logos)
        print("Calculating Aspect Ratios...")
        valid_ratios = self._extract_ratios(logos)

        # 3. Construct Brand Kit
        brand_kit = {
            "brand_name": "Humanitarians.AI",  # Manual entry or OCR detection
            "primary_colors": master_palette,
            "allowed_logo_ratios": valid_ratios,
            "brand_voice_attributes": [
                "professional",
                "innovative",
                "human-centric",
            ],  # Can be automated via NLP later
            "forbidden_keywords": ["cheap", "messy", "aggressive"],
        }
        return brand_kit
