"""Alert Model"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal, Optional

class Alert(BaseModel):
    """Model for system alerts"""
    alert_id: str = Field(..., description="Unique identifier for alert")
    type: Literal["frequency_deviation", "battery_low", "frequency_critical", "demand_spike", "generation_drop", "imbalance"] = Field(..., description="Type of alert")
    message: str = Field(..., description="Alert message")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Alert severity level")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = Field(default=False, description="Whether alert has been resolved")
    resolution_time: Optional[datetime] = Field(default=None, description="Time when alert was resolved")
    component: str = Field(..., description="System component triggering alert")
    action_taken: Optional[str] = Field(default=None, description="Action taken in response to alert")
    
    class Config:
        json_schema_extra = {
            "example": {
                "alert_id": "ALERT_001",
                "type": "frequency_deviation",
                "message": "Grid frequency deviated to 49.2 Hz",
                "severity": "high",
                "timestamp": "2026-03-27T10:30:00",
                "resolved": False,
                "resolution_time": None,
                "component": "GridFrequencyMonitor",
                "action_taken": None
            }
        }
