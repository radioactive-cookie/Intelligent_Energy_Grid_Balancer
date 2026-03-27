"""Energy Source Model"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

class EnergySource(BaseModel):
    """Model for energy generation sources"""
    source_id: str = Field(..., description="Unique identifier for energy source")
    type: Literal["solar", "wind"] = Field(..., description="Type of energy source")
    generation_value: float = Field(..., ge=0, description="Current generation in kW")
    capacity: float = Field(..., ge=0, description="Maximum capacity in kW")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location: str = Field(..., description="Location of energy source")
    efficiency: float = Field(default=0.95, ge=0, le=1, description="Efficiency percentage")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_id": "SOLAR_01",
                "type": "solar",
                "generation_value": 250.5,
                "capacity": 500.0,
                "timestamp": "2026-03-27T10:30:00",
                "location": "North Farm",
                "efficiency": 0.95
            }
        }
