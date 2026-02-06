import logging
from typing import Optional

import numpy as np
from sklearn.cluster import KMeans

from .brand_guideline_extractor import ExtractedBrandInfo

logger = logging.getLogger(__name__)


class BrandGuidelineGenerator:
    def __init__(self):
        logger.info("Initializing BrandGuidelineGenerator service")

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

    def generate_brand_kit(
        self, classified_assets, extracted_rules: Optional[ExtractedBrandInfo]
    ):
        """
        Input:
            - classified_assets: list of dicts {'image': PIL_Obj, 'type': 'LOGO'}
            - extracted_rules: Optional ExtractedBrandInfo object (from PDF)
        Output: JSON Dict (Brand Bible) - Optimized Schema
        """
        logos = [x["image"] for x in classified_assets if x["type"] == "LOGO"]
        imagery = [x["image"] for x in classified_assets if x["type"] == "IMAGERY"]

        # 1. Colors - Unified structure
        logger.info(
            f"Extracting color palette from {len(logos + imagery)} combined assets"
        )
        extracted_hex_colors = self._extract_palette(logos + imagery)

        # Build unified colors array
        colors = []
        if extracted_rules and extracted_rules.colors:
            # Use rich PDF-extracted colors
            colors = [c.dict() for c in extracted_rules.colors]
        else:
            # Use simple hex from K-Means
            colors = [{"hex": hex_color} for hex_color in extracted_hex_colors]

        # 2. Logo - Unified structure
        logger.info("Calculating Logo Rules...")
        logo_ratios = self._extract_ratios(logos)
        logo = {"allowed_ratios": logo_ratios, "rules": []}

        if extracted_rules and extracted_rules.logo_rules:
            logo["rules"] = [r.dict() for r in extracted_rules.logo_rules]

        # 3. Typography - From PDF or empty
        typography = []
        if extracted_rules and extracted_rules.typography:
            typography = [t.dict() for t in extracted_rules.typography]

        # 4. Brand Voice - Unified structure
        brand_voice = {
            "attributes": ["professional", "innovative", "human-centric"],
            "forbidden_keywords": ["cheap", "messy", "aggressive"],
            "frequent_keywords": ["minimalist", "technology", "humanitarian", "clean"],
        }

        if extracted_rules:
            if extracted_rules.brand_name:
                brand_name = extracted_rules.brand_name
            else:
                brand_name = "Humanitarians.AI"

            # Override with PDF data
            if extracted_rules.brand_voice.forbidden_keywords:
                brand_voice["forbidden_keywords"] = (
                    extracted_rules.brand_voice.forbidden_keywords
                )
            if extracted_rules.brand_voice.frequent_keywords:
                brand_voice["frequent_keywords"] = (
                    extracted_rules.brand_voice.frequent_keywords
                )
            if extracted_rules.brand_voice.attributes:
                brand_voice["attributes"] = extracted_rules.brand_voice.attributes
        else:
            brand_name = "Humanitarians.AI"

        # 5. Construct Optimized Brand Kit
        brand_kit = {
            "brand_name": brand_name,
            "colors": colors,
            "color_tolerance": 50,
            "typography": typography,
            "logo": logo,
            "brand_voice": brand_voice,
        }

        return brand_kit
