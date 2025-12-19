import requests
from PIL import Image
from io import BytesIO
from transformers import CLIPProcessor, CLIPModel
import torch

class AssetClassifier():
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_id = "openai/clip-vit-base-patch32"
        self.model = CLIPModel.from_pretrained(self.model_id).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(self.model_id)

        # --- IMPROVED PROMPTS ---
        self.labels = {
            "LOGO": [
                "a brand logo",
                "a company logotype or wordmark", # Explicitly mention Wordmarks
                "a graphic icon or symbol",
                "white text logo on black background", # Handle the specific failure case
                "black text logo on white background",
                "a stylized brand name"
            ],
            "TYPOGRAPHY": [
                "a font specimen sheet", # Be specific: it's a sheet, not just text
                "an alphabet grid of letters",
                "a page containing lorem ipsum text",
                "typography guidelines showing font weights",
                "a document with multiple paragraphs"
            ],
            "IMAGERY": ["a photograph", "lifestyle imagery", "stock photo of people"],
            "TEMPLATE": ["a layout design", "marketing flyer", "social media post template"]
        }

        self.flat_labels = [item for sublist in self.labels.values() for item in sublist]
        self.label_map = [key for key, val in self.labels.items() for _ in val]
    def _load_image(self, image_source):
        """
        Smart loader that handles:
        1. PIL Image Objects (from Zip Generator)
        2. URLs
        3. Local file paths
        """
        try:
            # --- FIX STARTS HERE ---
            # 1. Check if input is ALREADY a PIL Image
            if isinstance(image_source, Image.Image):
                return image_source.convert('RGB'), "OK"
            # --- FIX ENDS HERE ---

            # 2. Handle URL strings
            if isinstance(image_source, str) and image_source.startswith('http'):
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(image_source, headers=headers, timeout=10)
                if "svg" in response.headers.get("Content-Type", ""):
                    return None, "SVG_DETECTED"
                img = Image.open(BytesIO(response.content))

            # 3. Handle Local File strings
            else:
                if isinstance(image_source, str) and image_source.endswith(".svg"):
                    return None, "SVG_DETECTED"
                img = Image.open(image_source)

            return img.convert('RGB'), "OK"

        except Exception as e:
            return None, str(e)

    def predict_type(self, image_source):
        img, status = self._load_image(image_source)

        if status == "SVG_DETECTED":
            return "LOGO", 1.0

        if img is None:
            print(f"Error loading image: {status}")
            return None, 0.0

        # Process inputs
        inputs = self.processor(
            text=self.flat_labels,
            images=img,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        probs = outputs.logits_per_image.softmax(dim=1)
        best_idx = probs.argmax().item()

        return self.label_map[best_idx], probs[0][best_idx].item()

    def predict_types_batch(self, image_sources: list):
        """Process multiple images in a single forward pass."""
        images = []
        statuses = []
        
        for src in image_sources:
            img, status = self._load_image(src)
            if status == "SVG_DETECTED":
                statuses.append(("LOGO", 1.0))
            elif img is None:
                statuses.append((None, 0.0))
            else:
                images.append(img)
                statuses.append(None)  # Placeholder for batch result
        
        if not images:
            return statuses
        
        # Process all images in one batch
        inputs = self.processor(
            text=self.flat_labels,
            images=images,  # List of images
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
        
        # logits_per_image is now (batch_size, num_labels)
        probs = outputs.logits_per_image.softmax(dim=1)
        
        # Map results back
        batch_idx = 0
        results = []
        for status in statuses:
            if status is not None:
                results.append(status)
            else:
                best_idx = probs[batch_idx].argmax().item()
                conf = probs[batch_idx][best_idx].item()
                results.append((self.label_map[best_idx], conf))
                batch_idx += 1
        
        return results

if __name__ == "__main__":

    print("Hello World")
    classifier = AssetClassifier()

    # Example 1: Logo
    img_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Google_2015_logo.svg/1200px-Google_2015_logo.svg.png"

    # Example 2: Lifestyle Image
    img2_url = "https://images.unsplash.com/photo-1517048676732-d65bc937f952"

    out = classifier.predict_types_batch([img_url, img2_url])

    for category, conf in out:
        print(f"Prediction: {category}")
        print(f"Confidence: {conf:.2%}")

        # ROUTING LOGIC
        if category == "LOGO":
            print(">> Routing to Logo Geometry Checker...")
        elif category == "IMAGERY":
            print(">> Routing to Moodboard Validator...")
