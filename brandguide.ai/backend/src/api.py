import asyncio
import logging
import os
import shutil
import traceback
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import numpy as np  # Added for chunk processing
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pdf2image import convert_from_path
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
from .layout_classifier import LayoutClassifierFactory
from .logging_conf import configure_logging
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
from .services.ml_service import MLService

# from .typography.auditor import TypographyAuditor
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


# Configure Logging centrally
configure_logging()
logger = logging.getLogger(__name__)


# Lifespan event to init DB
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure DB tables exist
    await init_db()

    # Eager Load ML Models (Thread-Safe Singleton)
    # This ensures they are ready before any request hits
    # and prevents race conditions.
    logger.info("Lifespan: Triggering Eager Load of ML Services...")
    _ = MLService()
    _ = SiameseManager()
    logger.info("Lifespan: ML Services Ready.")

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

# Semaphore to prevent OOM
# Limit to 1 concurrent audits because Layout Analysis + ML is memory heavy
AUDIT_SEMAPHORE = asyncio.Semaphore(1)


@app.post("/brandkit", response_model=BrandKitRead)
async def create_brandkit(
    id: str = Form(...),
    title: str = Form(...),
    files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_session),
    siamese_manager: SiameseManager = Depends(SiameseManager),
    generator: BrandGuidelineGenerator = Depends(BrandGuidelineGenerator),
    classifier: AssetClassifier = Depends(AssetClassifier),
    extractor: BrandGuidelineExtractor = Depends(BrandGuidelineExtractor),
):
    """Create brand kit and store classified assets."""
    logger.info(f"Creating BrandKit: {title} (ID: {id})")
    assets_for_learning = []

    # Create a directory for this brand kit
    kit_dir = UPLOAD_DIR / id
    await run_in_threadpool(kit_dir.mkdir, parents=True, exist_ok=True)

    logger.debug("Phase 1: Learning from Assets...")
    extracted_rules = None

    # 1. Create the BrandKit Parent
    brand_kit = BrandKit(
        id=id,
        brand_name=title,  # Placeholder
        title=title,
        created_at=datetime.utcnow(),
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

        file_path = kit_dir / f.filename
        content = await f.read()

        def save_file():
            with open(file_path, "wb") as buffer:
                buffer.write(content)

        await run_in_threadpool(save_file)

        # Check for Guidelines PDF
        if f.filename.lower().endswith(".pdf"):
            logger.debug(f"Detected potential Brand Guidelines: {f.filename}")
            try:
                extracted_rules = await run_in_threadpool(
                    extractor.extract_guidelines, str(file_path)
                )
                logger.debug(f"Extracted rules: {extracted_rules}")
            except Exception as e:
                logger.warning(f"Failed to extract guidelines from PDF: {e}")
            category = "GUIDELINES"
            confidence = 1.0

        # Check for Font Files
        elif f.filename.lower().endswith((".ttf", ".otf")):
            print(f"Detected Font File: {f.filename}")
            try:
                ingest_res = await run_in_threadpool(
                    siamese_manager.ingest_new_font, str(file_path), f.filename
                )
                if ingest_res["success"]:
                    await run_in_threadpool(
                        siamese_manager.save_embeddings,
                        id,
                        f.filename,
                        ingest_res["embeddings"],
                    )
                else:
                    print(f"Font ingestion failed: {ingest_res.get('error')}")
            except Exception as e:
                print(f"Failed to ingest font: {e}")
            category = "FONT"
            confidence = 1.0

        else:
            category, confidence = await run_in_threadpool(
                classifier.predict_type, str(file_path)
            )

        # Create ASSET record
        asset = Asset(
            brand_kit_id=id,
            category=category,
            filename=f.filename,
            path=str(file_path),
            url=f"/uploads/{id}/{f.filename}",
        )
        session.add(asset)
        brand_kit.assets.append(asset)
        # Add to learning list
        try:
            if category in ["LOGO", "IMAGERY", "TEMPLATE"]:

                def load_image():
                    return Image.open(file_path).convert("RGB")

                img = await run_in_threadpool(load_image)
                assets_for_learning.append({"image": img, "type": category})
        except Exception as e:
            logger.warning(f"Skipping {f.filename} for learning: {e}")

    # 3. Generate Guidelines (Rules)
    # generator is now injected via DI
    brand_kit_dict = await run_in_threadpool(
        generator.generate_brand_kit,
        assets_for_learning,
        extracted_rules=extracted_rules,
    )
    logger.info(
        "Brand Guidelines Generated. "
        f"Found {len(brand_kit_dict.get('colors', []))} colors."
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
        # Also append to relationship to ensure consistency
        brand_kit.colors.append(color)

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
        # Also append to relationship to ensure consistency
        brand_kit.typography.append(font)

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
    logger.info(f"BrandKit Created Successfully: {id}")
    logger.debug(
        f"Returning BrandKit DTO inspection: Colors={len(brand_kit.colors)}, "
        f"Fonts={len(brand_kit.typography)}"
    )
    return brand_kit


def _process_audit_job(
    pdf_input: str,
    bible_dict: dict,
    assets_for_auditor: list,
    brand_kit_id: str,
    allowed_fonts: list,
    ml_service: MLService,
    use_layout_engine: bool = False,
):
    """
    Blocking CPU-bound function to process PDF audit.
    MUST be run in a separate thread (run_in_executor).
    """
    # Initialize Auditor
    auditor = IntegratedBrandAuditor(bible_dict, assets_for_auditor, ml_service)
    # typ_auditor = TypographyAuditor(siamese_manager)

    logger.info(
        f"Audit Job Started for BrandKit: {brand_kit_id}. "
        f"Use Layout Engine: {use_layout_engine}"
    )

    pages = []
    layout_classifier = None

    if use_layout_engine and isinstance(pdf_input, str):
        # V2: pdf_input is actually a path string
        pdf_path = pdf_input
        try:
            pages = convert_from_path(pdf_path, dpi=150)
            layout_classifier = LayoutClassifierFactory.get_classifier("pymupdf")
        except Exception as e:
            raise ValueError(f"Failed to process PDF V2: {str(e)}")
    else:
        raise ValueError("Invalid PDF input")

    logger.debug(f"PDf Processed. Page Count: {len(pages)}")
    all_results = []

    # Batch Processing: Chunk pages to avoid OOM
    # 10 pages per chunk is safe for ~50 images/chunk
    BATCH_SIZE = 10

    # ---------------------------------------------------------
    # BATCH LOOP
    # ---------------------------------------------------------
    for i in range(0, len(pages), BATCH_SIZE):
        chunk_pages = pages[i : i + BATCH_SIZE]
        chunk_results_map = []  # List of [InspectionResult]

        if use_layout_engine and layout_classifier:
            # V2 BATCH
            chunk_layouts = []
            chunk_cvs = []

            for j, p in enumerate(chunk_pages):
                # Downsample first? V2 uses full res usually, but let's be consistent
                # Actually V2 Layout Classifier needs alignment with PDF coords.
                # If we downsample image, we must scale bbox.
                # Let's keep V2 full res for analysis, simple.
                layout = layout_classifier.analyze_page(i + j, pdf_path=pdf_input)
                chunk_layouts.append(layout)
                chunk_cvs.append(np.array(p))

            # Calls new Batch Auditor
            raw_batch_results = auditor.audit_batch(
                chunk_pages, chunk_layouts, chunk_cvs
            )
            chunk_results_map = raw_batch_results

        else:
            # V1 LEGACY (Iterative)
            for page_img in chunk_pages:
                page_img = downsample_image(page_img)
                res = auditor.audit_page(page_img)
                chunk_results_map.append(res)

        # Process Results into API Schema
        for j, results in enumerate(chunk_results_map):
            page_obj = chunk_pages[j]
            page_num = i + j + 1
            page_w, page_h = page_obj.size

            for r in results:
                x, y, w, h = r["bbox"]
                status = r["status"]

                # Determine level
                level = r.get("level", "MEDIUM")  # Default
                # Legacy rule override
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
async def audit_project_v2(
    id: str = Form(...),
    title: str = Form(...),
    brand_kit_id: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    ml_service: MLService = Depends(MLService),
):
    """V2: Structure-Aware Audit using Layout Engine (PyMuPDF)."""
    try:
        async with AUDIT_SEMAPHORE:
            logger.info(f"Received V2 Audit Request: {title} (ID: {id})")
            # 1. Load Brand Kit
            query = (
                select(BrandKit)
                .where(BrandKit.id == brand_kit_id)
                .options(
                    selectinload(BrandKit.assets),  # type: ignore
                    selectinload(BrandKit.colors),  # type: ignore
                    selectinload(BrandKit.typography),  # type: ignore
                )
            )
            result = await session.exec(query)
            brand_kit = result.first()

            if not brand_kit:
                raise HTTPException(
                    status_code=404, detail=f"Brand kit '{brand_kit_id}' not found"
                )

            # 2. Save File FIRST (Required for Ref-Based Layout Analysis)
            project_dir = UPLOAD_DIR / "projects" / id
            await run_in_threadpool(project_dir.mkdir, parents=True, exist_ok=True)
            if not file.filename:
                file.filename = "unknown.pdf"

            # Sanitize filename (strip directory components)
            file.filename = Path(file.filename).name

            pdf_path = project_dir / file.filename

            # Write stream to disk
            def save_file():
                with open(pdf_path, "wb") as f:
                    shutil.copyfileobj(file.file, f)

            await run_in_threadpool(save_file)

            logger.debug(f"Saved PDF to disk: {pdf_path}")

            # 3. Prepare Auditor Config
            assets_for_auditor = []
            for asset in brand_kit.assets:
                assets_for_auditor.append(
                    {
                        "image": asset.path,
                        "type": asset.category,
                        "filename": asset.filename,
                    }
                )

            bible_dict = {
                "brand_name": brand_kit.brand_name,
                "colors": [c.model_dump() for c in brand_kit.colors],
                "typography": [f.model_dump() for f in brand_kit.typography],
                "logo": brand_kit.logo_rules,
                "brandvoice": brand_kit.brand_voice,
                "brand_voice_attributes": brand_kit.brand_voice.get("attributes", [])
                if brand_kit.brand_voice
                else [],
            }

            allowed_fonts = [
                a.filename for a in brand_kit.assets if a.category == "FONT"
            ]

            # 4. Run Blocking Audit (With Path + Layout Flag)
            try:
                all_results, page_count = await run_in_threadpool(
                    _process_audit_job,
                    str(pdf_path),
                    bible_dict,
                    assets_for_auditor,
                    brand_kit_id,
                    allowed_fonts,
                    ml_service,
                    True,  # Use Layout Engine
                )
                logger.info(
                    f"Audit V2 Completed. {len(all_results)} "
                    f"findings across {page_count} pages."
                )
            except Exception as e:
                logger.error(f"Audit V2 Job Failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=400, detail=f"Audit V2 failed: {str(e)}"
                )

            # 5. Save Project Record
            critical_count = sum(1 for v in all_results if v.level == "CRITICAL")
            medium_count = sum(
                1 for v in all_results if v.level == "MEDIUM" or v.level == "WARNING"
            )
            score = max(0, 100 - (critical_count * 20) - (medium_count * 10))

            if critical_count > 0:
                overall_status = "CRITICAL"
            elif medium_count > 0:
                overall_status = "ACTION_REQUIRED"
            else:
                overall_status = "COMPLIANT"

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
                created_at=datetime.utcnow(),
                status=overall_status,
                score=score,
                brand_kit_id=brand_kit_id,
                files=[project_file],
            )

            session.add(project)
            await session.commit()
            await session.refresh(project)

            return ProjectRead(
                id=project.id,
                title=project.title,
                created_at=project.created_at,
                status=project.status,
                score=project.score,
                brand_kit_id=project.brand_kit_id,
                brand_kit=brand_kit,
                files=[ProjectFileRead.from_orm(project_file)],
            )
    except Exception as e:
        logger.error(f"CRITICAL ERROR in audit_project_v2: {e}", exc_info=True)
        tb_str = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {tb_str}")


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
    id: str,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    siamese_manager: SiameseManager = Depends(SiameseManager),
):
    """Upload a TTF/OTF font file to the brand kit."""
    brand_kit = await session.get(BrandKit, id)
    if not brand_kit:
        raise HTTPException(status_code=404, detail="Brand kit not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    # save file
    kit_dir = UPLOAD_DIR / id
    await run_in_threadpool(kit_dir.mkdir, parents=True, exist_ok=True)
    font_path = kit_dir / file.filename

    def save_font():
        with open(font_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    await run_in_threadpool(save_font)

    # Ingest
    result = await run_in_threadpool(
        siamese_manager.ingest_new_font, str(font_path), file.filename
    )

    if not result["success"]:
        try:
            os.remove(font_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=400, detail=result.get("error", "Failed to process font")
        )

    # Save Embeddings
    await run_in_threadpool(
        siamese_manager.save_embeddings, id, file.filename, result["embeddings"]
    )

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


@app.post("/brandkit/{brand_kit_id}/fonts/upload")
async def upload_font_file_to_existing_kit(
    brand_kit_id: str,
    font_family: str = Form(...),
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    siamese_manager: SiameseManager = Depends(SiameseManager),
):
    """Upload and process a font file for an existing brand kit."""

    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    # 1. Validate brand kit exists and load typography relationship
    stmt = (
        select(BrandKit)
        .where(BrandKit.id == brand_kit_id)
        .options(selectinload(BrandKit.typography))
    )
    result = await session.execute(stmt)
    brand_kit = result.scalar_one_or_none()

    if not brand_kit:
        raise HTTPException(status_code=404, detail="Brand kit not found")

    # 2. Validate file type
    if not file.filename or not file.filename.lower().endswith((".ttf", ".otf")):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .ttf and .otf files are supported",
        )

    # 3. Save file to uploads directory
    kit_dir = UPLOAD_DIR / brand_kit_id
    await run_in_threadpool(kit_dir.mkdir, parents=True, exist_ok=True)
    font_path = kit_dir / file.filename

    def save_font():
        with open(font_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    await run_in_threadpool(save_font)

    # 4. Process font with SiameseManager
    try:
        ingest_res = await run_in_threadpool(
            siamese_manager.ingest_new_font, str(font_path), file.filename
        )

        if not ingest_res["success"]:
            # Clean up file on failure
            try:
                os.remove(font_path)
            except Exception:
                pass
            raise HTTPException(
                status_code=500,
                detail=f"Font processing failed: {ingest_res.get('error')}",
            )

        # 5. Save embeddings
        await run_in_threadpool(
            siamese_manager.save_embeddings,
            brand_kit_id,
            file.filename,
            ingest_res["embeddings"],
        )

        # 6. Update database: Mark font as uploaded
        # Find the BrandFont entry matching font_family
        font_entry = None
        for font in brand_kit.typography:
            if font.family_name == font_family:
                font_entry = font
                break

        if font_entry:
            font_entry.is_uploaded = True
            font_entry.filename = file.filename
            session.add(font_entry)
            await session.commit()
            # await session.refresh(brand_kit)

        return {
            "success": True,
            "font_family": font_family,
            "filename": file.filename,
            "char_count": ingest_res["char_count"],
            "message": "Font uploaded and processed successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Font upload failed: {e}")
        # Clean up file on error
        try:
            os.remove(font_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))
