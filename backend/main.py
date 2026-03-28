"""Main FastAPI Application"""
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import os
import logging
import random
from datetime import datetime
from contextlib import asynccontextmanager

from config import get_settings
from routes import router
from utils import setup_logging, get_logger
from controllers import GridController, AlertController
from services import simulation_state, simulation_engine

logger = None
settings = None
DEMAND_NOISE_OFFSET_KW = 30
DEMAND_NOISE_SPAN_KW = DEMAND_NOISE_OFFSET_KW * 2
# MW delta threshold used to raise SURPLUS/DEFICIT alerts when imbalance is material.
IMBALANCE_THRESHOLD = float(os.getenv("IMBALANCE_THRESHOLD", "20"))
MAX_HISTORY = 20
gridHistory = []


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
    solar = round(float(dashboard.get("solar_generation", dashboard.get("solar_mw", 0.0))), 1)
    wind = round(float(dashboard.get("wind_generation", dashboard.get("wind_mw", 0.0))), 1)
    supply = round(float(dashboard.get("total_generation", solar + wind)), 1)
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

    return {
        "energy": {
            "solar": solar,
            "wind": wind,
            "total": supply,
            "hour": snapshot_hour,
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
            "gridStatus": "SURPLUS" if delta >= 0 else "DEFICIT",
            "efficiency": efficiency,
            "delta": delta,
            "alerts": alerts,
        },
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
    }


@app.post("/api/balance-grid")
async def post_api_balance_grid(hour: Optional[int] = None):
    return await get_api_balance_grid(hour)


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
