import cv2
import numpy as np
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
        self.nlp_pipe = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        # --- 2. INDEX LOGO VARIANTS ---
        # We index every single logo file provided in the training assets
        self.logo_variants = []
        logo_imgs = [x for x in reference_assets if x['type'] == 'LOGO']

        print(f"Indexing {len(logo_imgs)} Logo Variants...")
        for i, item in enumerate(logo_imgs):
            pil_img = item['image']
            
            # --- FIX: Handle file paths if passed instead of PIL objects ---
            if isinstance(pil_img, str):
                try:
                    pil_img = Image.open(pil_img).convert("RGB")
                except Exception as e:
                    print(f"Failed to load logo variant {item.get('filename')}: {e}")
                    continue
            # ---------------------------------------------------------------

            filename = item.get('filename', f"variant_{i}")

            # Convert to Grayscale for SIFT
            img_cv = np.array(pil_img)
            if len(img_cv.shape) == 3: img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)

            kp, des = self.sift.detectAndCompute(img_cv, None)

            if des is not None:
                w, h = pil_img.size
                self.logo_variants.append({
                    "id": i,
                    "name": filename,
                    "kp": kp,
                    "des": des,
                    "size": (w, h),
                    "aspect_ratio": w / h,
                    "original_image": pil_img # Keep for color comparison
                })

    # ==================================================
    # PHASE 1: LOGO DETECTION (Multi-Variant SIFT)
    # ==================================================
    def _find_logos(self, page_cv_gray):
        found_instances = []

        kp_page, des_page = self.sift.detectAndCompute(page_cv_gray, None)
        if des_page is None: return []

        flann = cv2.FlannBasedMatcher(dict(algorithm=1, trees=5), dict(checks=50))

        # Check against EVERY variant
        for variant in self.logo_variants:
            matches = flann.knnMatch(variant['des'], des_page, k=2)
            good = [m for m, n in matches if m.distance < 0.65 * n.distance]

            if len(good) > 15:
                src_pts = np.float32([variant['kp'][m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
                dst_pts = np.float32([kp_page[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

                M, _ = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                if M is not None:
                    h, w = variant['size'][1], variant['size'][0]
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)

                    x = int(min(dst[:, 0, 0]))
                    y = int(min(dst[:, 0, 1]))
                    w_new = int(max(dst[:, 0, 0])) - x
                    h_new = int(max(dst[:, 0, 1])) - y

                    # Sanity Checks (Size & Ratio)
                    if w_new < 30 or h_new < 30: continue

                    detected_ratio = w_new / h_new
                    ref_ratio = variant['aspect_ratio']

                    # Allow 25% distortion
                    if not (ref_ratio * 0.75 < detected_ratio < ref_ratio * 1.25):
                        continue

                    found_instances.append({
                        "variant": variant,
                        "bbox": [x, y, w_new, h_new],
                        "match_score": len(good)
                    })

        return self._deduplicate_matches(found_instances)

    def _deduplicate_matches(self, instances):
        """If multiple variants match the same spot, pick the best one."""
        if not instances: return []
        instances.sort(key=lambda x: x['match_score'], reverse=True)
        unique = []
        for cand in instances:
            cx, cy, _, _ = cand['bbox']
            is_overlap = False
            for exist in unique:
                ex, ey, _, _ = exist['bbox']
                # Simple distance check for overlap
                if abs(cx - ex) < 50 and abs(cy - ey) < 50:
                    is_overlap = True
                    break
            if not is_overlap: unique.append(cand)
        return unique

    def _check_logo_compliance(self, crop, variant_data):
        # 1. Ratio Check
        w, h = crop.size
        det_ratio = w / h
        ref_ratio = variant_data['aspect_ratio']
        ratio_pass = abs(det_ratio - ref_ratio) < 0.2

        # 2. Color Check (Compare against specific variant reference)
        crop_stat = ImageStat.Stat(crop)
        ref_stat = ImageStat.Stat(variant_data['original_image'])
        # Euclidean distance of RGB averages
        dist = sum([(a - b)**2 for a, b in zip(crop_stat.mean[:3], ref_stat.mean[:3])]) ** 0.5
        color_pass = dist < 65.0 # Tolerance

        status = "PASS" if (ratio_pass and color_pass) else "FAIL"
        return status, f"Matches {variant_data['name']}"

    # ==================================================
    # PHASE 2: IMAGERY DETECTION (Generic with Masking)
    # ==================================================
    def _find_imagery(self, page_cv_gray, mask_boxes):
        clean_page = page_cv_gray.copy()
        # Paint logos white to hide them
        for (x, y, w, h) in mask_boxes:
            cv2.rectangle(clean_page, (x, y), (x+w, y+h), (255), -1)

        thresh = cv2.adaptiveThreshold(clean_page, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 11, 2)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
        dilated = cv2.dilate(thresh, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        found_imgs = []
        page_area = clean_page.shape[0] * clean_page.shape[1]
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if w < 100 or h < 100: continue
            if (w * h) > (page_area * 0.9): continue
            found_imgs.append([x, y, w, h])
        return found_imgs

    def _check_imagery_vibe(self, img_crop):
        targets = f"a photo that is {', '.join(self.bible['frequent_keywords'])}"
        negative = "cartoon, blurry, text overlay, screenshot, low resolution"

        inputs = self.clip_processor(text=[targets, negative], images=img_crop, return_tensors="pt", padding=True)
        probs = self.clip_model(**inputs).logits_per_image.softmax(dim=1)
        score = probs[0][0].item()

        return "PASS" if score > 0.6 else "FAIL", f"Vibe Score: {score:.2%}"

    # ==================================================
    # PHASE 3: TEXT (Voice)
    # ==================================================
    def _check_text_voice(self, text):
        if len(text.split()) < 10: return None, None
        labels = self.bible['brand_voice_attributes'] + ["spammy", "aggressive"]
        res = self.nlp_pipe(text, labels)
        top = res['labels'][0]
        return "PASS" if top in self.bible['brand_voice_attributes'] else "WARNING", f"Tone: {top}"

    # ==================================================
    # MAIN EXECUTION
    # ==================================================
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
            page_gray = page_cv # Already gray

        # 1. LOGOS (Multi-Variant)
        detected_logos = self._find_logos(page_gray)
        logo_boxes_for_mask = []

        for item in detected_logos:
            x, y, w, h = item['bbox']
            crop = page_pil.crop((x, y, x+w, y+h))
            status, metric = self._check_logo_compliance(crop, item['variant'])

            page_results.append({
                "type": "LOGO",
                "bbox": item['bbox'],
                "status": status,
                "metric": metric,
                "variant": item['variant']['name']
            })
            logo_boxes_for_mask.append([x, y, w, h])

        # 2. IMAGERY (Generic, masking logos)
        img_boxes = self._find_imagery(page_gray, logo_boxes_for_mask)
        for box in img_boxes:
            x, y, w, h = box
            crop = page_pil.crop((x, y, x+w, y+h))
            status, metric = self._check_imagery_vibe(crop)

            page_results.append({
                "type": "IMAGERY",
                "bbox": box,
                "status": status,
                "metric": metric
            })

        # 3. TEXT
        text = pytesseract.image_to_string(page_gray)
        status, metric = self._check_text_voice(text)
        if status:
            page_results.append({
                "type": "TEXT_BODY",
                "bbox": [0,0,page_pil.width, 50],
                "status": status,
                "metric": metric
            })
            
        return page_results

    def audit_pdf(self, pdf_path):
        print(f"Auditing: {pdf_path}...")
        try: pages = convert_from_path(pdf_path)
        except Exception as e: return [f"Error: {e}"]

        report = []

        for i, page_pil in enumerate(pages):
            print(f" > Processing Page {i+1}...")
            items = self.audit_page(page_pil)
            page_data = {"page": i+1, "items": items}
            report.append(page_data)

        return report

if __name__ == "__main__":
    
    # 1. Initialize
    # pass in your generated bible and the list of classified assets
    auditor = IntegratedBrandAuditor(brand_kit, assets_for_learning)

    # 2. Run Audit on PDF
    pdf_path = "Humanitarians AI LANDING.pdf"
    results = auditor.audit_pdf(pdf_path)

    # 3. Visualize
    # Using the existing visualization function we wrote earlier
    if isinstance(results[0], dict):
        # Re-using the logic, but adding support for the new 'variant' key in label
        visualize_audit_results(pdf_path, results) # Use the simpler visualizer from before
    else:
        print(results)
