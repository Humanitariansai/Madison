from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from pydantic import root_validator, validator
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, Relationship, SQLModel

# Use JSONB for Postgres, JSON for generic fallback
JSON_TYPE = JSONB


# --- 1. ASSETS (Files) ---
class Asset(SQLModel, table=True):
    """
    Represents a physical file on disk/S3 (Logo, Font, Image).
    """

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    brand_kit_id: str = Field(foreign_key="brandkit.id", index=True)

    category: str  # "FONT", "LOGO", "IMAGERY"
    filename: str
    path: str  # Internal path: "uploads/xyz/font.ttf"
    url: str  # External path: "/uploads/xyz/font.ttf"

    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Metadata for specific types (e.g. image dims, file size)
    metadata_json: dict = Field(default={}, sa_column=Column(JSON_TYPE))

    # Relationships
    brand_kit: "BrandKit" = Relationship(back_populates="assets")


# --- 2. COLORS ---
class BrandColor(SQLModel, table=True):
    """
    A specific color definition in the Brand Kit.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    brand_kit_id: str = Field(foreign_key="brandkit.id", index=True)

    name: str = "Primary"
    hex: str  # "#FF0000" (Indexed for search)
    rgb: Optional[str] = None
    cmyk: Optional[str] = None

    usage: str = "PRIMARY"  # PRIMARY, SECONDARY, ACCENT
    text_color_rule: Optional[str] = None  # "Use White Text"

    brand_kit: "BrandKit" = Relationship(back_populates="colors")

    # pyrefly: ignore [deprecated]
    @validator("hex", pre=True)
    def validate_hex(cls, v):
        if v and not v.startswith("#"):
            return f"#{v}"
        return v


# --- 3. TYPOGRAPHY (Fonts) ---
class BrandFont(SQLModel, table=True):
    """
    A Typography Rule ("We use Helvetica for Headlines").
    Linked to an Asset file if available.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    brand_kit_id: str = Field(foreign_key="brandkit.id", index=True)

    family_name: str  # "Open Sans"
    use_case: str = "BODY"  # BODY, HEADING, CAPTION

    # Link to the actual physical file (e.g. OpenSans-Bold.ttf)
    primary_asset_id: Optional[str] = Field(default=None, foreign_key="asset.id")

    brand_kit: "BrandKit" = Relationship(back_populates="typography")
    # We could relationally link asset here too if needed


# --- 4. PROJECT FILES ---
class ProjectFile(SQLModel, table=True):
    """
    A specific PDF file being audited within a Project.
    """

    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    project_id: str = Field(foreign_key="project.id", index=True)

    name: str
    url: str
    page_count: int = 0
    status: str = "pending"  # pending, processing, complete, failed

    # Keeping violations as JSONB is acceptable for variable report data
    violations: List[dict] = Field(default=[], sa_column=Column(JSON_TYPE))

    upload_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    project: "Project" = Relationship(back_populates="files")


# --- MAIN ENTITIES ---


class BrandKit(SQLModel, table=True):
    __tablename__ = "brandkit"  # type: ignore

    id: str = Field(primary_key=True)
    brand_name: str
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Settings
    color_tolerance: int = Field(default=50)

    # Brand Voice & Logo Rules (Structure is variable, so JSONB is fine here)
    brand_voice: dict = Field(default={}, sa_column=Column(JSON_TYPE))
    logo_rules: dict = Field(default={}, sa_column=Column(JSON_TYPE))

    # Relationships
    # Relationships
    colors: List[BrandColor] = Relationship(back_populates="brand_kit")
    typography: List[BrandFont] = Relationship(back_populates="brand_kit")
    assets: List[Asset] = Relationship(back_populates="brand_kit")

    projects: List["Project"] = Relationship(back_populates="brand_kit")


class Project(SQLModel, table=True):
    id: str = Field(primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    brand_kit_id: str = Field(foreign_key="brandkit.id")

    # Audit Results
    status: str  # 'COMPLIANT', 'CRITICAL', 'ACTION_REQUIRED'
    score: int

    # Relationships
    brand_kit: BrandKit = Relationship(back_populates="projects")
    files: List[ProjectFile] = Relationship(back_populates="project")


# --- RESPONSE SCHEMAS (DTOs) ---


class AssetRead(SQLModel):
    id: str
    category: str
    filename: str
    path: str
    url: str
    upload_date: datetime
    metadata_json: dict = {}


# ... (BrandFontRead logic) ...


class BrandColorRead(SQLModel):
    id: str
    name: str
    hex: str
    rgb: Optional[str] = None
    cmyk: Optional[str] = None
    usage: str
    text_color_rule: Optional[str] = None

    # pyrefly: ignore [deprecated]
    @validator("hex", pre=True)
    def validate_hex(cls, v):
        if v and not v.startswith("#"):
            return f"#{v}"
        return v


class BrandFontRead(SQLModel):
    id: str
    family: str
    weights: List[str] = []
    use_case: str
    primary_asset_id: Optional[str] = None

    # pyrefly: ignore [deprecated]
    @root_validator(pre=True)
    def map_family_name(cls, values):
        # Handle ORM object or dict
        if hasattr(values, "family_name"):
            values = values.__dict__
        if "family_name" in values:
            values["family"] = values["family_name"]
        return values


class BrandKitRead(SQLModel):
    id: str
    brand_name: str
    title: str
    created_at: datetime
    color_tolerance: int
    brand_voice: dict
    logo_rules: dict

    # Nested Models
    colors: List[BrandColorRead] = []
    typography: List[BrandFontRead] = []
    assets: List[AssetRead] = []


class ProjectFileRead(SQLModel):
    id: str
    name: str
    url: str
    status: str
    violations: List[dict] = []
    upload_date: datetime


class ProjectRead(SQLModel):
    id: str
    title: str
    created_at: datetime
    status: str
    score: int
    brand_kit_id: str

    # Nested
    files: List[ProjectFileRead] = []
    brand_kit: Optional[BrandKitRead] = None
