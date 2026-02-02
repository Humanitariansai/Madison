import asyncio
import os
import shutil
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pdf2image import convert_from_bytes
from PIL import Image
from pydantic import BaseModel
from sqlalchemy.orm import selectinload
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from .asset_classifier import AssetClassifier
from .brand_auditor import IntegratedBrandAuditor
from .brand_guideline_extractor import BrandGuidelineExtractor
from .brand_guideline_generator import BrandGuidelineGenerator
from .database import get_session, init_db
from .middleware import ProcessTimeMiddleware
from .models import (
    Asset,
    BrandColor,
    BrandFont,
    BrandKit,
    BrandKitRead,
    Project,
    ProjectFile,
    ProjectFileRead,
    ProjectRead,
)
from .typography.auditor import TypographyAuditor
from .typography.siamese_manager import SiameseManager
from .utils import downsample_image


class InspectionResult(BaseModel):
    id: str
    pageNumber: int
    type: str
    message: str
    level: str
    status: str
    coordinates: dict


class AuditResponse(BaseModel):
    projectId: str
    title: str
    violations: List[InspectionResult]
    score: int
    status: str


# Initialize Extractor
guideline_extractor = BrandGuidelineExtractor()


# Lifespan event to init DB
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB tables exist
    await init_db()
    yield


app = FastAPI(title="BrandGuideAI", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ProcessTimeMiddleware)

# Mount uploads directory
UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

classifier = AssetClassifier()
siamese_manager = SiameseManager()


