"""Routes for API endpoints"""
from fastapi import APIRouter, Query
from typing import Optional, List
from pydantic import BaseModel, Field
from controllers import (
    GridController,
    EnergyController,
    BatteryController,
    BalancingController,
    PredictionController,
    SimulationController,
    AlertController,
    MetricsController
)
from models import BalancingAction

# Input models for real dashboard
class GridInputsUpdate(BaseModel):
    """Model for updating grid simulation inputs"""
    solar_mw: Optional[float] = None
    wind_mw: Optional[float] = None
    demand_mw: Optional[float] = None
    battery_current: Optional[float] = None
    battery_capacity: Optional[float] = None

class GridSimulationStep(BaseModel):
    """Model for simulating one time step"""
    solar_mw: float
    wind_mw: float
    demand_mw: float

# Add simulation models
class SimulationScenarioMW(BaseModel):
    """MW-based simulation scenario"""
    solar_mw: float = Field(..., ge=0, description="Solar generation in MW")
    wind_mw: float = Field(..., ge=0, description="Wind generation in MW")
    demand_mw: float = Field(..., ge=0, description="Total demand in MW")

class SimulationStep(BaseModel):
    """Single time step for multi-step simulation"""
    solar_mw: float = Field(..., ge=0, description="Solar generation in MW")
    wind_mw: float = Field(..., ge=0, description="Wind generation in MW")
    demand_mw: float = Field(..., ge=0, description="Total demand in MW")

class MultiStepSimulation(BaseModel):
    """Multi-step simulation run"""
    steps: List[SimulationStep] = Field(..., min_items=1, max_items=10, description="1-10 simulation steps")

# Create routers
router = APIRouter()

# ============================================
# GRID STATUS ENDPOINTS
# ============================================

@router.get("/grid/status", tags=["Grid Status"])
async def get_grid_status():
    """Get current grid status including frequency, demand, generation"""
    return GridController.get_grid_status()

@router.get("/grid/history", tags=["Grid Status"])
async def get_grid_history(limit: int = Query(100, ge=1, le=1000)):
    """Get grid state history"""
    return GridController.get_grid_history(limit)

@router.get("/grid/inputs", tags=["Grid Configuration"])
async def get_grid_inputs():
    """Get current simulation inputs (real dashboard inputs)"""
    return GridController.get_grid_inputs()

@router.post("/grid/update-inputs", tags=["Grid Configuration"])
async def update_grid_inputs(inputs: GridInputsUpdate):
    """
    Update grid simulation inputs and recalculate dashboard values.
    All fields are optional - only provided values are updated.
    
    Example:
    {
        "solar_mw": 150.0,
        "wind_mw": 200.0,
        "demand_mw": 350.0,
        "battery_current": 350.0,
        "battery_capacity": 500.0
    }
    """
    return GridController.update_grid_inputs(
        solar_mw=inputs.solar_mw,
        wind_mw=inputs.wind_mw,
        demand_mw=inputs.demand_mw,
        battery_current=inputs.battery_current,
        battery_capacity=inputs.battery_capacity
    )

@router.post("/grid/simulate-step", tags=["Grid Configuration"])
async def simulate_one_step(step: GridSimulationStep):
    """
    Simulate one time step with new generation and demand values.
    Battery automatically adjusts based on surplus/deficit.
    
    Example:
    {
        "solar_mw": 150.0,
        "wind_mw": 200.0,
        "demand_mw": 320.0
    }
    """
    return GridController.simulate_step(step.solar_mw, step.wind_mw, step.demand_mw)

# ============================================
# ENERGY ENDPOINTS
# ============================================

@router.get("/energy/solar", tags=["Energy"])
async def get_solar_generation():
    """Get current solar generation"""
    return EnergyController.get_solar_generation()

@router.get("/energy/wind", tags=["Energy"])
async def get_wind_generation():
    """Get current wind generation"""
    return EnergyController.get_wind_generation()

@router.get("/energy/total", tags=["Energy"])
async def get_total_generation():
    """Get total energy generation from all sources"""
    return EnergyController.get_total_generation()

# ============================================
# BATTERY ENDPOINTS
# ============================================

@router.get("/battery/status", tags=["Battery"])
async def get_battery_status():
    """Get current battery status"""
    return BatteryController.get_battery_status()

@router.post("/battery/charge", tags=["Battery"])
async def charge_battery(amount_kw: float = Query(..., ge=0)):
    """Charge battery by specified amount in kW"""
    return BatteryController.charge_battery(amount_kw)

@router.post("/battery/discharge", tags=["Battery"])
async def discharge_battery(amount_kw: float = Query(..., ge=0)):
    """Discharge battery by specified amount in kW"""
    return BatteryController.discharge_battery(amount_kw)

