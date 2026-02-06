import logging

import cv2
import numpy as np
import pytesseract
import torch
from pdf2image import convert_from_path
from PIL import Image, ImageStat
from sklearn.cluster import KMeans

from .layout_classifier import LayoutType, PageLayout
from .services.ml_service import MLService

logger = logging.getLogger(__name__)


class IntegratedBrandAuditor:
    def __init__(self, brand_bible, reference_assets, ml_service: MLService = None):
        self.bible = brand_bible
        # If no service provided, grab the singleton instance
        self.ml = ml_service if ml_service else MLService()

        # --- 2. INDEX LOGO VARIANTS ---
        # We index every single logo file provided in the training assets
        self.logo_variants = []
        logo_imgs = [x for x in reference_assets if x["type"] == "LOGO"]

        logger.info(f"Indexing {len(logo_imgs)} Logo Variants...")
        for i, item in enumerate(logo_imgs):
            pil_img = item["image"]

            # --- FIX: Handle file paths if passed instead of PIL objects ---
            if isinstance(pil_img, str):
                try:
                    pil_img = Image.open(pil_img).convert("RGB")
                except Exception as e:
                    logger.error(
                        f"Failed to load logo variant {item.get('filename')}: {e}"
                    )
                    continue
            # ---------------------------------------------------------------

            filename = item.get("filename", f"variant_{i}")

            # Convert to Grayscale for SIFT
            img_cv = np.array(pil_img)
            if len(img_cv.shape) == 3:
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)

            # Use singleton SIFT
            kp, des = self.ml.sift.detectAndCompute(img_cv, None)

            if des is not None:
                w, h = pil_img.size
                self.logo_variants.append(
                    {
                        "id": i,
                        "name": filename,
                        "kp": kp,
                        "des": des,
                        "size": (w, h),
                        "aspect_ratio": w / h,
                        "original_image": pil_img,
                    }
                )

        # --- 3. COMPUTE LOGO ANCHOR EMBEDDINGS (CLIP) ---
        # For the Semantic Safeguard (Distorted/Third-Party Logic)
        self.logo_embeddings = None
        if self.logo_variants:
            logger.info("Computing Logo Anchor Embeddings...")
            try:
                # Collect all logo PIL images
                anchor_imgs = [v["original_image"] for v in self.logo_variants]

                # Preprocess
                inputs = self.ml.clip_processor(
                    images=anchor_imgs, return_tensors="pt", padding=True
                )

                # Encode
                with torch.no_grad():
                    image_features = self.ml.clip_model.get_image_features(**inputs)

                # Normalize
                self.logo_embeddings = image_features / image_features.norm(
                    dim=-1, keepdim=True
                )
                logger.info(f"✅ Indexed {len(self.logo_embeddings)} Logo Anchors.")
            except Exception as e:
                logger.error(f"⚠️ Failed to compute logo embeddings: {e}")

        # --- 4. PRE-COMPUTE 3RD PARTY PROMPTS ---
        self.third_party_prompts = [
            "a logo",
            "a photograph",
            "generic imagery",
            "text screenshot",
        ]
        self.tp_text_feats = None
        try:
            txt_inputs = self.ml.clip_processor(
                text=self.third_party_prompts, return_tensors="pt", padding=True
            )
            with torch.no_grad():
                feat = self.ml.clip_model.get_text_features(**txt_inputs)

                # Defense
                if not isinstance(feat, torch.Tensor):
                    if hasattr(feat, "text_embeds"):
                        feat = feat.text_embeds
                    elif hasattr(feat, "pooler_output"):
                        feat = feat.pooler_output
                    else:
                        feat = feat[0]

                self.tp_text_feats = feat / feat.norm(dim=-1, keepdim=True)
            logger.info("✅ Pre-computed 3rd Party Prompts.")
        except Exception as e:
            logger.error(f"⚠️ Failed to compute prompt embeddings: {e}")

    def _parse_colors_to_rgb(self, colors: list) -> list:
        """
        Parse a list of color dictionaries to RGB values.
        Tries RGB field first (handles various formats), then falls back to hex.

        Args:
            colors: List of color dicts with 'rgb' and/or 'hex' fields

        Returns:
            List of RGB values (as lists or tuples)
        """
        allowed_rgbs = []

        if not colors:
            return allowed_rgbs

        for c in colors:
            # Try RGB first (if available from PDF)
            if c.get("rgb"):
                try:
                    val = c["rgb"]
                    if isinstance(val, str):
                        # Handle "74-21-75" or "74, 21, 75" formats
                        parts = val.replace(",", " ").replace("-", " ").split()
                        allowed_rgbs.append([float(p) for p in parts])
                    elif isinstance(val, list):
                        allowed_rgbs.append(val)
                    continue  # Successfully parsed RGB, skip hex
                except Exception:
                    pass  # Fall through to hex parsing

            # Fall back to hex (always present)
            if c.get("hex"):
                try:
                    h = c["hex"].lstrip("#")
                    rgb = tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))
                    allowed_rgbs.append(rgb)
                except Exception:
                    pass

        return allowed_rgbs

    # ==================================================
    # PHASE 0: BATCH AUDIT (Entry Point)
    # ==================================================
    def audit_batch(
        self,
        pages_pil: list[Image.Image],
        layouts: list[PageLayout],
        page_cvs: list[np.ndarray],
    ):
        """
        Efficient Batch Auditor.
        1. MAP: Collect all Text strings and Image crops from ALL pages.
        2. REDUCE: Run Batch Inference (NLP + CLIP).
        3. ASSIGN: Distribute results back to pages.
        """
        logger.info(f"Starting Batch Audit on {len(pages_pil)} pages...")
        batch_results = [[] for _ in pages_pil]  # results per page

        # --- A. Collect Inputs ---
        all_text_tasks = []  # (page_idx, text_string, w)
        all_crop_tasks = []  # (page_idx, region, crop_pil)

        for i, (page, layout) in enumerate(zip(pages_pil, layouts)):
            w, h = page.size

            # 1. Text Regions
            text_regions = (
                layout.get_regions_by_type(LayoutType.TEXT)
                + layout.get_regions_by_type(LayoutType.TITLE)
                + layout.get_regions_by_type(LayoutType.SECTION_HEADER)
            )

            full_text_parts = [
                r.content
                for r in text_regions
                if isinstance(r.content, str) and r.content
            ]
            if full_text_parts:
                full_text = " ".join(full_text_parts)
                if len(full_text.split()) >= 10:
                    all_text_tasks.append((i, full_text, w))

            # 2. Image Regions
            img_regions = layout.get_regions_by_type(LayoutType.FIGURE)
            for region in img_regions:
                x0, y0, x1, y1 = region.bbox
                crop_box = (int(x0), int(y0), int(x1), int(y1))
                if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
                    crop = page.crop(crop_box)
                    all_crop_tasks.append((i, region, crop))

        # --- B. Batch Inference ---

        # B1. Text (NLP Zero-Shot)
        if all_text_tasks:
            texts = [t[1] for t in all_text_tasks]
            labels = self.bible["brand_voice_attributes"] + ["spammy", "aggressive"]

            logger.info(f"Batch Auditing {len(texts)} text blocks...")
            try:
                # Run batch inference
                nlp_results = self.ml.nlp_pipe(
                    texts, candidate_labels=labels, batch_size=8
                )

                # Assign back
                if not isinstance(nlp_results, list):
                    nlp_results = [nlp_results]

                for (p_idx, txt, w), res in zip(all_text_tasks, nlp_results):
                    # pyrefly: ignore [bad-index]
                    top_label = res["labels"][0]
                    status = (
                        "PASS"
                        if top_label in self.bible["brand_voice_attributes"]
                        else "WARNING"
                    )

                    batch_results[p_idx].append(
                        {
                            "type": "TEXT_BODY",
                            "bbox": [0, 0, w, 50],
                            "status": status,
                            "metric": f"Tone: {top_label}",
                            "level": "PASS" if status == "PASS" else "WARNING",
                        }
                    )
            except Exception as e:
                logger.error(f"Batch Text Audit failed: {e}")

        # B2. Images (CLIP)
        if all_crop_tasks:
            crops = [t[2] for t in all_crop_tasks]
            logger.info(f"Batch Auditing {len(crops)} image crops...")

            try:
                # 1. Encode All Crops
                inputs = self.ml.clip_processor(
                    images=crops, return_tensors="pt", padding=True
                )
                with torch.no_grad():
                    crop_embeddings = self.ml.clip_model.get_image_features(**inputs)

                    # Defense against varying Transformers versions return types
                    if not isinstance(crop_embeddings, torch.Tensor):
                        if hasattr(crop_embeddings, "image_embeds"):
                            crop_embeddings = crop_embeddings.image_embeds
                        elif hasattr(crop_embeddings, "pooler_output"):
                            crop_embeddings = crop_embeddings.pooler_output
                        else:
                            crop_embeddings = crop_embeddings[0]

                    # Normalize
                    crop_embeddings = crop_embeddings / crop_embeddings.norm(
                        dim=-1, keepdim=True
                    )

                # 2. Process Each Crop with Pre-Computed Embedding
                for idx, (p_idx, region, crop) in enumerate(all_crop_tasks):
                    emb = crop_embeddings[idx].unsqueeze(0)  # Keep (1, D) shape

                    # Call modified worker that accepts embedding
                    res = self._process_single_image_region(region, crop, pre_emb=emb)
                    if res:
                        batch_results[p_idx].append(res)

            except Exception as e:
                logger.error(f"Batch Image Audit failed: {e}")

        # --- C. Background Pipeline (Fast CPU) ---
        # No batching needed for OpenCV logic, just run loop
        for i, (layout, page_cv) in enumerate(zip(layouts, page_cvs)):
            # Re-create gray
            if len(page_cv.shape) == 3:
                gray = cv2.cvtColor(page_cv, cv2.COLOR_RGB2GRAY)
            else:
                gray = page_cv

            bg_res = self._pipeline_background(layout, page_cv, gray)
            batch_results[i].extend(bg_res)

        return batch_results

    # ==================================================
    # PHASE 1: LOGO DETECTION (Multi-Variant SIFT)
    # ==================================================
    def _find_logos(self, page_cv_gray):
        found_instances = []

        kp_page, des_page = self.ml.sift.detectAndCompute(page_cv_gray, None)
        if des_page is None:
            return []

        flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))

        # Check against EVERY variant
        for variant in self.logo_variants:
            matches = flann.knnMatch(variant["des"], des_page, k=2)
            good = [m for m, n in matches if m.distance < 0.65 * n.distance]

            if len(good) > 15:
                src_pts = np.float32(
                    # pyrefly: ignore [bad-argument-type]
                    [variant["kp"][m.queryIdx].pt for m in good]
                ).reshape(-1, 1, 2)
                # pyrefly: ignore [bad-argument-type]
                dst_pts = np.float32([kp_page[m.trainIdx].pt for m in good]).reshape(
                    -1, 1, 2
                )

                M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                if M is not None:
                    h, w = variant["size"][1], variant["size"][0]
                    pts = np.float32(
                        # pyrefly: ignore [bad-argument-type]
                        [[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]
                    ).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)

                    x = int(min(dst[:, 0, 0]))
                    y = int(min(dst[:, 0, 1]))
                    w_new = int(max(dst[:, 0, 0])) - x
                    h_new = int(max(dst[:, 0, 1])) - y

                    # Sanity Checks (Size & Ratio)
                    if w_new < 30 or h_new < 30:
                        continue

                    detected_ratio = w_new / h_new
                    ref_ratio = variant["aspect_ratio"]

                    # Allow 25% distortion
                    if not (ref_ratio * 0.75 < detected_ratio < ref_ratio * 1.25):
                        continue

                    found_instances.append(
                        {
                            "variant": variant,
                            "bbox": [x, y, w_new, h_new],
                            "match_score": len(good),
                        }
                    )

        return self._deduplicate_matches(found_instances)

    def _deduplicate_matches(self, instances):
        """If multiple variants match the same spot, pick the best one."""
        if not instances:
            return []
        instances.sort(key=lambda x: x["match_score"], reverse=True)
        unique = []
        for cand in instances:
            cx, cy, _, _ = cand["bbox"]
            is_overlap = False
            for exist in unique:
                ex, ey, _, _ = exist["bbox"]
                # Simple distance check for overlap
                if abs(cx - ex) < 50 and abs(cy - ey) < 50:
                    is_overlap = True
                    break
            if not is_overlap:
                unique.append(cand)
        return unique

    def _check_logo_compliance(self, crop, variant_data):
        # 1. Ratio Check
        w, h = crop.size
        det_ratio = w / h
        ref_ratio = variant_data["aspect_ratio"]
        ratio_pass = abs(det_ratio - ref_ratio) < 0.2

        # 2. Color Check (Compare against specific variant reference)
        crop_stat = ImageStat.Stat(crop)
        ref_stat = ImageStat.Stat(variant_data["original_image"])
        # Euclidean distance of RGB averages
        dist = (
            sum([(a - b) ** 2 for a, b in zip(crop_stat.mean[:3], ref_stat.mean[:3])])
            ** 0.5
        )
        color_pass = dist < 65.0  # Tolerance

        status = "PASS" if (ratio_pass and color_pass) else "FAIL"
        return status, f"Matches {variant_data['name']}"

    # ==================================================
    # PHASE 2: IMAGERY DETECTION (Generic with Masking)
    # ==================================================
    def _find_imagery(self, page_cv_gray, mask_boxes):
        clean_page = page_cv_gray.copy()
        # Paint logos white to hide them
        for x, y, w, h in mask_boxes:
            cv2.rectangle(clean_page, (x, y), (x + w, y + h), (255), -1)

        thresh = cv2.adaptiveThreshold(
            clean_page,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2,
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        found_imgs = []
        page_area = clean_page.shape[0] * clean_page.shape[1]
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w < 100 or h < 100:
                continue
            if (w * h) > (page_area * 0.9):
                continue
            found_imgs.append([x, y, w, h])
        return found_imgs

    def _check_imagery_vibe(self, img_crop):
        targets = "a photo that is " + ", ".join(
            self.bible.get("brandvoice", {}).get("frequent_keywords", [])
        )
        negative = "cartoon, blurry, text overlay, screenshot, low resolution"

        inputs = self.ml.clip_processor(
            # pyrefly: ignore [bad-argument-type]
            text=[targets, negative],
            images=img_crop,
            return_tensors="pt",
            padding=True,
        )
        probs = self.ml.clip_model(**inputs).logits_per_image.softmax(dim=1)
        score = probs[0][0].item()

        return "PASS" if score > 0.6 else "FAIL", f"Vibe Score: {score:.2%}"

    # ==================================================
    # PHASE 3: TEXT (Voice)
    # ==================================================
    def _check_text_voice(self, text):
        if len(text.split()) < 10:
            return None, None
        labels = self.bible["brand_voice_attributes"] + ["spammy", "aggressive"]
        res = self.ml.nlp_pipe(text, labels)
        # pyrefly: ignore [bad-index]
        top = res["labels"][0]
        return "PASS" if top in self.bible[
            "brand_voice_attributes"
        ] else "WARNING", f"Tone: {top}"

    # ==================================================
    # PHASE 4: COLOR PALETTE COMPLIANCE
    # ==================================================
    def _extract_dominant_colors(self, image_pil, k=5):
        """Extract dominant colors from the page using KMeans."""
        thumb = image_pil.resize((150, 150))
        if thumb.mode != "RGB":
            thumb = thumb.convert("RGB")

        # Convert to numpy and reshape
        img_arr = np.array(thumb)
        pixels = img_arr.reshape(-1, 3)

        # KMeans
        kmeans = KMeans(n_clusters=k, n_init=5)
        kmeans.fit(pixels)

        # Returns list of RGB tuples
        return kmeans.cluster_centers_

    def _check_palette_compliance(self, dominant_colors):
        """
        Compare dominant page colors against the Brand Kit's allowed colors.
        Returns: status (PASS/FAIL), message
        """
        # 1. Get Allowed Colors from Brand Kit (unified colors field)
        allowed_rgbs = self._parse_colors_to_rgb(self.bible.get("colors", []))

        if not allowed_rgbs:
            return "WARNING", "No Brand Colors defined in Kit."

        # 2. Check each dominant color
        violations = []
        tolerance = 80.0  # Euclidean distance threshold (Increased for textures)

        for dom in dominant_colors:
            # Check distance to NEAREST brand color
            distances = [
                sum([(a - b) ** 2 for a, b in zip(dom, ref)]) ** 0.5
                for ref in allowed_rgbs
            ]
            min_dist = min(distances)

            # If color is White/Black/Grayish, we might want to ignore?
            is_white = all(c > 240 for c in dom)
            is_black = all(c < 15 for c in dom)

            # Check for Greyscale/Desaturated (R ~= G ~= B)
            is_grey = np.std(dom) < 10.0

            if not is_white and not is_black and not is_grey and min_dist > tolerance:
                # Convert to Hex for display
                dom_hex = "#{:02x}{:02x}{:02x}".format(
                    int(dom[0]), int(dom[1]), int(dom[2])
                )
                violations.append(dom_hex)

        if violations:
            return "FAIL", f"Off-brand colors detected: {', '.join(violations[:3])}"

        return "PASS", "Palette compliant"

    def _audit_background_layer(self, page_cv, bg_mask, colors):
        """
        Audits background pixels using Histogram Coverage (Texture Safe).
        """
        # 1. Sample pixels from the MASKED background
        masked_bg = cv2.bitwise_and(page_cv, page_cv, mask=bg_mask)

        # Pixels where mask is 255
        bg_pixels = masked_bg[bg_mask == 255]

        if len(bg_pixels) < 100:
            return "PASS", "No significant background detected"

        # Downsample for speed (e.g. 5000 pixels)
        if len(bg_pixels) > 5000:
            indices = np.random.choice(len(bg_pixels), 5000, replace=False)
            bg_pixels = bg_pixels[indices]

        # 2. Prepare Allowed Colors
        allowed_rgbs = self._parse_colors_to_rgb(colors if colors else [])

        if not allowed_rgbs:
            return "WARNING", "No Brand Colors defined"

        # 3. Vote (Histogram Coverage)
        # Count how many pixels are "close enough" to ANY brand color
        match_count = 0
        tolerance = 45.0  # Stricter than K-Means because no averaging

        for pix in bg_pixels:
            # Distance to nearest brand color
            min_dist = float("inf")
            for ref in allowed_rgbs:
                d = sum([(a - b) ** 2 for a, b in zip(pix, ref)]) ** 0.5
                if d < min_dist:
                    min_dist = d

            # Check if neutral (Grey/White/Black)
            is_white = all(c > 240 for c in pix)
            is_black = all(c < 15 for c in pix)
            # is_grey = np.std(pix) < 10.0 # Strict grey check

            if min_dist < tolerance or is_white or is_black:
                match_count += 1

        compliance_ratio = match_count / len(bg_pixels)

        # Pass if > 70% of the background is compliant
        if compliance_ratio > 0.70:
            return "PASS", f"Background Compliant ({compliance_ratio:.0%})"
        else:
            return "FAIL", f"Non-compliant Background ({compliance_ratio:.0%} match)"

    def _audit_text_layer(self, page_cv, text_bboxes, brand_kit):
        """
        Audits Text Colors against Background Context.
        Enforces: "Use White Text on Aubergine" etc.

        Returns:
            tuple: (status, message, bbox)
            - status (str): 'PASS', 'FAIL', or 'WARNING'
            - message (str): Description of the finding
            - bbox (list | None): [x, y, w, h] of the violating text or None
        """
        usage_rules = brand_kit.get("color_usage_rules", [])
        if not usage_rules:
            return "PASS", "No Text Rules defined", None

        # Prepare rules lookup
        # e.g. "aubergine" -> allowed=["white"]

        # Simplistic check for now:
        # For each text box, determine Text Color and Local BG Color
        violations = []

        for x, y, w, h in text_bboxes:
            if w < 5 or h < 5:
                continue

            # Extract Text ROI
            roi = page_cv[y : y + h, x : x + w]

            # 1. Determine Local Background (just outside the box?)
            # Or assume the "Text Color" is the foreground and "BG" is the rest
            # Use Otsu's thresholding to separate FG/BG
            try:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                _, mask = cv2.threshold(
                    gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
                )

                # FG (Text) = pixels where mask is 0 (Black)
                # usually involved with dark text on light?
                # Actually Otsu makes one class 0 and other 255.
                # Let's assume Text is the Minority Class usually?
                num_zeros = np.count_nonzero(mask == 0)
                num_ones = np.count_nonzero(mask == 255)

                if num_zeros < num_ones:
                    fg_mask = mask == 0
                    bg_mask = mask == 255
                else:
                    fg_mask = mask == 255
                    bg_mask = mask == 0

                fg_pixels = roi[fg_mask]
                bg_pixels = roi[bg_mask]

                if len(fg_pixels) == 0 or len(bg_pixels) == 0:
                    continue

                # Average Colors
                # text_color = np.mean(fg_pixels, axis=0)  # R,G,B (Unused)
                bg_color = np.mean(bg_pixels, axis=0)  # R,G,B

                # 2. Check Rules
                # We need to map "bg_color" (RGB) to a Name (e.g. "Aubergine")
                # Find closest named brand color
                bg_name_found = None

                if brand_kit.get("rich_colors"):
                    min_d = float("inf")
                    for rc in brand_kit["rich_colors"]:
                        try:
                            val = rc["rgb"].replace(",", " ").replace("-", " ")
                            ref_rgb = [float(p) for p in val.split()]
                            d = (
                                sum([(a - b) ** 2 for a, b in zip(bg_color, ref_rgb)])
                                ** 0.5
                            )
                            if d < min_d:
                                min_d = d
                                bg_name_found = rc["name"]
                        except Exception:
                            pass

                # If we found a background name, check strict rules
                if bg_name_found:
                    for rule in usage_rules:
                        # Fuzzy match name? "Aubergine" vs "Core Aubergine"
                        if rule["background_color"].lower() in bg_name_found.lower():
                            # Enforce allowed text colors
                            # This is tricky without knowing what "White" RGB is exactly
                            # Assume "White" means > 240, 240, 240

                            allowed = [c.lower() for c in rule["allowed_text_colors"]]

                            # Use 95th Percentile to ignore anti-aliased edges
                            text_p95 = np.percentile(fg_pixels, 95, axis=0)

                            def get_lum(c):
                                return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

                            t_lum = get_lum(text_p95)
                            bg_lum = get_lum(bg_color)

                            # Saturation
                            c_max, c_min = np.max(text_p95), np.min(text_p95)
                            sat = (c_max - c_min) / c_max if c_max > 0 else 0

                            is_strict_white = all(c > 200 for c in text_p95)

                            # Robust White: High Brightness (>140),
                            # High Contrast vs BG (>60), Low Saturation (<0.2)
                            is_robust_white = (
                                (t_lum > 140) and (t_lum - bg_lum > 60) and (sat < 0.20)
                            )

                            if "white" in allowed and not (
                                is_strict_white or is_robust_white
                            ):
                                violations.append(
                                    f"Text on {bg_name_found} must be White."
                                )
                                return (
                                    "FAIL",
                                    f"Text Rule Violation: Text on {bg_name_found}"
                                    " must be White.",
                                    [x, y, w, h],
                                )

            except Exception:
                continue

        return "PASS", "Text Colors Compliant", None

    def audit_page(self, page_pil):
        """
        Audits a single PIL Image page.
        Returns a list of dicts representing findings (logos, imagery, text).
        """
        page_results = []

        page_cv = np.array(page_pil)
        if len(page_cv.shape) == 3:
            page_gray = cv2.cvtColor(page_cv, cv2.COLOR_RGB2GRAY)
        else:
            page_gray = page_cv  # Already gray

        # 1. LOGOS (Multi-Variant)
        detected_logos = self._find_logos(page_gray)
        logo_boxes_for_mask = []

        for item in detected_logos:
            x, y, w, h = item["bbox"]
            crop = page_pil.crop((x, y, x + w, y + h))
            status, metric = self._check_logo_compliance(crop, item["variant"])

            page_results.append(
                {
                    "type": "LOGO",
                    "bbox": item["bbox"],
                    "status": status,
                    "metric": metric,
                    "variant": item["variant"]["name"],
                }
            )
            logo_boxes_for_mask.append([x, y, w, h])

        # 2. IMAGERY (Generic, masking logos)
        # img_boxes = self._find_imagery(page_gray, logo_boxes_for_mask)
        # for box in img_boxes:
        #     x, y, w, h = box
        #     crop = page_pil.crop((x, y, x + w, y + h))
        #     status, metric = self._check_imagery_vibe(crop)

        #     page_results.append(
        #         {"type": "IMAGERY", "bbox": box, "status": status, "metric": metric}
        #     )

        # 3. TEXT & UNIFIED SMART MASK
        # Use image_to_data to get bounding boxes for text masking + context awareness
        try:
            data = pytesseract.image_to_data(
                page_gray, output_type=pytesseract.Output.DICT
            )
            # pyrefly: ignore [bad-index]
            n_boxes = len(data["level"])
            text_bboxes = []  # (x, y, w, h)
            all_text_parts = []

            for i in range(n_boxes):
                # pyrefly: ignore [bad-index]
                txt = data["text"][i].strip()
                # pyrefly: ignore [missing-attribute]
                conf = int(data.get("conf", [-1])[i])
                if txt and conf > 0:
                    all_text_parts.append(txt)
                    x, y, w, h = (
                        # pyrefly: ignore [bad-index]
                        data["left"][i],
                        # pyrefly: ignore [bad-index]
                        data["top"][i],
                        # pyrefly: ignore [bad-index]
                        data["width"][i],
                        # pyrefly: ignore [bad-index]
                        data["height"][i],
                    )
                    text_bboxes.append((x, y, w, h))

            # 3a. Check Tone (using joined text)
            full_text = " ".join(all_text_parts)
            status, metric = self._check_text_voice(full_text)
            if status:
                page_results.append(
                    {
                        "type": "TEXT_BODY",
                        "bbox": [0, 0, page_pil.width, 50],
                        "status": status,
                        "metric": metric,
                    }
                )

            # 4. COLOR COMPLIANCE (Smart Masking)
            # Create Masks
            mask_text = np.zeros(page_gray.shape, dtype=np.uint8)
            for x, y, w, h in text_bboxes:
                # Fill text regions with 255 (White)
                # Dilate slightly to catch anti-aliasing
                cv2.rectangle(mask_text, (x, y), (x + w, y + h), 255, -1)

            # Mask Background = Invert Text Mask
            mask_bg = cv2.bitwise_not(mask_text)

            # 4a. Audit Background (Exclude Text) via Histogram Coverage
            # This fixes "Texture/Jolly Lush" issue
            bg_status, bg_msg = self._audit_background_layer(
                page_cv,
                mask_bg,
                self.bible.get("colors"),
            )

            page_results.append(
                {
                    "type": "PALETTE",
                    "bbox": [0, 0, 50, 50],
                    "status": bg_status,
                    "metric": bg_msg,
                }
            )

            # 4b. Audit Text Layer (Context & Contrast)
            # This enforces "White Text on Aubergine"
            txt_status, txt_msg, bad_bbox = self._audit_text_layer(
                page_cv, text_bboxes, self.bible
            )
            if txt_status == "FAIL":
                page_results.append(
                    {
                        "type": "TYPOGRAPHY",
                        "bbox": bad_bbox
                        if bad_bbox
                        else [0, 0, page_pil.width, page_pil.height],
                        "status": "FAIL",
                        "metric": txt_msg,
                    }
                )

        except Exception as e:
            print(f"Smart Audit failed: {e}")
            # Fallback (safety)
            pass

        return page_results

    def audit_page_with_layout(self, page_pil: Image.Image, layout: PageLayout):
        """
        V2 Audit: Uses structural layout analysis instead of blind OCR.
        Implements a Pipeline/Map-Reduce style architecture.
        """
        logger.info(f"V2 AUDIT START: Page Layout has {len(layout.regions)} regions.")

        page_cv = np.array(page_pil)
        if len(page_cv.shape) == 3:
            # Grayscale needed for masking (Background Audit) and SIFT
            page_gray = cv2.cvtColor(page_cv, cv2.COLOR_RGB2GRAY)
        else:
            page_gray = page_cv

        # --- PIPELINE START ---
        results = []

        # 1. Text Pipeline
        results.extend(self._pipeline_text(layout, page_pil.size))

        # 2. Image Pipeline (The Cascade)
        results.extend(self._pipeline_images(layout, page_pil))

        # 3. Background Pipeline
        results.extend(self._pipeline_background(layout, page_cv, page_gray))

        return results

    # ==========================
    # PIPELINE HELPERS
    # ==========================

    def _pipeline_text(self, layout: PageLayout, page_size) -> list:
        """Aggregates all text regions and audits Brand Voice."""
        w, h = page_size
        text_types = [LayoutType.TEXT, LayoutType.TITLE, LayoutType.SECTION_HEADER]
        text_regions = [r for r in layout.regions if r.type in text_types]

        logger.debug(f"Pipeline Text: Found {len(text_regions)} text regions.")

        full_text_parts = [
            r.content for r in text_regions if isinstance(r.content, str) and r.content
        ]

        results = []
        if full_text_parts:
            full_text = " ".join(full_text_parts)
            logger.debug(
                f"Pipeline Text: Audit Voice on {len(full_text.split())} words."
            )
            status, metric = self._check_text_voice(full_text)
            if status:
                results.append(
                    {
                        "type": "TEXT_BODY",
                        "bbox": [0, 0, w, 50],
                        "status": status,
                        "metric": metric,
                        "level": "PASS" if status == "PASS" else "WARNING",
                    }
                )
        return results

    def _pipeline_images(self, layout: PageLayout, page_pil: Image.Image) -> list:
        """Process all image regions through the Logo/Imagery Cascade."""
        # MAP: Transform regions to results (or None)
        image_regions = layout.get_regions_by_type(LayoutType.FIGURE)
        logger.debug(f"Pipeline Images: Found {len(image_regions)} figure regions.")

        results = []
        for region in image_regions:
            res = self._process_single_image_region(region, page_pil)
            if res:
                results.append(res)
        return results

    def _process_single_image_region(self, region, page_pil, pre_emb=None):
        """
        Worker for Image Pipeline - The Cascade Logic.
        If 'pre_emb' is provided, skips CLIP encoding step.
        """
        x0, y0, x1, y1 = region.bbox
        crop_box = (int(x0), int(y0), int(x1), int(y1))

        if crop_box[2] <= crop_box[0] or crop_box[3] <= crop_box[1]:
            return None

        # Optimization: use page_pil directly if it IS a crop (passed from batch)
        # But region.bbox is usually relative to page.
        # Check if page_pil size matches bbox size (indicating it is already cropped)
        if page_pil.size == (crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]):
            crop = page_pil
        else:
            crop = page_pil.crop(crop_box)

        crop_cv = np.array(crop)
        crop_gray = (
            cv2.cvtColor(crop_cv, cv2.COLOR_RGB2GRAY)
            if len(crop_cv.shape) == 3
            else crop_cv
        )

        # A. SIFT Check
        local_logos = self._find_logos(crop_gray)
        if local_logos:
            best = local_logos[0]
            status, metric = self._check_logo_compliance(crop, best["variant"])
            lx, ly, lw, lh = best["bbox"]
            logger.info(f"Pipeline Image: SIFT Match found: {best['variant']['name']}")
            return {
                "type": "LOGO",
                "bbox": [x0 + lx, y0 + ly, lw, lh],
                "status": status,
                "metric": metric,
                "variant": best["variant"]["name"],
                "level": "PASS" if status == "PASS" else "CRITICAL",
            }

        # B. CLIP Semantic Checks
        # Encode if not provided
        if pre_emb is not None:
            crop_emb = pre_emb
        else:
            with torch.no_grad():
                inputs = self.ml.clip_processor(
                    images=crop, return_tensors="pt", padding=True
                )
                crop_emb = self.ml.clip_model.get_image_features(**inputs)
                # Normalize
                crop_emb = crop_emb / crop_emb.norm(dim=-1, keepdim=True)

        # B1. Distorted Logo Check
        if self.logo_embeddings is not None:
            sims = crop_emb @ self.logo_embeddings.T
            max_sim = sims.max().item()
            if max_sim > 0.85:
                logger.warning(f"Pipeline Image: CLIP Distorted Logo ({max_sim:.2f})")
                # pyrefly: ignore [dict-item]
                return {
                    "type": "DISTORTED_LOGO",
                    "bbox": [x0, y0, x1 - x0, y1 - y0],
                    "status": "FAIL",
                    "metric": f"Potential Distorted Logo (Sim: {max_sim:.2f})",
                    "level": "WARNING",
                }

        # B2. Third-Party Check
        # Use Pre-computed if available
        if self.tp_text_feats is not None:
            txt_feats = self.tp_text_feats
        else:
            # Fallback (old slow way)
            prompts = ["a logo", "a photograph", "generic imagery", "text screenshot"]
            txt_inputs = self.ml.clip_processor(
                text=prompts, return_tensors="pt", padding=True
            )
            with torch.no_grad():
                txt_feats = self.ml.clip_model.get_text_features(**txt_inputs)
                txt_feats /= txt_feats.norm(dim=-1, keepdim=True)

        probs = ((crop_emb @ txt_feats.T) * 100).softmax(dim=-1)[0]
        if probs[0].item() > probs[1].item():
            logger.info("Pipeline Image: Detected Third-Party Logo")
            return {
                "type": "THIRD_PARTY_LOGO",
                "bbox": [x0, y0, x1 - x0, y1 - y0],
                "status": "PASS",
                "metric": "External/Partner Logo detected",
                "level": "INFO",
            }

        # C. Default Imagery Audit
        status, metric = self._check_imagery_vibe(crop)
        logger.debug(f"Pipeline Image: Generic Vibe Check -> {status}")
        return {
            "type": "IMAGERY",
            "bbox": [x0, y0, x1 - x0, y1 - y0],
            "status": status,
            "metric": metric,
            "level": "PASS" if status == "PASS" else "MEDIUM",
        }

    def _pipeline_background(self, layout: PageLayout, page_cv, page_gray) -> list:
        """Generates masks from layout and audits background compliance."""
        mask_bg = np.zeros(page_gray.shape, dtype=np.uint8) + 255  # Start White

        # Mask out ALL content regions
        for r in layout.regions:
            rx0, ry0, rx1, ry1 = r.bbox
            cv2.rectangle(mask_bg, (int(rx0), int(ry0)), (int(rx1), int(ry1)), 0, -1)

        bg_status, bg_msg = self._audit_background_layer(
            page_cv, mask_bg, self.bible.get("colors")
        )

        return [
            {
                "type": "PALETTE",
                "bbox": [0, 0, 50, 50],
                "status": bg_status,
                "metric": bg_msg,
                "level": "PASS" if bg_status == "PASS" else "MEDIUM",
            }
        ]

    def audit_pdf(self, pdf_path):
        print(f"Auditing: {pdf_path}...")
        try:
            pages = convert_from_path(pdf_path)
        except Exception as e:
            return [f"Error: {e}"]

        report = []

        for i, page_pil in enumerate(pages):
            print(f" > Processing Page {i + 1}...")
            items = self.audit_page(page_pil)
            page_data = {"page": i + 1, "items": items}
            report.append(page_data)

        return report
