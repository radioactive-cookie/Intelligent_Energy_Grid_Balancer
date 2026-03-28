"""Main FastAPI Application"""
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
import asyncio
import os
import logging
import random
import math
from datetime import datetime
from contextlib import asynccontextmanager

from config import get_settings
from routes import router
from utils import setup_logging, get_logger
<<<<<<< HEAD
from controllers import GridController, MetricsController, AlertController
from services.weather_service import weather_service
from services import simulation_state
=======
from controllers import GridController, AlertController
from services import simulation_state, simulation_engine, real_data_fetcher, carbon_service
>>>>>>> 1f2a52ecf0159046cd2db518ab0f121bea39cd72

logger = None
settings = None
DEMAND_NOISE_OFFSET_KW = 30
DEMAND_NOISE_SPAN_KW = DEMAND_NOISE_OFFSET_KW * 2
# MW delta threshold used to raise SURPLUS/DEFICIT alerts when imbalance is material.
IMBALANCE_THRESHOLD = float(os.getenv("IMBALANCE_THRESHOLD", "20"))
MAX_HISTORY = 20
gridHistory = []
BASE_MAX_LOAD = float(os.getenv("MAX_BASE_LOAD", "600"))
MAX_SOLAR_OUTPUT = float(os.getenv("MAX_SOLAR_OUTPUT", "500"))
MAX_WIND_OUTPUT = float(os.getenv("MAX_WIND_OUTPUT", "300"))
HOUSES_PLACEHOLDER_COUNT = 0


class ScenarioSimulationRequest(BaseModel):
    demandMultiplier: float = Field(1.0, ge=0.5, le=3.0)
    loadSheddingPercent: float = Field(0.0, ge=0.0, le=40.0)
    hour: int = Field(default_factory=lambda: datetime.utcnow().hour, ge=0, le=23)


def _round1(value: float) -> float:
    return round(float(value), 1)


def _round2(value: float) -> float:
    return round(float(value), 2)


def _supply_for_hour(hour: int) -> tuple[float, float]:
    daylight_factor = max(0.0, math.sin(((hour - 6) / 12) * math.pi))
    solar = _round1(MAX_SOLAR_OUTPUT * daylight_factor * 0.85)

    wind_base = 0.45 + 0.2 * math.cos(((hour + 2) / 24) * 2 * math.pi)
    wind = _round1(MAX_WIND_OUTPUT * max(0.2, min(wind_base, 0.95)))

    return solar, wind


def _get_pattern_for_hour(hour: int) -> str:
    if 6 <= hour < 9:
        return "morning-rush"
    if 9 <= hour < 17:
        return "midday"
    if 17 <= hour < 21:
        return "evening-peak"
    if 21 <= hour < 24:
        return "night"
    return "off-peak"