# ============================================
# BALANCING ENDPOINTS
# ============================================

@router.post("/balance/run", tags=["Balancing"])
async def run_balancing():
    """
    Run the balancing decision engine.
    Returns recommended action: store, release, shed_load, demand_response, or none
    """
    return BalancingController.run_balancing()

@router.get("/balance/history", tags=["Balancing"])
async def get_balancing_history(limit: int = Query(100, ge=1, le=1000)):
    """Get history of balancing actions"""
    return BalancingController.get_action_history(limit)

# ============================================
# PREDICTION ENDPOINTS
# ============================================

@router.post("/predict/generation/solar", tags=["Predictions"])
async def predict_solar_generation(hours: int = Query(24, ge=1, le=168)):
    """Predict solar generation for next N hours"""
    return PredictionController.predict_solar_generation(hours)

@router.post("/predict/generation/wind", tags=["Predictions"])
async def predict_wind_generation(hours: int = Query(24, ge=1, le=168)):
    """Predict wind generation for next N hours"""
    return PredictionController.predict_wind_generation(hours)

@router.post("/predict/demand", tags=["Predictions"])
async def predict_demand(hours: int = Query(24, ge=1, le=168)):
    """Predict electricity demand for next N hours"""
    return PredictionController.predict_demand(hours)

# ============================================
# SIMULATION ENDPOINTS (MW-based)
# ============================================

@router.post("/simulate/scenario", tags=["Simulation"])
async def simulate_scenario(scenario: SimulationScenarioMW):
    """
    Simulate a grid scenario with MW-based inputs.
    
    Implements realistic power grid calculations:
    - Total generation = solar_mw + wind_mw
    - Battery charge/discharge based on surplus/deficit
    - Grid frequency calculation (50 Hz nominal)
    - Efficiency and grid status determination
    - Load shedding calculation if needed
    - Grid stability score (0-100)
    
    Example:
    {
        "solar_mw": 150.0,
        "wind_mw": 200.0,
        "demand_mw": 350.0
    }
    
    Response includes:
    - inputs: Your input values
    - results: All calculated values (generation, frequency, efficiency, battery state, grid status)
    - timestamp: When simulation was run
    """
    return SimulationController.run_scenario(
        scenario.solar_mw,
        scenario.wind_mw,
        scenario.demand_mw
    )

@router.post("/simulate/multi-step", tags=["Simulation"])
async def simulate_multi_step(simulation: MultiStepSimulation):
    """
    Simulate multiple time steps sequentially.
    
    Battery state updates across steps. Maximum 10 steps per request.
    
    Example:
    {
        "steps": [
            {"solar_mw": 150, "wind_mw": 200, "demand_mw": 350},
            {"solar_mw": 160, "wind_mw": 210, "demand_mw": 360},
            {"solar_mw": 140, "wind_mw": 190, "demand_mw": 340}
        ]
    }
    
    Response includes:
    - steps: Results for each step
    - summary: Aggregated statistics across all steps
    - timestamp: When simulation was run
    """
    return SimulationController.run_multi_step_simulation(
        [{"solar_mw": s.solar_mw, "wind_mw": s.wind_mw, "demand_mw": s.demand_mw} 
         for s in simulation.steps]
    )

@router.get("/simulate/history", tags=["Simulation"])
async def get_simulation_history(limit: int = Query(50, ge=1, le=100)):
    """Get historical simulation runs"""
    return SimulationController.get_simulation_history(limit)

@router.post("/simulate/reset-state", tags=["Simulation"])
async def reset_simulation_state(battery_current: float = Query(250.0, ge=0, le=500)):
    """
    Reset simulation state (battery level).
    Useful between different scenario tests.
    """
    return SimulationController.reset_simulation_state(battery_current)

# ============================================
# ALERT ENDPOINTS
# ============================================

@router.get("/alerts", tags=["Alerts"])
async def get_alerts():
    """Get all active and historical alerts"""
    return AlertController.get_all_alerts()

@router.get("/alerts/history", tags=["Alerts"])
async def get_alert_history(limit: int = Query(100, ge=1, le=1000)):
    """Get alert history"""
    return AlertController.get_alert_history(limit)

@router.post("/alerts/{alert_id}/resolve", tags=["Alerts"])
async def resolve_alert(alert_id: str):
    """Mark an alert as resolved"""
    return AlertController.resolve_alert(alert_id)

# ============================================
# METRICS & STATISTICS
# ============================================

@router.get("/metrics", tags=["Metrics"])
async def get_system_metrics():
    """Get overall system metrics and statistics"""
    return MetricsController.get_system_metrics()

# ============================================
# HEALTH CHECK
# ============================================

@router.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Intelligent Energy Grid Balancer",
        "version": "1.0.0"
    }
