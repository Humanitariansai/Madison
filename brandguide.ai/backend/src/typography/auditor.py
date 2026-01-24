from typing import Any, Dict, List, cast

import numpy as np
import pytesseract
from PIL import Image

from .siamese_manager import SiameseManager


class TypographyAuditor:
    def __init__(self, manager: SiameseManager):
        self.manager = manager

    def audit_page(
        self, page_image: Image.Image, brand_kit_id: str, allowed_fonts: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Audit a page image for typography compliance with Hierarchy Detection.
        """
        # Load embeddings
        embeddings = self.manager.load_kit_embeddings(brand_kit_id, allowed_fonts)
        if not embeddings:
            return [
                {
                    "type": "TYPOGRAPHY",
                    "status": "WARNING",
                    "metric": "No Brand Fonts initialized",
                    "bbox": [0, 0, 0, 0],
                }
            ]

        self.manager.classifier.set_reference_embeddings(embeddings)

        try:
            # 1. Block Extraction & Hierarchy Analysis
            # Output: level, page_num, block_num, par_num, line_num, word_num,
            # left, top, width, height, conf, text
            data = pytesseract.image_to_data(
                page_image, output_type=pytesseract.Output.DICT
            )

            w_page, h_page = page_image.size
            # pyrefly: ignore [bad-index]
            n_boxes = len(data["level"])

            # Group by Block
            blocks: Dict[int, Dict[str, Any]] = {}
            all_heights = []

            for i in range(n_boxes):
                # Level 5 = Word
                # pyrefly: ignore [bad-index]
                if data["level"][i] != 5:
                    continue

                # pyrefly: ignore [bad-index]
                text = data["text"][i].strip()
                if not text:
                    continue

                # pyrefly: ignore [bad-index]
                block_id = data["block_num"][i]

                if block_id not in blocks:
                    blocks[block_id] = {
                        "words": [],
                        "bboxes": [],  # list of (l,t,w,h)
                        "heights": [],
                    }

                left, t, w, h = (
                    # pyrefly: ignore [bad-index]
                    data["left"][i],
                    # pyrefly: ignore [bad-index]
                    data["top"][i],
                    # pyrefly: ignore [bad-index]
                    data["width"][i],
                    # pyrefly: ignore [bad-index]
                    data["height"][i],
                )
                blocks[block_id]["words"].append(text)
                blocks[block_id]["bboxes"].append((left, t, w, h))
                blocks[block_id]["heights"].append(h)
                all_heights.append(h)

            if not blocks:
                return []

            # 2. Determine Hierarchy Threshold
            median_height = np.median(all_heights) if all_heights else 20
            header_threshold = median_height * 1.3

            violations = []

            # 3. Audit Per Block
            for block_id, block_data in blocks.items():
                avg_height = np.mean(block_data["heights"])
                role = "HEADER" if avg_height > header_threshold else "BODY"

                # Get crops for characters in this block
                # NOTE: image_to_data gives WORDS. We need CHARACTERS for Siamese.
                # Re-cropping characters from words is tricky without char-boxes.
                #
                # Strategy:
                # We will perform a focused `image_to_boxes` OR
                # iterate character-by-character on the word crop?
                # Tesseract `image_to_boxes` is global.
                #
                # Hybrid approach:
                # We already established the Siamese model needs individual chars.
                # Let's crop the WHOLE BLOCK area and run `image_to_boxes`
                # on just that block?
                # Or just map the global `image_to_boxes` to this block's coordinates?
                #
                # Simpler: Crop the Block Area -> Run image_to_boxes on that crop.

                # Calculate Block BBox
                min_x = min(b[0] for b in block_data["bboxes"])
                min_y = min(b[1] for b in block_data["bboxes"])
                max_x = max(b[0] + b[2] for b in block_data["bboxes"])
                max_y = max(b[1] + b[3] for b in block_data["bboxes"])

                block_crop = page_image.crop((min_x, min_y, max_x, max_y))

                # Run Classification on this Block
                # We need a helper to extract chars from a crop
                block_result = self._audit_crop(block_crop)

                detected = block_result.get("detected_font", "unknown")
                confidence = block_result.get("confidence", 0.0)

                # Construct Result
                if detected != "unknown":
                    if detected not in allowed_fonts:
                        violations.append(
                            {
                                "type": "TYPOGRAPHY",
                                "status": "FAIL",
                                "metric": f"{role}: Detected off-brand '{detected}' "
                                f"({confidence:.0%})",
                                "bbox": [min_x, min_y, max_x - min_x, max_y - min_y],
                            }
                        )
                    else:
                        violations.append(
                            {
                                "type": "TYPOGRAPHY",
                                "status": "PASS",
                                "metric": f"{role}: {detected} is compliant",
                                "bbox": [min_x, min_y, max_x - min_x, max_y - min_y],
                            }
                        )
                else:
                    # Only warn for Headers, ignore unknown small text?
                    if role == "HEADER":
                        violations.append(
                            {
                                "type": "TYPOGRAPHY",
                                "status": "WARNING",
                                "metric": f"{role}: Could not identify font",
                                "bbox": [min_x, min_y, max_x - min_x, max_y - min_y],
                            }
                        )

            return violations

        except Exception as e:
            print(f"Typography Audit Error: {e}")
            return []

    def _audit_crop(self, image: Image.Image) -> dict:
        """
        Helper to run char extraction and classification on a specific image crop.
        """
        try:
            # image_to_boxes on the crop
            data = cast(
                Dict[str, List[Any]],
                pytesseract.image_to_boxes(image, output_type=pytesseract.Output.DICT),
            )

            w, h = image.size
            char_crops = []
            n_chars = len(data["char"])

            for i in range(n_chars):
                char = data["char"][i]
                if not char.isalnum():
                    continue

                # Tesseract coordinates (0,0 is bottom-left)
                left = data["left"][i]
                bottom = data["bottom"][i]
                right = data["right"][i]
                top_from_bottom = data["top"][i]

                # Convert to PIL (0,0 is top-left)
                box = (left, h - top_from_bottom, right, h - bottom)

                if box[2] <= box[0] or box[3] <= box[1]:
                    continue

                crop = image.crop(box)
                char_crops.append((char, crop))

            return self.manager.classifier.classify_image_chars(char_crops)

        except Exception:
            return {"detected_font": "unknown"}
