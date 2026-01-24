from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from pdf2image import convert_from_bytes
from PIL import Image
import uuid
import shutil
from pathlib import Path
import json
import datetime

from .asset_classifier import AssetClassifier
from .brand_guideline_generator import BrandGuidelineGenerator
from .brand_guideline_extractor import BrandGuidelineExtractor
from .brand_auditor import IntegratedBrandAuditor


class InspectionResult(BaseModel):
    id: str
    pageNumber: int
    type: str  # 'COLOR', 'FONT', 'LOGO', etc.
    message: str
    level: str  # 'CRITICAL', 'MEDIUM', 'PASS'
    status: str  # 'FAIL', 'PASS'
    coordinates: dict  # {x, y, width, height}


class AuditResponse(BaseModel):
    projectId: str
    title: str
    violations: List[InspectionResult]
    score: int
    status: str  # 'COMPLIANT', 'CRITICAL', 'ACTION_REQUIRED'


# Initialize Extractor
guideline_extractor = BrandGuidelineExtractor()

app = FastAPI(title="BrandGuardAI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory to serve files (optional but good for debugging/frontend)
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# Persistence Setup
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
STORE_FILE = DATA_DIR / "store.json"

# In-memory store
brand_kit_store: dict = {}
project_store: dict = {}  # New store for projects


def load_store():
    global brand_kit_store, project_store
    if STORE_FILE.exists():
        try:
            with open(STORE_FILE, "r") as f:
                data = json.load(f)
                brand_kit_store = data.get("brand_kits", {})
                project_store = data.get("projects", {})
            print(
                f"Loaded {len(brand_kit_store)} brand kits and {len(project_store)} projects from disk."
            )
        except Exception as e:
            print(f"Failed to load store: {e}")


def save_store():
    try:
        data = {"brand_kits": brand_kit_store, "projects": project_store}
        with open(STORE_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Failed to save store: {e}")


# Load on startup
load_store()

classifier = AssetClassifier()
# classifier (loaded globally or on demand)


@app.post("/brandkit")
async def create_brandkit(
    id: str = Form(...), title: str = Form(...), files: List[UploadFile] = File(...)
):
    """Create brand kit and store classified assets."""
    assets_for_learning = []
    stored_assets = []

    # Create a directory for this brand kit
    kit_dir = UPLOAD_DIR / id
    kit_dir.mkdir(parents=True, exist_ok=True)

    print("Phase 1: Learning from Assets...")

    extracted_rules = None  # [NEW] to hold PDF data

    for f in files:
        # Save file to disk
        file_path = kit_dir / f.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)

        # [NEW] Check for Guidelines PDF
        if f.filename.lower().endswith(".pdf"):
            print(f"Detected potential Brand Guidelines: {f.filename}")
            try:
                # Attempt to extract rules
                print(">>> Running Brand Guideline Extractor...")
                extracted_rules = guideline_extractor.extract_guidelines(str(file_path))
                print(">>> Extraction Complete.")
            except Exception as e:
                print(f"Failed to extract guidelines from PDF: {e}")

            # We also treat it as an asset?
            # Or skip classification for PDF?
            # Let's say we assume a PDF is Guidelines and NOT an image asset for classification
            # unless we convert it. For now, let's categorize it explicitly.
            category = "GUIDELINES"
            confidence = 1.0
        else:
            # Standard Classification
            category, confidence = classifier.predict_type(str(file_path))

        print(f"Result: {category} ({confidence:.2%})")
        print("-" * 30)

        # Asset object for internal logic
        # We need to reload the image for the generator if it expects PIL images
        try:
            # Only attempt to open as image if it's likely an image
            if category in ["LOGO", "IMAGERY", "TEMPLATE"]:
                img = Image.open(file_path).convert("RGB")
                assets_for_learning.append({"image": img, "type": category})
            else:
                pass
        except Exception as e:
            print(
                f"Skipping {f.filename} for guideline generation (not a readable image): {e}"
            )

        stored_assets.append(
            {
                "id": str(uuid.uuid4()),
                "filename": f.filename,
                "category": category,
                "path": str(file_path),
                "url": f"/uploads/{id}/{f.filename}",
            }
        )

    # ==========================================
    # 2. GENERATE GUIDELINES
    # ==========================================
    generator = BrandGuidelineGenerator()

    # Pass the extracted_rules to the generator [NEW]
    brand_kit = generator.generate_brand_kit(
        assets_for_learning, extracted_rules=extracted_rules
    )

    print("brand_kit \n", brand_kit)
    if not hasattr(brand_kit, "color_tolerance"):
        print("adding color_tolerance key into brand_kit")
        brand_kit["color_tolerance"] = 50

    if not hasattr(brand_kit, "frequent_keywords"):
        print("adding frequent_keywords key into brand_kit")
        brand_kit["frequent_keywords"] = [
            "minimalist",
            "technology",
            "humanitarian",
            "clean",
        ]

    # Merge our stored assets into the brand_kit dict
    brand_kit["id"] = id
    brand_kit["title"] = title
    brand_kit["assets"] = stored_assets

    brand_kit["date"] = datetime.datetime.now().strftime("%b %d, %Y")

    brand_kit_store[id] = brand_kit
    save_store()  # PERSIST
    return brand_kit


@app.post("/project/audit", response_model=AuditResponse)
async def audit_project(
    id: str = Form(...),
    title: str = Form(...),
    brand_kit_id: str = Form(...),
    file: UploadFile = File(...),
):
    """Audit a PDF against a brand kit's assets."""

    # 1. Retrieve brand kit
    brand_kit = brand_kit_store.get(brand_kit_id)
    if not brand_kit:
        raise HTTPException(
            status_code=404, detail=f"Brand kit '{brand_kit_id}' not found"
        )

    # 2. Read PDF
    pdf_bytes = await file.read()

    try:
        pages = convert_from_bytes(pdf_bytes, dpi=150)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process PDF: {str(e)}")

    # 3. Initialize auditor with brand kit assets
    reference_assets = brand_kit["assets"]

    # Prepare assets for auditor
    assets_for_auditor = []
    has_logos = False
    for asset in reference_assets:
        assets_for_auditor.append({"image": asset["path"], "type": asset["category"]})
        if asset["category"] == "LOGO":
            has_logos = True

    # If no logos, we might normally return empty, but now we might want to audit generic things
    # But current auditor relies on logos for initialization partly?
    # Let's just proceed. The auditor logic handles empty logos gracefully mostly or we check:
    if not has_logos:
        # Still audit text etc? The original code returned empty.
        # Let's stick to original behavior for now if absolutely required, OR proceed.
        # BrandAuditor init does loop over logos. If empty, logo_variants is empty.
        pass

    auditor = IntegratedBrandAuditor(brand_kit, assets_for_auditor)

    # 4. Audit each page
    all_results: List[InspectionResult] = []

    for page_num, page_img in enumerate(pages, start=1):
        # Now returns list of dicts, including PASS items
        results = auditor.audit_page(page_img)

        page_w, page_h = page_img.size

        for r in results:
            x, y, w, h = r["bbox"]
            status = r["status"]

            # Determine severity
            if status == "PASS":
                level = "PASS"
            else:
                level = "MEDIUM"
                if "ratio" in r["metric"].lower() and "0.3" in r["metric"]:
                    level = "CRITICAL"

            # Normalize coordinates to 0-1 range
            # Ensure we don't divide by zero (unlikely for a page)
            norm_x = x / page_w
            norm_y = y / page_h
            norm_w = w / page_w
            norm_h = h / page_h

            result_item = InspectionResult(
                id=str(uuid.uuid4()),
                pageNumber=page_num,
                type=r["type"],
                message=f"{r['type']}: {r['metric']}",
                level=level,
                status=status,
                coordinates={
                    "x": norm_x,
                    "y": norm_y,
                    "width": norm_w,
                    "height": norm_h,
                },
            )
            all_results.append(result_item)

    # 5. Calculate score
    critical_count = sum(1 for v in all_results if v.level == "CRITICAL")
    medium_count = sum(1 for v in all_results if v.level == "MEDIUM")

    # Don't penalize PASS items
    score = max(0, 100 - (critical_count * 20) - (medium_count * 10))

    if critical_count > 0:
        overall_status = "CRITICAL"
    elif medium_count > 0:
        overall_status = "ACTION_REQUIRED"  # Fixed logic
    else:
        overall_status = "COMPLIANT"

    # === PERSISTENCE LOGIC START ===
    project_data = {
        "id": id,
        "title": title,
        "date": datetime.datetime.now().strftime("%b %d, %Y"),
        "status": overall_status,
        "score": score,
        "brandKitId": brand_kit_id,
        "files": [
            {
                "id": str(uuid.uuid4()),
                "name": file.filename,
                "url": f"/uploads/projects/{id}/{file.filename}",
                "status": "ready",
                "violations": [v.dict() for v in all_results],
                "uploadDate": datetime.datetime.now().strftime("%m/%d/%Y"),
            }
        ],
    }

    # Save PDF to disk for viewing
    project_dir = UPLOAD_DIR / "projects" / id
    project_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = project_dir / file.filename

    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    project_store[id] = project_data
    save_store()
    # === PERSISTENCE LOGIC END ===

    return AuditResponse(
        projectId=id,
        title=title,
        violations=all_results,
        score=score,
        status=overall_status,
    )


@app.get("/brandkits")
def list_brandkits():
    """List all brand kits."""
    return list(brand_kit_store.values())


@app.get("/projects")
def list_projects():
    """List all projects."""
    return list(project_store.values())