def computeGridSnapshot(hour: Optional[int] = None) -> dict:
    now = datetime.utcnow()
    snapshot_hour = now.hour if hour is None else hour

    dashboard = simulation_state.get_dashboard()
    fallback_generation = {
        "solar_mw": float(dashboard.get("solar_generation", dashboard.get("solar_mw", 0.0))),
        "wind_mw": float(dashboard.get("wind_generation", dashboard.get("wind_mw", 0.0))),
    }
    # Prefer real weather-derived generation when available and safely fall back to simulation values.
    weather_generation = real_data_fetcher.get_generation(fallback_generation)
    solar = round(float(weather_generation.get("solar_mw", fallback_generation["solar_mw"])), 1)
    wind = round(float(weather_generation.get("wind_mw", fallback_generation["wind_mw"])), 1)
    supply = round(solar + wind, 1)
    predicted = round(float(dashboard.get("demand", dashboard.get("demand_mw", 0.0))), 1)
    actual = round(
        predicted + (random.random() * DEMAND_NOISE_SPAN_KW - DEMAND_NOISE_OFFSET_KW), 1
    )
    delta = round(supply - actual, 1)

    denominator = max(supply, actual)
    if denominator == 0:
        efficiency = 100.0
    else:
        efficiency = round((min(supply, actual) / denominator * 100), 1)

    battery_level = round(float(simulation_engine.config.battery_current), 1)
    battery_capacity = round(float(simulation_engine.config.battery_capacity), 1)
    battery_percentage = round(
        (battery_level / battery_capacity * 100) if battery_capacity > 0 else 0.0, 1
    )
    is_charging = delta > 0 and battery_level < battery_capacity
    is_draining = delta < 0 and battery_level > 0
    charging_rate = round(abs(delta) if (is_charging or is_draining) else 0.0, 1)

    alerts = []
    if delta > IMBALANCE_THRESHOLD:
        alerts.append("SURPLUS")
    if delta < -IMBALANCE_THRESHOLD:
        alerts.append("DEFICIT")
    if battery_percentage < 10:
        alerts.append("BATTERY_CRITICAL")

    action = "storing" if is_charging else "releasing" if is_draining else "idle"
    carbon_intensity = carbon_service.get_carbon_intensity()
    data_source = weather_generation.get("dataSource", "simulated")
    raw_weather = weather_generation.get("rawWeather", {})
    grid_status = "SURPLUS" if delta >= 0 else "DEFICIT"
    sources = {
        "solar": solar,
        "wind": wind,
    }

    # Keep both nested and top-level fields for compatibility:
    # - nested fields support existing dashboard component bindings
    # - top-level fields match the hackathon demo response contract
    return {
        "energy": {
            "solar": solar,
            "wind": wind,
            "total": supply,
            "hour": snapshot_hour,
            "dataSource": data_source,
            "rawWeather": raw_weather,
        },
        "demand": {
            "predicted": predicted,
            "actual": actual,
            "pattern": _get_pattern_for_hour(snapshot_hour),
            "hour": snapshot_hour,
        },
        "battery": {
            "level": battery_level,
            "percentage": battery_percentage,
            "capacity": battery_capacity,
            "isCharging": is_charging,
            "isDraining": is_draining,
            "chargingRate": charging_rate,
        },
        "grid": {
            "action": action,
            "gridStatus": grid_status,
            "efficiency": efficiency,
            "delta": delta,
            "alerts": alerts,
            "carbonIntensity": carbon_intensity,
        },
        # Frontend-compatible top-level summary payload.
        "total_supply": supply,
        "total_demand": actual,
        "battery_level": battery_percentage,
        "grid_status": grid_status,
        # Temporary placeholder until explicit house telemetry is introduced.
        "houses": HOUSES_PLACEHOLDER_COUNT,
        "alerts": alerts,
        "sources": sources,
        "dataSource": data_source,
        "rawWeather": raw_weather,
        "carbonIntensity": carbon_intensity,
        "timestamp": now.isoformat(),
    }

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    global logger, settings
    
    # Startup
    settings = get_settings()
    logger = get_logger(__name__)
    setup_logging(settings.log_file, settings.log_level)
    logger.info("="*50)
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info("="*50)
    
    # Start background monitoring task
    monitoring_task = asyncio.create_task(monitor_and_broadcast())
    
    yield
    
    # Shutdown
    monitoring_task.cancel()
    logger.info("Shutting down application...")

async def monitor_and_broadcast():
    """Background task to periodically broadcast grid status updates"""
    global logger
    try:
        while True:
            snapshot = computeGridSnapshot()
            gridHistory.append(snapshot)
            if len(gridHistory) > MAX_HISTORY:
                gridHistory.pop(0)

            if manager.active_connections:
                try:
<<<<<<< HEAD
                    # Sync with real-world weather data for Bhubaneswar every ~5 mins (approx 60 cycles)
                    if not hasattr(monitor_and_broadcast, "weather_counter"):
                        monitor_and_broadcast.weather_counter = 0
                    
                    if monitor_and_broadcast.weather_counter % 60 == 0:
                        weather_data = await weather_service.get_current_weather()
                        simulation_state.update_from_weather(weather_data)
                    
                    monitor_and_broadcast.weather_counter += 1

                    metrics = MetricsController.get_system_metrics()
=======
>>>>>>> 1f2a52ecf0159046cd2db518ab0f121bea39cd72
                    await manager.broadcast({
                        "type": "GRID_UPDATE",
                        "data": snapshot
                    })
                except Exception as e:
                    logger.error(f"Error in broadcast: {e}")
            
            await asyncio.sleep(5)  # Update every 5 seconds
    except asyncio.CancelledError:
        logger.info("Monitoring task cancelled")

# Create FastAPI app
app = FastAPI(
    title="Intelligent Energy Grid Balancer",
    description="A production-ready backend system for intelligent energy grid management",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
frontend_url = os.getenv("FRONTEND_URL")
allowed_origins = [
    frontend_url,
    "https://intelligent-energy-grid-balancer.vercel.app",
    "http://localhost:5173",
]

if not frontend_url:
    logging.getLogger(__name__).warning(
        "FRONTEND_URL is not set; CORS is limited to default production/dev origins."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in allowed_origins if origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)

# ============================================
# WebSocket ENDPOINTS
# ============================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time grid updates.
    Streams grid status, battery level, and alerts.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Receive message from client (for future commands)
            data = await websocket.receive_text()
            logger.debug(f"Received from client: {data}")
            
            # For now, just acknowledge
            await websocket.send_json({
                "type": "ack",
                "message": "Connected to grid monitoring stream"
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.websocket("/ws/grid")
async def websocket_grid_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint specifically for grid status updates.
    Streams frequency, demand, generation, and stability score.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Send grid updates every 5 seconds
            grid_state = GridController.get_grid_status()
            await websocket.send_json({
                "type": "grid_update",
                "frequency": grid_state.frequency,
                "generation": grid_state.total_generation,
                "demand": grid_state.total_demand,
                "stability_score": grid_state.grid_stability_score,
                "is_stable": grid_state.is_stable,
                "timestamp": grid_state.timestamp.isoformat()
            })
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ============================================
# Frontend Compatibility API
# ============================================

@app.get("/api/history")
async def get_api_history():
    return {"history": gridHistory, "count": len(gridHistory)}


@app.get("/api/predict-demand")
async def get_api_predict_demand(hour: Optional[int] = None):
    snapshot = computeGridSnapshot(hour)
    return {
        "predicted": snapshot["demand"]["predicted"],
        "actual": snapshot["demand"]["actual"],
        "pattern": snapshot["demand"]["pattern"],
        "hour": snapshot["demand"]["hour"],
        "timestamp": snapshot["timestamp"],
    }


@app.get("/api/battery-status")
async def get_api_battery_status(hour: Optional[int] = None):
    snapshot = computeGridSnapshot(hour)
    return {
        **snapshot["battery"],
        "timestamp": snapshot["timestamp"],
    }


@app.get("/api/balance-grid")
async def get_api_balance_grid(hour: Optional[int] = None):
    snapshot = computeGridSnapshot(hour)
    demand_value = snapshot["demand"]["actual"]
    supply_value = snapshot["energy"]["total"]
    delta = snapshot["grid"]["delta"]
    return {
        "action": snapshot["grid"]["action"],
        "surplus": round(max(delta, 0), 1),
        "deficit": round(max(-delta, 0), 1),
        "batteryUsed": snapshot["battery"]["chargingRate"],
        "gridStatus": snapshot["grid"]["gridStatus"],
        "efficiency": snapshot["grid"]["efficiency"],
        "supply": supply_value,
        "demand": snapshot["demand"],
        "demandValue": demand_value,
        "delta": delta,
        "hour": snapshot["demand"]["hour"],
        "timestamp": snapshot["timestamp"],
        "alerts": snapshot["grid"]["alerts"],
        "battery": snapshot["battery"],
        "energy": snapshot["energy"],
        "sources": snapshot["sources"],
        "total_supply": snapshot["total_supply"],
        "total_demand": snapshot["total_demand"],
        "battery_level": snapshot["battery_level"],
        "grid_status": snapshot["grid_status"],
        "houses": snapshot["houses"],
        "dataSource": snapshot["dataSource"],
        "rawWeather": snapshot["rawWeather"],
        "carbonIntensity": snapshot["carbonIntensity"],
    }


@app.post("/api/balance-grid")
async def post_api_balance_grid(hour: Optional[int] = None):
    return await get_api_balance_grid(hour)


@app.post("/api/simulate-scenario")
@app.post("/simulate-scenario")
async def post_api_simulate_scenario(payload: ScenarioSimulationRequest):
    hour = payload.hour
    demand_multiplier = payload.demandMultiplier
    load_shedding_percent = payload.loadSheddingPercent

    solar, wind = _supply_for_hour(hour)
    total_supply = _round1(solar + wind)

    scaled_demand = _round1(BASE_MAX_LOAD * demand_multiplier)
    industrial_demand = _round1(scaled_demand * 0.4)
    commercial_demand = _round1(scaled_demand * 0.3)
    residential_demand = _round1(scaled_demand * 0.3)

    industrial_shed = _round1(industrial_demand * (load_shedding_percent / 100))
    commercial_shed_percent = _round1(load_shedding_percent / 2)
    commercial_shed = _round1(commercial_demand * (commercial_shed_percent / 100))
    total_shed = _round1(industrial_shed + commercial_shed)
    demand_after_shedding = _round1(scaled_demand - total_shed)
    gap = _round1(demand_after_shedding - total_supply)

    battery_current = _round1(float(simulation_engine.config.battery_current))
    battery_capacity = _round1(float(simulation_engine.config.battery_capacity))
    battery_percent = _round1((battery_current / battery_capacity * 100) if battery_capacity > 0 else 0.0)
    net_drain = _round1(gap if gap > 0 else 0.0)

    survival_hours = None
    survival_hours_with_solar = None
    if gap > 0:
        survival_hours = _round2(battery_current / max(gap, 1))
        survival_hours_with_solar = _round2(
            battery_current / max(gap - solar * 0.3, 1)
        )

    if gap <= 0:
        strategy_label = "SURPLUS_STORE"
    elif gap <= 100:
        strategy_label = "MINOR_DEFICIT_BATTERY_ONLY"
    elif gap <= 400:
        strategy_label = "LOAD_SHEDDING_AND_BATTERY"
    else:
        strategy_label = "CRITICAL_SHED_ALL"

    if strategy_label == "SURPLUS_STORE":
        steps = [
            {"order": 1, "action": "Maximise renewable harvest", "detail": f"Solar + wind generation: {_round1(total_supply)} kW"},
            {"order": 2, "action": "Store excess energy", "detail": f"Charge battery with {_round1(abs(gap))} kW surplus"},
            {"order": 3, "action": "Prepare reserve margin", "detail": "Maintain charge for next peak period"},
        ]
    elif strategy_label == "MINOR_DEFICIT_BATTERY_ONLY":
        steps = [
            {"order": 1, "action": "Maximise renewable harvest", "detail": f"Solar + wind at current output: {_round1(total_supply)} kW"},
            {"order": 2, "action": "Draw from battery reserve", "detail": f"Cover net deficit of {_round1(gap)} kW"},
            {"order": 3, "action": "Reassess in 15 minutes", "detail": "No load shedding needed at this deficit level"},
        ]
    elif strategy_label == "LOAD_SHEDDING_AND_BATTERY":
        steps = [
            {"order": 1, "action": "Maximise renewable harvest", "detail": f"Solar + wind at full output: {_round1(total_supply)} kW"},
            {"order": 2, "action": "Industrial demand response", "detail": f"Shed {load_shedding_percent:.0f}% from industrial zone: -{_round1(industrial_shed)} kW"},
            {"order": 3, "action": "Commercial demand response", "detail": f"Shed {commercial_shed_percent:.0f}% from commercial zone: -{_round1(commercial_shed)} kW"},
            {"order": 4, "action": "Draw from battery reserve", "detail": f"Net deficit {_round1(gap)} kW covered for {_round1(survival_hours) if survival_hours is not None else '0'} hrs"},
            {"order": 5, "action": "Schedule off-peak recharge", "detail": "Recharge 00:00–05:00 at max rate"},
        ]
    else:
        steps = [
            {"order": 1, "action": "Activate emergency demand response", "detail": f"Industrial shed -{_round1(industrial_shed)} kW, commercial shed -{_round1(commercial_shed)} kW"},
            {"order": 2, "action": "Draw maximum battery support", "detail": f"Battery draw {_round1(net_drain)} kW at critical level"},
            {"order": 3, "action": "Trigger critical load protection", "detail": "Protect residential essentials and prepare contingency imports"},
        ]

    alerts = []
    if gap > 0:
        alerts.append("DEFICIT")
        alerts.append("BATTERY_DRAW_ACTIVE")
        if gap > 400:
            alerts.append("CRITICAL_DEFICIT")
    else:
        alerts.append("SURPLUS")

    scenario_timestamp = datetime.utcnow().replace(
        hour=hour, minute=0, second=0, microsecond=0
    ).isoformat() + "Z"

    return {
        "scenario": {
            "demandMultiplier": _round1(demand_multiplier),
            "hour": hour,
        },
        "supply": {
            "solar": _round1(solar),
            "wind": _round1(wind),
            "total": _round1(total_supply),
        },
        "demand": {
            "base": _round1(BASE_MAX_LOAD),
            "scaled": _round1(scaled_demand),
            "afterShedding": _round1(demand_after_shedding),
            "loadShedKw": _round1(total_shed),
        },
        "gap": _round1(gap),
        "gridStatus": "DEFICIT" if gap > 0 else "SURPLUS",
        "battery": {
            "currentKwh": battery_current,
            "capacityKwh": battery_capacity,
            "percentCharged": battery_percent,
            "netDrainRateKw": _round1(net_drain),
            "survivalHours": survival_hours,
            "survivalHoursWithSolar": survival_hours_with_solar,
        },
        "zones": {
            "industrial": {
                "demandKw": _round1(industrial_demand),
                "shedKw": _round1(industrial_shed),
                "shedPercent": _round1(load_shedding_percent),
            },
            "commercial": {
                "demandKw": _round1(commercial_demand),
                "shedKw": _round1(commercial_shed),
                "shedPercent": _round1(commercial_shed_percent),
            },
            "residential": {
                "demandKw": _round1(residential_demand),
                "shedKw": 0.0,
                "shedPercent": 0.0,
            },
        },
        "strategy": {
            "label": strategy_label,
            "steps": steps,
        },
        "alerts": alerts,
        "timestamp": scenario_timestamp,
    }


# ============================================
# DOCUMENTATION
# ============================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API documentation"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Intelligent Energy Grid Balancer</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            h1 { color: #333; }
            .endpoint { 
                background: white; 
                padding: 15px; 
                margin: 10px 0; 
                border-radius: 5px;
                border-left: 4px solid #007bff;
            }
            .method { font-weight: bold; color: #007bff; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>⚡ Intelligent Energy Grid Balancer</h1>
        <p>A production-ready backend system for intelligent energy grid management and balancing.</p>
        
        <h2>API Documentation</h2>
        <p>Full API documentation available at <a href="/docs">/docs</a> (Swagger UI)</p>
        <p>Alternative docs at <a href="/redoc">/redoc</a> (ReDoc)</p>
        
        <h2>Key Features</h2>
        <ul>
            <li>Real-time grid status monitoring</li>
            <li>Intelligent energy balancing engine</li>
            <li>Battery storage management</li>
            <li>AI-powered demand and generation prediction</li>
            <li>Scenario simulation engine</li>
            <li>WebSocket support for live updates</li>
            <li>Comprehensive alerting system</li>
            <li>System metrics and analytics</li>
        </ul>
        
        <h2>Quick Start</h2>
        <div class="endpoint">
            <p><span class="method">GET</span> /health - Check service health</p>
        </div>
        <div class="endpoint">
            <p><span class="method">GET</span> /grid/status - Get current grid status</p>
        </div>
        <div class="endpoint">
            <p><span class="method">POST</span> /balance/run - Run balancing engine</p>
        </div>
        <div class="endpoint">
            <p><span class="method">GET</span> /metrics - Get system metrics</p>
        </div>
        
        <h2>WebSocket Endpoints</h2>
        <div class="endpoint">
            <p><span class="method">WS</span> /ws - Connect to all system updates</p>
        </div>
        <div class="endpoint">
            <p><span class="method">WS</span> /ws/grid - Connect to grid updates only</p>
        </div>
        
        <h2>System Architecture</h2>
        <ul>
            <li><strong>Models:</strong> Pydantic models for data validation</li>
            <li><strong>Services:</strong> Business logic including balancing engine, predictions, monitoring</li>
            <li><strong>Controllers:</strong> Request handlers for API endpoints</li>
            <li><strong>Utils:</strong> Helper functions and mock data generators</li>
            <li><strong>Config:</strong> Configuration management</li>
        </ul>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    logger = get_logger(__name__)
    
    uvicorn.run(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.lower()
    )
