"""Demand Profile Model"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict

class DemandProfile(BaseModel):
    """Model for demand profile"""
    profile_id: str = Field(..., description="Unique identifier for demand profile")
    current_demand: float = Field(default=0, ge=0, description="Current demand in kW")
    peak_demand: float = Field(default=0, ge=0, description="Peak demand in kW")
    minimum_demand: float = Field(default=0, ge=0, description="Minimum demand in kW")
    average_demand: float = Field(default=0, ge=0, description="Average demand in kW")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    hourly_distribution: Dict[int, float] = Field(default_factory=dict, description="Hourly demand distribution")
    sector_breakdown: Dict[str, float] = Field(default_factory=dict, description="Demand by sector")
    elasticity_index: float = Field(default=0.5, ge=0, le=1, description="Demand elasticity index")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_id": "DEMAND_01",
                "current_demand": 1500.0,
                "peak_demand": 2000.0,
                "minimum_demand": 800.0,
                "average_demand": 1400.0,
                "timestamp": "2026-03-27T10:30:00",
                "hourly_distribution": {
                    "0": 900.0,
                    "1": 850.0,
                    "12": 1800.0,
                    "18": 2000.0
                },
                "sector_breakdown": {
                    "residential": 700.0,
                    "commercial": 550.0,
                    "industrial": 250.0
                },
                "elasticity_index": 0.6
            }
        }
