from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
class ProjectType(str, Enum):
    KITCHEN_REMODEL = "kitchen_remodel"
    BATHROOM_REMODEL = "bathroom_remodel"
    ROOM_ADDITION = "room_addition"
    WHOLE_HOUSE_REMODEL = "whole_house_remodel"
    ADU = "accessory_dwelling_unit"
    LANDSCAPING = "landscaping"
    POOL_INSTALLATION = "pool_installation"
    GARAGE_CONVERSION = "garage_conversion"
    ROOFING = "roofing"
    FLOORING = "flooring"
class ChatRequest(BaseModel):
    content: str
    role: str = "user"
    session_id: Optional[str] = None
class ChatResponse(BaseModel):
    message: str
    type: str = "text"
    metadata: Optional[Dict[str, Any]] = None
    session_id: str
class ProjectDetails(BaseModel):
    project_type: ProjectType
    property_type: str = Field(..., pattern="^(single_family|condo|townhouse|multi_family)$")
    address: Optional[str] = None
    city: str
    state: str
    square_footage: float = Field(gt=0, le=10000)
    additional_details: Optional[str] = None
    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        if v.upper() != "CA":
            raise ValueError('Currently only serving California')
        return v.upper()
    @field_validator('city')
    @classmethod
    def validate_city(cls, v):
        allowed_cities = ["San Diego", "Los Angeles", "LA", "SD"]
        city_upper = v.upper()
        if city_upper == "LA":
            return "Los Angeles"
        elif city_upper == "SD":
            return "San Diego"
        elif v.title() in allowed_cities:
            return v.title()
        else:
            raise ValueError(f"We currently only serve San Diego and Los Angeles")
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
class ExportRequest(BaseModel):
    estimate_id: str
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")
    include_breakdown: bool = True
    include_similar_projects: bool = True
class ExportResponse(BaseModel):
    file_url: str
    download_name: str
    expires_at: datetime