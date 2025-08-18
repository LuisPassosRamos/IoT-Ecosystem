"""
FastAPI IoT Backend - Main application
"""

import os
import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
from typing import List

# Import models and services
from models.schemas import create_tables
from services.mqtt_client import init_mqtt_service, get_mqtt_service
from services.openweather import get_openweather_service
from api.v1 import auth, sensors

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# WebSocket connections manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)

# Global connection manager
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting IoT Backend...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    # Initialize MQTT service
    mqtt_service = init_mqtt_service(MQTT_HOST, MQTT_PORT)
    
    # Add WebSocket callback to MQTT service
    async def websocket_callback(message: dict):
        await manager.broadcast(json.dumps(message))
    
    mqtt_service.add_websocket_callback(websocket_callback)
    
    # Start MQTT service
    if mqtt_service.start():
        logger.info("MQTT service started successfully")
    else:
        logger.error("Failed to start MQTT service")
    
    # Initialize OpenWeather service
    weather_service = get_openweather_service()
    logger.info("OpenWeather service initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IoT Backend...")
    mqtt_service.stop()

# Create FastAPI app
app = FastAPI(
    title="IoT Ecosystem Backend",
    description="Backend API for IoT environmental monitoring system",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router)
app.include_router(sensors.router)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with basic API information"""
    return """
    <html>
        <head>
            <title>IoT Ecosystem Backend</title>
        </head>
        <body>
            <h1>IoT Ecosystem Backend API</h1>
            <p>Welcome to the IoT environmental monitoring backend!</p>
            <h2>API Documentation</h2>
            <ul>
                <li><a href="/docs">Swagger UI</a></li>
                <li><a href="/redoc">ReDoc</a></li>
            </ul>
            <h2>WebSocket</h2>
            <ul>
                <li><a href="/ws">WebSocket endpoint for real-time updates</a></li>
            </ul>
            <h2>API Endpoints</h2>
            <ul>
                <li><strong>Authentication:</strong> /v1/auth/login</li>
                <li><strong>Sensors:</strong> /v1/sensors/latest</li>
                <li><strong>History:</strong> /v1/sensors/history</li>
                <li><strong>Weather:</strong> /v1/sensors/external/weather</li>
            </ul>
        </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        mqtt_service = get_mqtt_service()
        mqtt_status = "connected" if mqtt_service.connected else "disconnected"
    except:
        mqtt_status = "unavailable"
    
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",
        "services": {
            "mqtt": mqtt_status,
            "database": "available",
            "weather": "available"
        }
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time sensor data"""
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "data": {"status": "connected"},
                "timestamp": "2024-01-01T00:00:00Z"
            }),
            websocket
        )
        
        # Listen for messages from client
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "data": {},
                            "timestamp": "2024-01-01T00:00:00Z"
                        }),
                        websocket
                    )
                elif message.get("type") == "subscribe":
                    # Handle subscription requests
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "subscribed",
                            "data": {"topics": message.get("topics", [])},
                            "timestamp": "2024-01-01T00:00:00Z"
                        }),
                        websocket
                    )
                
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({
                        "type": "error",
                        "data": {"message": "Invalid JSON format"},
                        "timestamp": "2024-01-01T00:00:00Z"
                    }),
                    websocket
                )
            except Exception as e:
                logger.error(f"WebSocket message handling error: {e}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    try:
        mqtt_service = get_mqtt_service()
        latest_readings = mqtt_service.get_latest_readings()
        
        return {
            "api_version": "1.0.0",
            "mqtt_connected": mqtt_service.connected,
            "active_websockets": len(manager.active_connections),
            "latest_readings_count": len(latest_readings),
            "uptime": "System running"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )