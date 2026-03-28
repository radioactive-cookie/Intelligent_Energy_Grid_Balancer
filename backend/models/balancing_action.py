"""Balancing Action Model"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Dict, Any

class BalancingAction(BaseModel):
    """Model for balancing actions"""
    action_id: str = Field(..., description="Unique identifier for action")
    action: Literal["store", "release", "shed_load", "demand_response", "ramp_up", "ramp_down", "none"] = Field(..., description="Action to take")
    reasoning: str = Field(..., description="Explanation for the action")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    magnitude: float = Field(default=0, description="Magnitude of action in MW")
    target_frequency: float = Field(default=50.0, description="Target grid frequency in Hz")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level 1-10")
    execution_status: Literal["pending", "executing", "completed", "failed"] = Field(default="pending")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional action details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "action_id": "ACTION_001",
                "action": "store",
                "reasoning": "Generation exceeds demand by 150 MW, storing excess energy in battery",
                "timestamp": "2026-03-27T10:30:00",
                "magnitude": 150.0,
                "target_frequency": 50.0,
                "priority": 7,
                "execution_status": "completed",
                "details": {
                    "battery_charge_rate": 100.0,
                    "expected_completion": "2026-03-27T10:45:00"
                }
            }
        }