@app.post("/brandkit")
async def create_brandkit(
    id: str = Form(...),
    title: str = Form(...),
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Create brand kit and store classified assets."""
    assets_for_learning = []

    # Create a directory for this brand kit
    kit_dir = UPLOAD_DIR / id
    kit_dir.mkdir(parents=True, exist_ok=True)

    print("Phase 1: Learning from Assets...")
    extracted_rules = None

    # 1. Create the BrandKit Parent
    brand_kit = BrandKit(
        id=id,
        brand_name=title,  # Placeholder
        title=title,
        created_at=datetime.now(timezone.utc),
        colors=[],  # Init empty
        typography=[],  # Renamed from fonts
        assets=[],
        projects=[],
    )
    session.add(brand_kit)

    # 2. Process Files & Create Asset Records
    for f in files:
        if not f.filename:
            continue
        # Save file to disk
        file_path = kit_dir / f.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(f.file, buffer)

        # Check for Guidelines PDF
        if f.filename.lower().endswith(".pdf"):
            print(f"Detected potential Brand Guidelines: {f.filename}")
            try:
                extracted_rules = guideline_extractor.extract_guidelines(str(file_path))
            except Exception as e:
                print(f"Failed to extract guidelines from PDF: {e}")
            category = "GUIDELINES"
            confidence = 1.0

        # Check for Font Files
        elif f.filename.lower().endswith((".ttf", ".otf")):
            print(f"Detected Font File: {f.filename}")
            try:
                ingest_res = siamese_manager.ingest_new_font(str(file_path), f.filename)
                if ingest_res["success"]:
                    siamese_manager.save_embeddings(
                        id, f.filename, ingest_res["embeddings"]
                    )
                else:
                    print(f"Font ingestion failed: {ingest_res.get('error')}")
            except Exception as e:
                print(f"Failed to ingest font: {e}")
            category = "FONT"
            confidence = 1.0

        else:
            category, confidence = classifier.predict_type(str(file_path))

        # Create ASSET record
        asset = Asset(
            brand_kit_id=id,
            category=category,
            filename=f.filename,
            path=str(file_path),
            url=f"/uploads/{id}/{f.filename}",
        )
        session.add(asset)

        # Add to learning list
        try:
            if category in ["LOGO", "IMAGERY", "TEMPLATE"]:
                img = Image.open(file_path).convert("RGB")
                assets_for_learning.append({"image": img, "type": category})
        except Exception as e:
            print(f"Skipping {f.filename}: {e}")

    # 3. Generate Guidelines (Rules)
    generator = BrandGuidelineGenerator()
    brand_kit_dict = generator.generate_brand_kit(
        assets_for_learning, extracted_rules=extracted_rules
    )

    # Update BrandKit Metadata
    brand_kit.brand_name = brand_kit_dict.get("brand_name", "Unknown")
    brand_kit.color_tolerance = brand_kit_dict.get("color_tolerance", 50)
    brand_kit.brand_voice = brand_kit_dict.get("brand_voice", {})
    brand_kit.logo_rules = brand_kit_dict.get("logo", {})

    # 4. Create Color Records
    # pyrefly: ignore [not-iterable]
    for c in brand_kit_dict.get("colors", []):
        color = BrandColor(
            brand_kit_id=id,
            # pyrefly: ignore [missing-attribute]
            hex=c.get("hex", "#000000"),
            # pyrefly: ignore [missing-attribute]
            name=c.get("name", "Unknown"),
            # pyrefly: ignore [missing-attribute]
            rgb=c.get("rgb"),
            # pyrefly: ignore [missing-attribute]
            cmyk=c.get("cmyk"),
            # pyrefly: ignore [missing-attribute]
            usage=c.get("usage", "ACCENT"),
            # pyrefly: ignore [missing-attribute]
            text_color_rule=c.get("text_color_rule"),
        )
        session.add(color)

    # 5. Create Font Records
    # pyrefly: ignore [not-iterable]
    for t in brand_kit_dict.get("typography", []):
        font = BrandFont(
            brand_kit_id=id,
            # pyrefly: ignore [missing-attribute]
            family_name=t.get("family", "Unknown"),
            # pyrefly: ignore [missing-attribute]
            use_case=t.get("use_case", "BODY"),
        )
        session.add(font)

    await session.commit()

    query = (
        select(BrandKit)
        .where(BrandKit.id == id)
        .options(
            # pyrefly: ignore [bad-argument-type]
            selectinload(BrandKit.assets),
            # pyrefly: ignore [bad-argument-type]
            selectinload(BrandKit.colors),
            # pyrefly: ignore [bad-argument-type]
            selectinload(BrandKit.typography),
        )
    )
    result = await session.exec(query)
    brand_kit = result.first()

    # Return validated DTO
    return brand_kit


def _process_audit_job(
    pdf_bytes: bytes,
    bible_dict: dict,
    assets_for_auditor: list,
    brand_kit_id: str,
    allowed_fonts: list,
):
    """
    Blocking CPU-bound function to process PDF audit.
    MUST be run in a separate thread (run_in_executor).
    """
    try:
        pages = convert_from_bytes(pdf_bytes, dpi=150)
    except Exception as e:
        # Raise generic error to be caught by caller
        raise ValueError(f"Failed to process PDF: {str(e)}")

    auditor = IntegratedBrandAuditor(bible_dict, assets_for_auditor)
    typ_auditor = TypographyAuditor(siamese_manager)

    all_results = []

    for page_num, page_img in enumerate(pages, start=1):
        page_img = downsample_image(page_img)

        # Run audits
        results = auditor.audit_page(page_img)
        typ_results = typ_auditor.audit_page(page_img, brand_kit_id, allowed_fonts)
        results.extend(typ_results)

        page_w, page_h = page_img.size
        for r in results:
            x, y, w, h = r["bbox"]
            status = r["status"]

            # Determine level
            level = "PASS" if status == "PASS" else "MEDIUM"
            if "ratio" in r["metric"].lower() and "0.3" in r["metric"]:
                level = "CRITICAL"

            # Normalize coordinates
            norm_x = float(x) / float(page_w) if page_w else 0.0
            norm_y = float(y) / float(page_h) if page_h else 0.0
            norm_w = float(w) / float(page_w) if page_w else 0.0
            norm_h = float(h) / float(page_h) if page_h else 0.0

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

    return all_results, len(pages)


@app.post("/project/audit", response_model=ProjectRead)
async def audit_project(
    id: str = Form(...),
    title: str = Form(...),
    brand_kit_id: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
):
    """Audit a PDF against a brand kit's assets."""
    # EAGER LOAD everything to avoid N+1 and async generic errors
    query = (
        select(BrandKit)
        .where(BrandKit.id == brand_kit_id)
        .options(
            # pyrefly: ignore [bad-argument-type]
            selectinload(BrandKit.assets),
            # pyrefly: ignore [bad-argument-type]
            selectinload(BrandKit.colors),
            # pyrefly: ignore [bad-argument-type]
            selectinload(BrandKit.typography),  # Updated rel name
        )
    )
    result = await session.exec(query)
    brand_kit = result.first()

    if not brand_kit:
        raise HTTPException(
            status_code=404, detail=f"Brand kit '{brand_kit_id}' not found"
        )

    pdf_bytes = await file.read()

    # Prepare assets for auditor (Adapter to old dict format)
    assets_for_auditor = []
    for asset in brand_kit.assets:
        assets_for_auditor.append(
            {"image": asset.path, "type": asset.category, "filename": asset.filename}
        )

    # Prepare Bible Dict (Adapter)
    bible_dict = {
        "brand_name": brand_kit.brand_name,
        "colors": [c.model_dump() for c in brand_kit.colors],
        "typography": [f.model_dump() for f in brand_kit.typography],  # Updated rel
        "logo": brand_kit.logo_rules,
        "brandvoice": brand_kit.brand_voice,
    }

    # Extract allowed fonts dynamically from assets
    allowed_fonts = [a.filename for a in brand_kit.assets if a.category == "FONT"]

    try:
        loop = asyncio.get_running_loop()
        all_results, page_count = await loop.run_in_executor(
            None,
            _process_audit_job,
            pdf_bytes,
            bible_dict,
            assets_for_auditor,
            brand_kit_id,
            allowed_fonts,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Audit failed: {str(e)}")

    critical_count = sum(1 for v in all_results if v.level == "CRITICAL")
    medium_count = sum(1 for v in all_results if v.level == "MEDIUM")
    score = max(0, 100 - (critical_count * 20) - (medium_count * 10))

    if critical_count > 0:
        overall_status = "CRITICAL"
    elif medium_count > 0:
        overall_status = "ACTION_REQUIRED"
    else:
        overall_status = "COMPLIANT"

    # Save PDF
    project_dir = UPLOAD_DIR / "projects" / id
    project_dir.mkdir(parents=True, exist_ok=True)
    if not file.filename:
        file.filename = "unknown.pdf"
    pdf_path = project_dir / file.filename
    with open(pdf_path, "wb") as f:
        f.write(pdf_bytes)

    # Create ProjectFile
    project_file = ProjectFile(
        project_id=id,
        name=file.filename,
        url=f"/uploads/projects/{id}/{file.filename}",
        status="ready",
        violations=[v.model_dump() for v in all_results],
        page_count=page_count,
    )

    project = Project(
        id=id,
        title=title,
        created_at=datetime.now(timezone.utc),
        status=overall_status,
        score=score,
        brand_kit_id=brand_kit_id,
        files=[project_file],
    )

    session.add(project)
    await session.commit()
    await session.refresh(project)

    # Construct DTO explicitly to avoid manipulating attached DB object
    return ProjectRead(
        id=project.id,
        title=project.title,
        created_at=project.created_at,
        status=project.status,
        score=project.score,
        brand_kit_id=project.brand_kit_id,
        brand_kit=brand_kit,  # Explicitly pass loaded object
        # pyrefly: ignore [deprecated]
        files=[ProjectFileRead.from_orm(project_file)],  # Explicitly pass loaded object
    )


@app.get("/brandkits", response_model=List[BrandKitRead])
async def list_brandkits(session: AsyncSession = Depends(get_session)):
    """List all brand kits."""
    # Eager load assets, colors, and typography (was fonts)
    query = select(BrandKit).options(
        selectinload(BrandKit.assets),  # type: ignore
        selectinload(BrandKit.colors),  # type: ignore
        selectinload(BrandKit.typography),  # type: ignore
    )
    result = await session.exec(query)
    kits = result.all()

    # DTO automatically handles serialization of nested models
    return kits


@app.get("/projects", response_model=List[ProjectRead])
async def list_projects(
    expand: Optional[str] = Query(None),
    limit: Optional[int] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    """List all projects."""
    # Eager load nested data if expanded
    query = (
        select(Project)
        # pyrefly: ignore [missing-attribute]
        .order_by(Project.created_at.desc())
        .options(
            selectinload(Project.files),  # type: ignore
        )
    )

    if expand == "brandKit":
        # Eager load BrandKit and its children
        query = query.options(
            selectinload(Project.brand_kit).options(  # type: ignore
                selectinload(BrandKit.assets),  # type: ignore
                selectinload(BrandKit.colors),  # type: ignore
                selectinload(BrandKit.typography),  # type: ignore
            )
        )

    result = await session.exec(query)
    projects = list(result.all())

    if limit:
        projects = projects[:limit]

    return projects


@app.post("/brandkit/{id}/font")
async def upload_font(
    id: str, file: UploadFile = File(...), session: AsyncSession = Depends(get_session)
):
    """Upload a TTF/OTF font file to the brand kit."""
    brand_kit = await session.get(BrandKit, id)
    if not brand_kit:
        raise HTTPException(status_code=404, detail="Brand kit not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    # save file
    kit_dir = UPLOAD_DIR / id
    kit_dir.mkdir(parents=True, exist_ok=True)
    font_path = kit_dir / file.filename

    with open(font_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Ingest
    result = siamese_manager.ingest_new_font(str(font_path), file.filename)

    if not result["success"]:
        try:
            os.remove(font_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to process font")
        )

    # Save Embeddings
    siamese_manager.save_embeddings(id, file.filename, result["embeddings"])

    # Create Asset Record
    new_asset = Asset(
        brand_kit_id=id,
        category="FONT",
        filename=file.filename,
        path=str(font_path),
        url=f"/uploads/{id}/{file.filename}",
    )

    session.add(new_asset)
    await session.commit()

    return {
        "status": "success",
        "file": file.filename,
        "stats": {k: v for k, v in result.items() if k != "embeddings"},
    }
