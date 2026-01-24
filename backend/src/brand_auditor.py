import cv2
import numpy as np
from sklearn.cluster import KMeans
import colorsys
import pytesseract
from pdf2image import convert_from_path
from PIL import ImageStat, Image
from transformers import CLIPModel, CLIPProcessor, pipeline


class IntegratedBrandAuditor:
    def __init__(self, brand_bible, reference_assets):
        self.bible = brand_bible

        # --- 1. SETUP AI MODELS ---
        print("Loading AI Models (CLIP, NLP, SIFT)...")
        self.sift = cv2.SIFT_create()
        self.nlp_pipe = pipeline(
            "zero-shot-classification", model="facebook/bart-large-mnli"
        )
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained(
            "openai/clip-vit-base-patch32"
        )

        # --- 2. INDEX LOGO VARIANTS ---
        # We index every single logo file provided in the training assets
        self.logo_variants = []
        logo_imgs = [x for x in reference_assets if x["type"] == "LOGO"]

        print(f"Indexing {len(logo_imgs)} Logo Variants...")
        for i, item in enumerate(logo_imgs):
            pil_img = item["image"]

            # --- FIX: Handle file paths if passed instead of PIL objects ---
            if isinstance(pil_img, str):
                try:
                    pil_img = Image.open(pil_img).convert("RGB")
                except Exception as e:
                    print(f"Failed to load logo variant {item.get('filename')}: {e}")
                    continue
            # ---------------------------------------------------------------

            filename = item.get("filename", f"variant_{i}")

            # Convert to Grayscale for SIFT
            img_cv = np.array(pil_img)
            if len(img_cv.shape) == 3:
                img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)

            kp, des = self.sift.detectAndCompute(img_cv, None)

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
                        "original_image": pil_img,  # Keep for color comparison
                    }
                )

    # ==================================================
    # PHASE 1: LOGO DETECTION (Multi-Variant SIFT)
    # ==================================================
    def _find_logos(self, page_cv_gray):
        found_instances = []

        kp_page, des_page = self.sift.detectAndCompute(page_cv_gray, None)
        if des_page is None:
            return []

        flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))

        # Check against EVERY variant
        for variant in self.logo_variants:
            matches = flann.knnMatch(variant["des"], des_page, k=2)
            good = [m for m, n in matches if m.distance < 0.65 * n.distance]

            if len(good) > 15:
                src_pts = np.float32(
                    [variant["kp"][m.queryIdx].pt for m in good]
                ).reshape(-1, 1, 2)
                dst_pts = np.float32([kp_page[m.trainIdx].pt for m in good]).reshape(
                    -1, 1, 2
                )

                M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                if M is not None:
                    h, w = variant["size"][1], variant["size"][0]
                    pts = np.float32(
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
        targets = f"a photo that is {', '.join(self.bible['frequent_keywords'])}"
        negative = "cartoon, blurry, text overlay, screenshot, low resolution"

        inputs = self.clip_processor(
            text=[targets, negative], images=img_crop, return_tensors="pt", padding=True
        )
        probs = self.clip_model(**inputs).logits_per_image.softmax(dim=1)
        score = probs[0][0].item()

        return "PASS" if score > 0.6 else "FAIL", f"Vibe Score: {score:.2%}"

    # ==================================================
    # PHASE 3: TEXT (Voice)
    # ==================================================
    def _check_text_voice(self, text):
        if len(text.split()) < 10:
            return None, None
        labels = self.bible["brand_voice_attributes"] + ["spammy", "aggressive"]
        res = self.nlp_pipe(text, labels)
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
        # 1. Get Allowed Colors from Brand Kit
        # Priority: rich_colors matches (best) -> primary_colors (hex)
        allowed_rgbs = []
        
        if self.bible.get('rich_colors'):
            # Extract RGBs from rich data
            for c in self.bible['rich_colors']:
                if 'rgb' in c and c['rgb']:
                    # Parse "74-21-75" or similar format if needed? 
                    # The extractor might return it as string or tuple. 
                    # Let's assume the extractor returns sanitized strings or we verify.
                    # Actually, let's look at api.py/extractor structure. 
                    # For now, let's try to handle the string "R-G-B" or [R, G, B]
                    try:
                        val = c['rgb']
                        if isinstance(val, str):
                            # Handle "74-21-75" or "74, 21, 75"
                            parts = val.replace(',', ' ').replace('-', ' ').split()
                            allowed_rgbs.append([float(p) for p in parts])
                        elif isinstance(val, list):
                            allowed_rgbs.append(val)
                    except Exception:
                        pass
        
        # Fallback to Hex if no RGBs found (or added as well)
        if not allowed_rgbs and self.bible.get('primary_colors'):
            for hex_code in self.bible['primary_colors']:
                h = hex_code.lstrip('#')
                try:
                    rgb = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
                    allowed_rgbs.append(rgb)
                except Exception:
                    pass

        if not allowed_rgbs:
            return "WARNING", "No Brand Colors defined in Kit."

        # 2. Check each dominant color
        violations = []
        tolerance = 80.0 # Euclidean distance threshold (Increased for textures)
        
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
                dom_hex = "#{:02x}{:02x}{:02x}".format(int(dom[0]), int(dom[1]), int(dom[2]))
                violations.append(dom_hex)

        if violations:
            return "FAIL", f"Off-brand colors detected: {', '.join(violations[:3])}"
        
        return "PASS", "Palette compliant"
    def _audit_background_layer(self, page_cv, bg_mask, rich_colors, primary_colors):
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
        allowed_rgbs = []
        if rich_colors:
            for rc in rich_colors:
                try:
                    if rc.get("rgb"):
                         # Clean format "R, G, B" or "R-G-B"
                         val = rc["rgb"].replace(',', ' ').replace('-', ' ')
                         allowed_rgbs.append([float(p) for p in val.split()])
                except: pass
        if not allowed_rgbs and primary_colors:
             for hex_code in primary_colors:
                try:
                    h = hex_code.lstrip('#')
                    allowed_rgbs.append(tuple(int(h[i:i+2], 16) for i in (0, 2, 4)))
                except: pass

        if not allowed_rgbs:
            return "WARNING", "No Brand Colors defined"

        # 3. Vote (Histogram Coverage)
        # Count how many pixels are "close enough" to ANY brand color
        match_count = 0
        tolerance = 45.0 # Stricter than K-Means because no averaging
        
        for pix in bg_pixels:
            # Distance to nearest brand color
            min_dist = float('inf')
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
        """
        usage_rules = brand_kit.get("color_usage_rules", [])
        if not usage_rules:
            return "PASS", "No Text Rules defined", None

        # Prepare rules lookup
        # e.g. "aubergine" -> allowed=["white"]
        
        # Simplistic check for now: 
        # For each text box, determine Text Color and Local BG Color
        violations = []
        
        for (x, y, w, h) in text_bboxes:
            if w < 5 or h < 5: continue
            
            # Extract Text ROI
            roi = page_cv[y:y+h, x:x+w]
            
            # 1. Determine Local Background (just outside the box?)
            # Or assume the "Text Color" is the foreground and "BG" is the rest
            # Use Otsu's thresholding to separate FG/BG
            try:
                gray_roi = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
                _, mask = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # FG (Text) = pixels where mask is 0 (Black) usually involved with dark text on light?
                # Actually Otsu makes one class 0 and other 255.
                # Let's assume Text is the Minority Class usually?
                num_zeros = np.count_nonzero(mask == 0)
                num_ones = np.count_nonzero(mask == 255)
                
                if num_zeros < num_ones:
                    fg_mask = (mask == 0)
                    bg_mask = (mask == 255)
                else:
                    fg_mask = (mask == 255)
                    bg_mask = (mask == 0)

                fg_pixels = roi[fg_mask]
                bg_pixels = roi[bg_mask]
                
                if len(fg_pixels) == 0 or len(bg_pixels) == 0: continue

                # Average Colors
                text_color = np.mean(fg_pixels, axis=0) # R,G,B
                bg_color = np.mean(bg_pixels, axis=0) # R,G,B
                
                # 2. Check Rules
                # We need to map "bg_color" (RGB) to a Name (e.g. "Aubergine")
                # Find closest named brand color
                bg_name_found = None
                
                if brand_kit.get("rich_colors"):
                    min_d = float('inf')
                    for rc in brand_kit["rich_colors"]:
                         try:
                             val = rc["rgb"].replace(',', ' ').replace('-', ' ')
                             ref_rgb = [float(p) for p in val.split()]
                             d = sum([(a-b)**2 for a,b in zip(bg_color, ref_rgb)])**0.5
                             if d < min_d:
                                 min_d = d
                                 bg_name_found = rc["name"]
                         except: pass
                
                # If we found a background name, check strict rules
                if bg_name_found:
                    for rule in usage_rules:
                        # Fuzzy match name? "Aubergine" vs "Core Aubergine"
                        if rule["background_color"].lower() in bg_name_found.lower():
                            # Enforce allowed text colors
                            # This is tricky without knowing what "White" RGB is exactly.
                            # Assume "White" means > 240, 240, 240
                            
                            allowed = [c.lower() for c in rule["allowed_text_colors"]]
                            
                            # Use 95th Percentile to ignore anti-aliased edges
                            text_p95 = np.percentile(fg_pixels, 95, axis=0)
                            
                            def get_lum(c): return 0.299*c[0] + 0.587*c[1] + 0.114*c[2]
                            t_lum = get_lum(text_p95)
                            bg_lum = get_lum(bg_color)
                            
                            # Saturation
                            c_max, c_min = np.max(text_p95), np.min(text_p95)
                            sat = (c_max - c_min) / c_max if c_max > 0 else 0
                            
                            is_strict_white = all(c > 200 for c in text_p95)
                            
                            # Robust White: High Brightness (>140), High Contrast vs BG (>60), Low Saturation (<0.2)
                            is_robust_white = (t_lum > 140) and (t_lum - bg_lum > 60) and (sat < 0.20)
                            
                            if "white" in allowed and not (is_strict_white or is_robust_white):
                                violations.append(f"Text on {bg_name_found} must be White.")
                                return "FAIL", f"Text Rule Violation: Text on {bg_name_found} must be White.", [x,y,w,h]

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
        img_boxes = self._find_imagery(page_gray, logo_boxes_for_mask)
        for box in img_boxes:
            x, y, w, h = box
            crop = page_pil.crop((x, y, x + w, y + h))
            status, metric = self._check_imagery_vibe(crop)

            page_results.append(
                {"type": "IMAGERY", "bbox": box, "status": status, "metric": metric}
            )

        # 3. TEXT & UNIFIED SMART MASK
        # Use image_to_data to get bounding boxes for text masking + context awareness
        try:
            data = pytesseract.image_to_data(page_gray, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['level'])
            text_bboxes = [] # (x, y, w, h)
            all_text_parts = []
            
            for i in range(n_boxes):
                txt = data['text'][i].strip()
                conf = int(data.get('conf', [-1])[i])
                if txt and conf > 0:
                    all_text_parts.append(txt)
                    x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
                    text_bboxes.append((x, y, w, h))
            
            # 3a. Check Tone (using joined text)
            full_text = " ".join(all_text_parts)
            status, metric = self._check_text_voice(full_text)
            if status:
                page_results.append({
                    "type": "TEXT_BODY",
                    "bbox": [0,0, page_pil.width, 50],
                    "status": status,
                    "metric": metric
                })

            # 4. COLOR COMPLIANCE (Smart Masking)
            # Create Masks
            mask_text = np.zeros(page_gray.shape, dtype=np.uint8)
            for (x, y, w, h) in text_bboxes:
                # Fill text regions with 255 (White)
                # Dilate slightly to catch anti-aliasing
                cv2.rectangle(mask_text, (x, y), (x + w, y + h), 255, -1)
            
            # Mask Background = Invert Text Mask
            mask_bg = cv2.bitwise_not(mask_text)

            # 4a. Audit Background (Exclude Text) via Histogram Coverage
            # This fixes "Texture/Jolly Lush" issue
            bg_status, bg_msg = self._audit_background_layer(page_cv, mask_bg, self.bible.get('rich_colors'), self.bible.get('primary_colors'))
            
            page_results.append({
                "type": "PALETTE",
                "bbox": [0, 0, 50, 50],
                "status": bg_status,
                "metric": bg_msg
            })

            # 4b. Audit Text Layer (Context & Contrast)
            # This enforces "White Text on Aubergine"
            txt_status, txt_msg, bad_bbox = self._audit_text_layer(page_cv, text_bboxes, self.bible)
            if txt_status == "FAIL":
                 page_results.append({
                    "type": "TYPOGRAPHY",
                    "bbox": bad_bbox if bad_bbox else [0, 0, page_pil.width, page_pil.height],
                    "status": "FAIL",
                    "metric": txt_msg
                })

        except Exception as e:
            print(f"Smart Audit failed: {e}")
            # Fallback (safety)
            pass

        return page_results

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
