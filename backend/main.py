"""Main FastAPI Application"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
import asyncio
import json
import os
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from config import get_settings
from routes import router
from utils import setup_logging, get_logger
from controllers import GridController, MetricsController, AlertController

logger = None
settings = None

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
            if manager.active_connections:
                try:
                    metrics = MetricsController.get_system_metrics()
                    await manager.broadcast({
                        "type": "metrics_update",
                        "data": metrics
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
