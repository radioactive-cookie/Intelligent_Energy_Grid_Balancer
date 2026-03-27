"""Grid State Model"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class GridState(BaseModel):
    """Model for current grid state"""
    grid_id: str = Field(..., description="Unique identifier for grid")
    frequency: float = Field(default=50.0, description="Grid frequency in Hz")
    total_demand: float = Field(default=0, ge=0, description="Total demand in kW")
    total_generation: float = Field(default=0, ge=0, description="Total generation in kW")
    load_percentage: float = Field(default=0, ge=0, le=100, description="Current load percentage")
    renewable_percentage: float = Field(default=0, ge=0, le=100, description="Renewable energy percentage")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    grid_stability_score: float = Field(default=100, ge=0, le=100, description="Grid stability score 0-100")
    is_stable: bool = Field(default=True, description="Whether grid is stable")
    imbalance: float = Field(default=0, description="Generation - Demand imbalance in kW")
    
    class Config:
        json_schema_extra = {
            "example": {
                "grid_id": "MAIN_GRID_01",
                "frequency": 50.0,
                "total_demand": 1500.0,
                "total_generation": 1550.0,
                "load_percentage": 75.0,
                "renewable_percentage": 65.5,
                "timestamp": "2026-03-27T10:30:00",
                "grid_stability_score": 95.0,
                "is_stable": True,
                "imbalance": 50.0
            }
        }
