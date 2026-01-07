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

    def generate_brand_kit(self, classified_assets, extracted_rules=None):
        """
        Input: 
            - classified_assets: list of dicts {'image': PIL_Obj, 'type': 'LOGO'/'IMAGERY'}
            - extracted_rules: Optional ExtractedBrandInfo object (from PDF)
        Output: JSON Dict (Brand Bible)
        """
        logos = [x["image"] for x in classified_assets if x["type"] == "LOGO"]
        imagery = [x["image"] for x in classified_assets if x["type"] == "IMAGERY"]

        # 1. Colors (From all assets) - Default to K-Means
        print("Extracting Color Palette...")
        master_palette = self._extract_palette(logos + imagery)

        # 2. Geometry (From logos)
        print("Calculating Aspect Ratios...")
        valid_ratios = self._extract_ratios(logos)

        # 3. Construct Base Brand Kit
        brand_kit = {
            "brand_name": "Humanitarians.AI", 
            "primary_colors": master_palette,
            "allowed_logo_ratios": valid_ratios,
            "brand_voice_attributes": [
                "professional",
                "innovative",
                "human-centric",
            ],
            "forbidden_keywords": ["cheap", "messy", "aggressive"],
        }
        
        # 4. MERGE / OVERRIDE with Extracted Rules (if present)
        if extracted_rules:
            print(">>> Merging Extracted Guidelines Rules...")
            
            if extracted_rules.brand_name:
                brand_kit["brand_name"] = extracted_rules.brand_name
            
            # Identify core vs secondary from the extracted list
            if extracted_rules.colors:
                # We can store the detailed object or just the hex strings for backward compat
                # Let's simple replace the primary_colors list with the extracted hexes for now
                # In the future, we should update the frontend to support the detailed objects
                extracted_hexes = [c.hex for c in extracted_rules.colors]
                brand_kit["primary_colors"] = extracted_hexes
                
                # Store the full rich data in a new key
                brand_kit["rich_colors"] = [c.dict() for c in extracted_rules.colors]
            
            if extracted_rules.typography:
                brand_kit["typography"] = [t.dict() for t in extracted_rules.typography]
                
            if extracted_rules.logo_rules:
                brand_kit["logo_rules"] = [r.dict() for r in extracted_rules.logo_rules]
                
            if extracted_rules.forbidden_keywords:
                brand_kit["forbidden_keywords"] = extracted_rules.forbidden_keywords

        return brand_kit
