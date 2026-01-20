from pydantic import BaseModel
from typing import List, Optional

class Product(BaseModel):
    name: str
    category: str
    description: Optional[str] = None

class Competitor(BaseModel):
    name: str
    strengths: List[str]
    weaknesses: List[str]
    pricing_strategy: Optional[str] = None
    target_market: Optional[str] = None

class CustomerPersona(BaseModel):
    name: str
    demographics: str
    motivations: str
    pain_points: str
    preferred_channels: List[str]
