from __future__ import annotations

from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator

# NEW ────────────────────────────────────────────────────────────────────
from services.city_mappings import normalize_location
# ────────────────────────────────────────────────────────────────────────


# ── Enums ───────────────────────────────────────────────────────────────
class ProjectType(str, Enum):
    KITCHEN_REMODEL        = "kitchen_remodel"
    BATHROOM_REMODEL       = "bathroom_remodel"
    ROOM_ADDITION          = "room_addition"
    WHOLE_HOUSE_REMODEL    = "whole_house_remodel"
    ADU                    = "accessory_dwelling_unit"
    LANDSCAPING            = "landscaping"
    POOL_INSTALLATION      = "pool_installation"
    GARAGE_CONVERSION      = "garage_conversion"
    ROOFING                = "roofing"
    FLOORING               = "flooring"


# ── Chat schema ─────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    content: str
    role: str = "user"
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    type: str = "text"
    metadata: Optional[Dict[str, Any]] = None
    session_id: str


# ── Project details / validation ────────────────────────────────────────
class ProjectDetails(BaseModel):
    project_type: ProjectType
    property_type: str = Field(
        ...,
        pattern="^(single_family|condo|townhouse|multi_family)$"
    )

    address: Optional[str] = None
    city: str
    state: str
    square_footage: float = Field(gt=0, le=10_000)
    additional_details: Optional[str] = None

    # ── State must be CA -------------------------------------------------
    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        if v.upper() != "CA":
            raise ValueError("Currently we serve California only")
        return v.upper()

    # ── City normalisation / acceptance ---------------------------------
    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        """
        Accept “San Diego”, “Los Angeles”, their abbreviations “SD” / “LA”,
        **or** any alias present in CITY_MAPPINGS (e.g. “Chula Vista”,
        “West Hills”, “LA County”, etc.).  Always return the canonical
        “San Diego” or “Los Angeles”.
        """
        if not v:
            raise ValueError("City is required")

        # 1) Try the shared helper (covers all aliases)
        mapped = normalize_location(v)
        if mapped:
            return mapped

        # 2) Fallback to legacy exact-match support
        v_upper = v.strip().upper()
        if v_upper in {"SAN DIEGO", "SD"}:
            return "San Diego"
        if v_upper in {"LOS ANGELES", "LA"}:
            return "Los Angeles"

        # 3) Still unknown → reject
        raise ValueError("We currently support projects only in San Diego or Los Angeles.")


# ── Estimate request / response ─────────────────────────────────────────
class EstimateRequest(BaseModel):
    project_details: ProjectDetails
    session_id: Optional[str] = None


class CostBreakdown(BaseModel):
    materials: float
    labor: float
    permits: float
    other: float
    total: float


class TimelineBreakdown(BaseModel):
    planning_days: int
    permit_days: int
    construction_days: int
    total_days: int


class SimilarProject(BaseModel):
    project_type: str
    location: str
    cost_range: str
    timeline: str
    source: str


class EstimateResponse(BaseModel):
    estimate_id: str
    total_cost: float
    cost_range_low: float
    cost_range_high: float
    cost_breakdown: CostBreakdown
    confidence_score: float
    timeline: TimelineBreakdown
    similar_projects: List[SimilarProject]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


# ── Export ------------------------------------------------------------------
class ExportRequest(BaseModel):
    estimate_id: str
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")
    include_breakdown: bool = True
    include_similar_projects: bool = True


class ExportResponse(BaseModel):
    file_url: str
    download_name: str
    expires_at: datetime
