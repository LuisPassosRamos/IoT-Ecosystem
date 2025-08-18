#!/usr/bin/env python3
"""
IoT-Ecosystem Cloud Backend
FastAPI application for handling sensor data, authentication, and external API integration.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import Dict, Any, List
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import sensors, auth
from app.services.mqtt_client import mqtt_client
from app.services.openweather import openweather_service
from app.models.schemas import WeatherResponse, SystemStatus, WSMessage

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state for tracking system status
app_state = {
    "start_time": None,
    "active_websockets": [],
    "system_stats": {
        "total_readings": 0,
        "mqtt_connected": False,
        "last_reading_time": None
    }
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting IoT-Ecosystem Cloud Backend...")
    
    # Record start time
    from datetime import datetime
    app_state["start_time"] = datetime.utcnow()
    
    # Initialize MQTT client
    mqtt_client.set_message_handler(handle_mqtt_message)
    mqtt_connected = await mqtt_client.connect()
    app_state["system_stats"]["mqtt_connected"] = mqtt_connected
    
    if mqtt_connected:
        logger.info("MQTT client connected successfully")
    else:
        logger.error("Failed to connect MQTT client")
    
    # Check OpenWeather service configuration
    if openweather_service.is_configured():
        logger.info("OpenWeatherMap service configured")
    else:
        logger.warning("OpenWeatherMap service not configured - weather features disabled")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down IoT-Ecosystem Cloud Backend...")
    await mqtt_client.disconnect()
    logger.info("Application shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="IoT-Ecosystem Cloud Backend",
    description="Backend API for IoT sensor data collection, processing, and real-time monitoring",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(sensors.router, prefix="/v1/sensors", tags=["sensors"])
app.include_router(auth.router, prefix="/v1/auth", tags=["authentication"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        app_state["active_websockets"] = self.active_connections
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            app_state["active_websockets"] = self.active_connections
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

async def handle_mqtt_message(topic: str, payload: Dict[str, Any]):
    """Handle incoming MQTT messages."""
    try:
        # Store sensor reading
        await sensors.add_sensor_reading(topic, payload)
        
        # Update system stats
        app_state["system_stats"]["total_readings"] += 1
        app_state["system_stats"]["last_reading_time"] = payload.get("ts")
        
        # Broadcast to WebSocket clients
        ws_message = WSMessage(
            type="sensor_data",
            data={
                "topic": topic,
                "payload": payload,
                "sensor_type": payload.get("type"),
                "value": payload.get("value"),
                "anomaly": payload.get("anomaly", False)
            }
        )
        
        await manager.broadcast(ws_message.dict())
        
    except Exception as e:
        logger.error(f"Error handling MQTT message: {e}")

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "service": "IoT-Ecosystem Cloud Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "sensors": "/v1/sensors/",
            "auth": "/v1/auth/",
            "weather": "/v1/external/weather",
            "websocket": "/ws",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "mqtt_connected": app_state["system_stats"]["mqtt_connected"],
        "active_websockets": len(app_state["active_websockets"]),
        "total_readings": app_state["system_stats"]["total_readings"]
    }

@app.get("/v1/external/weather", response_model=WeatherResponse)
async def get_weather(city: str = Query(..., description="City name")):
    """Get weather data from OpenWeatherMap API and compare with local sensors."""
    try:
        # Get weather data
        weather_data = await openweather_service.get_weather(city)
        
        if not weather_data or "error" in weather_data:
            raise HTTPException(
                status_code=404 if weather_data and weather_data.get("error") == "City not found" else 500,
                detail=weather_data.get("error", "Failed to fetch weather data") if weather_data else "Failed to fetch weather data"
            )
        
        # Get local sensor data for comparison
        local_data = sensors.get_local_sensor_data()
        
        # Compare with local sensors
        comparison = openweather_service.compare_with_local_sensors(weather_data, local_data)
        
        return WeatherResponse(
            city=weather_data["city"],
            country=weather_data["country"],
            temperature=weather_data["temperature"],
            humidity=weather_data["humidity"],
            description=weather_data["description"],
            timestamp=weather_data["timestamp"],
            comparison=comparison
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weather data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/v1/system/status", response_model=SystemStatus)
async def get_system_status():
    """Get system status information."""
    try:
        from datetime import datetime
        
        # Calculate uptime
        uptime_seconds = 0
        if app_state["start_time"]:
            uptime_seconds = int((datetime.utcnow() - app_state["start_time"]).total_seconds())
        
        # Get active sensors
        active_sensors = []
        if hasattr(sensors, 'sensor_readings'):
            sensor_ids = set()
            for reading in sensors.sensor_readings[-100:]:  # Check last 100 readings
                if reading.get("sensor_id"):
                    sensor_ids.add(reading["sensor_id"])
            active_sensors = list(sensor_ids)
        
        return SystemStatus(
            mqtt_connected=app_state["system_stats"]["mqtt_connected"],
            database_connected=True,  # Always true for in-memory storage
            total_readings=app_state["system_stats"]["total_readings"],
            active_sensors=active_sensors,
            uptime_seconds=uptime_seconds,
            last_reading_time=app_state["system_stats"]["last_reading_time"]
        )
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming."""
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        welcome_message = WSMessage(
            type="connection_established",
            data={
                "message": "Connected to IoT-Ecosystem real-time stream",
                "features": ["sensor_data", "system_status", "anomaly_alerts"]
            }
        )
        await manager.send_message(welcome_message.dict(), websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                
                # Handle client requests
                if message.get("type") == "ping":
                    pong_message = WSMessage(type="pong", data={"timestamp": message.get("timestamp")})
                    await manager.send_message(pong_message.dict(), websocket)
                
                elif message.get("type") == "get_latest":
                    # Send latest sensor data
                    latest_data = await sensors.get_latest_readings()
                    data_message = WSMessage(type="latest_data", data=latest_data.dict())
                    await manager.send_message(data_message.dict(), websocket)
                
            except json.JSONDecodeError:
                error_message = WSMessage(type="error", data={"message": "Invalid JSON format"})
                await manager.send_message(error_message.dict(), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )