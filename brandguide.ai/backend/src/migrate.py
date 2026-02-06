import asyncio
import json
from pathlib import Path

from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from database import engine, init_db
from models import BrandKit, Project

# Path to legacy store
DATA_DIR = Path(__file__).parent.parent / "data"
STORE_FILE = DATA_DIR / "store.json"


async def migrate_data():
    print("🚀 Starting Data Migration...")

    # 1. Initialize Tables
    await init_db()
    print("✅ Database tables created.")

    # 2. Read JSON
    if not STORE_FILE.exists():
        print(f"⚠️ No store.json found at {STORE_FILE}. Skipping data import.")
        return

    try:
        with open(STORE_FILE, "r") as f:
            data = json.load(f)
            brand_kits_dict = data.get("brand_kits", {})
            projects_dict = data.get("projects", {})

        print(
            f"📦 Found {len(brand_kits_dict)} brand kits "
            f"and {len(projects_dict)} projects in JSON."
        )

        # pyrefly: ignore [no-matching-overload]
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )  # type: ignore

        async with async_session() as session:
            # Import Brand Kits
            for bk_id, bk_data in brand_kits_dict.items():
                existing = await session.get(BrandKit, bk_id)
                if not existing:
                    bk = BrandKit(
                        id=bk_id,
                        brand_name=bk_data.get("brand_name", ""),
                        title=bk_data.get("title"),
                        primary_colors=bk_data.get("primary_colors", []),
                        allowed_logo_ratios=bk_data.get("allowed_logo_ratios", []),
                        brand_voice_attributes=bk_data.get(
                            "brand_voice_attributes", []
                        ),
                        forbidden_keywords=bk_data.get("forbidden_keywords", []),
                        frequent_keywords=bk_data.get("frequent_keywords", []),
                        color_tolerance=bk_data.get("color_tolerance", 50),
                        assets=bk_data.get("assets", []),
                    )
                    session.add(bk)

            # Import Projects
            for proj_id, proj_data in projects_dict.items():
                existing = await session.get(Project, proj_id)
                if not existing:
                    proj = Project(
                        id=proj_id,
                        title=proj_data.get("title", "Untitled"),
                        date=proj_data.get("date", ""),
                        status=proj_data.get("status", "UNKNOWN"),
                        score=proj_data.get("score", 0),
                        brandKitId=proj_data.get("brandKitId"),
                        files=proj_data.get("files", []),
                    )
                    session.add(proj)

            await session.commit()
            print("✅ Data successfully migrated to PostgreSQL.")

    except Exception as e:
        print(f"❌ Migration failed: {e}")


if __name__ == "__main__":
    asyncio.run(migrate_data())
