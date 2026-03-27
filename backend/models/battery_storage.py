"""Battery Storage Model"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class BatteryStorage(BaseModel):
    """Model for battery storage system"""
    battery_id: str = Field(..., description="Unique identifier for battery")
    capacity: float = Field(..., ge=0, description="Total capacity in kWh")
    current_level: float = Field(..., ge=0, description="Current charge level in kWh")
    charge_rate: float = Field(..., ge=0, description="Charging rate in kW")
    discharge_rate: float = Field(..., ge=0, description="Discharging rate in kW")
    state_of_charge: float = Field(default=0, ge=0, le=100, description="State of charge percentage")
    status: str = Field(default="idle", description="idle, charging, discharging")
    health: float = Field(default=100, ge=0, le=100, description="Battery health percentage")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    temperature: float = Field(default=25.0, description="Battery temperature in Celsius")
    cycles: int = Field(default=0, description="Number of charge/discharge cycles")
    
    class Config:
        json_schema_extra = {
            "example": {
                "battery_id": "BATT_01",
                "capacity": 500.0,
                "current_level": 350.0,
                "charge_rate": 100.0,
                "discharge_rate": 100.0,
                "state_of_charge": 70.0,
                "status": "idle",
                "health": 95.0,
                "timestamp": "2026-03-27T10:30:00",
                "temperature": 25.0,
                "cycles": 1250
            }
        }
