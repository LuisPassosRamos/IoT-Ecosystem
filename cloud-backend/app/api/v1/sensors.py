from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
import logging
from datetime import datetime, timedelta

from ..models.schemas import (
    LatestReadingsResponse, 
    HistoryResponse, 
    SensorReadingResponse,
    HistoryQueryParams
)
from ..services.openweather import openweather_service

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory storage for sensor readings (in production, use a proper database)
sensor_readings: List[dict] = []

def get_latest_reading_by_type(sensor_type: str) -> Optional[dict]:
    """Get the latest reading for a specific sensor type."""
    readings = [r for r in sensor_readings if r.get("sensor_type") == sensor_type]
    if readings:
        return max(readings, key=lambda x: x.get("timestamp", datetime.min))
    return None

def convert_to_response_model(reading: dict) -> SensorReadingResponse:
    """Convert internal reading dict to response model."""
    return SensorReadingResponse(
        id=reading.get("id", 0),
        timestamp=reading.get("timestamp", datetime.utcnow()),
        sensor_type=reading.get("sensor_type", "unknown"),
        sensor_id=reading.get("sensor_id", "unknown"),
        value=reading.get("value", 0.0),
        unit=reading.get("unit", ""),
        origin=reading.get("origin", "unknown"),
        anomaly=reading.get("anomaly", False),
        anomaly_details=reading.get("anomaly_details"),
        created_at=reading.get("created_at", datetime.utcnow())
    )

@router.get("/latest", response_model=LatestReadingsResponse)
async def get_latest_readings():
    """Get the latest readings from all sensor types."""
    try:
        # Get latest reading for each sensor type
        latest_temp = get_latest_reading_by_type("temperature")
        latest_humidity = get_latest_reading_by_type("humidity") 
        latest_luminosity = get_latest_reading_by_type("luminosity")
        
        return LatestReadingsResponse(
            temperature=convert_to_response_model(latest_temp) if latest_temp else None,
            humidity=convert_to_response_model(latest_humidity) if latest_humidity else None,
            luminosity=convert_to_response_model(latest_luminosity) if latest_luminosity else None,
            total_readings=len(sensor_readings)
        )
        
    except Exception as e:
        logger.error(f"Error getting latest readings: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/history", response_model=HistoryResponse)
async def get_sensor_history(
    sensor_id: Optional[str] = Query(None, description="Filter by sensor ID"),
    sensor_type: Optional[str] = Query(None, description="Filter by sensor type (temperature, humidity, luminosity)"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of readings"),
    anomalies_only: bool = Query(False, description="Return only anomalous readings")
):
    """Get historical sensor readings with optional filtering."""
    try:
        # Apply filters
        filtered_readings = sensor_readings.copy()
        
        if sensor_id:
            filtered_readings = [r for r in filtered_readings if r.get("sensor_id") == sensor_id]
        
        if sensor_type:
            filtered_readings = [r for r in filtered_readings if r.get("sensor_type") == sensor_type]
        
        if anomalies_only:
            filtered_readings = [r for r in filtered_readings if r.get("anomaly", False)]
        
        # Sort by timestamp (most recent first)
        filtered_readings.sort(key=lambda x: x.get("timestamp", datetime.min), reverse=True)
        
        # Apply limit
        limited_readings = filtered_readings[:limit]
        
        return HistoryResponse(
            readings=[convert_to_response_model(r) for r in limited_readings],
            total_count=len(filtered_readings),
            filters_applied={
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "limit": limit,
                "anomalies_only": anomalies_only
            }
        )
        
    except Exception as e:
        logger.error(f"Error getting sensor history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats")
async def get_sensor_stats():
    """Get sensor statistics and summary data."""
    try:
        if not sensor_readings:
            return {
                "total_readings": 0,
                "sensor_types": [],
                "anomaly_rate": 0.0,
                "active_sensors": [],
                "time_range": None
            }
        
        # Calculate statistics
        total_readings = len(sensor_readings)
        anomalous_readings = len([r for r in sensor_readings if r.get("anomaly", False)])
        anomaly_rate = (anomalous_readings / total_readings) * 100 if total_readings > 0 else 0.0
        
        # Get unique sensor types and IDs
        sensor_types = list(set(r.get("sensor_type") for r in sensor_readings if r.get("sensor_type")))
        active_sensors = list(set(r.get("sensor_id") for r in sensor_readings if r.get("sensor_id")))
        
        # Get time range
        timestamps = [r.get("timestamp") for r in sensor_readings if r.get("timestamp")]
        time_range = None
        if timestamps:
            time_range = {
                "earliest": min(timestamps).isoformat(),
                "latest": max(timestamps).isoformat()
            }
        
        # Get readings per sensor type
        readings_by_type = {}
        for sensor_type in sensor_types:
            type_readings = [r for r in sensor_readings if r.get("sensor_type") == sensor_type]
            readings_by_type[sensor_type] = {
                "count": len(type_readings),
                "anomalies": len([r for r in type_readings if r.get("anomaly", False)]),
                "latest_value": max(type_readings, key=lambda x: x.get("timestamp", datetime.min)).get("value") if type_readings else None
            }
        
        return {
            "total_readings": total_readings,
            "anomalous_readings": anomalous_readings,
            "anomaly_rate": round(anomaly_rate, 2),
            "sensor_types": sensor_types,
            "active_sensors": active_sensors,
            "readings_by_type": readings_by_type,
            "time_range": time_range,
            "last_reading_time": max(timestamps).isoformat() if timestamps else None
        }
        
    except Exception as e:
        logger.error(f"Error getting sensor stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Function to add new sensor reading (called by MQTT handler)
async def add_sensor_reading(topic: str, payload: dict):
    """Add a new sensor reading from MQTT message."""
    try:
        # Generate unique ID
        reading_id = len(sensor_readings) + 1
        
        # Parse timestamp
        timestamp_str = payload.get("ts", datetime.utcnow().isoformat())
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except ValueError:
            timestamp = datetime.utcnow()
        
        # Create reading record
        reading = {
            "id": reading_id,
            "timestamp": timestamp,
            "sensor_type": payload.get("type", "unknown"),
            "sensor_id": payload.get("sensor_id", "unknown"),
            "value": payload.get("value", 0.0),
            "unit": payload.get("unit", ""),
            "origin": payload.get("origin", "unknown"),
            "anomaly": payload.get("anomaly", False),
            "anomaly_details": payload.get("anomaly_details"),
            "protocol": payload.get("protocol"),
            "created_at": datetime.utcnow(),
            "mqtt_topic": topic
        }
        
        # Add to storage
        sensor_readings.append(reading)
        
        # Keep only recent readings (last 10000) to prevent memory issues
        if len(sensor_readings) > 10000:
            sensor_readings[:] = sensor_readings[-5000:]  # Keep last 5000 readings
        
        logger.info(f"Added sensor reading: {reading['sensor_type']} = {reading['value']} {reading['unit']} (anomaly: {reading['anomaly']})")
        
    except Exception as e:
        logger.error(f"Error adding sensor reading: {e}")

# Function to get local sensor data for weather comparison
def get_local_sensor_data() -> dict:
    """Get latest local sensor data for weather comparison."""
    try:
        latest_temp = get_latest_reading_by_type("temperature")
        latest_humidity = get_latest_reading_by_type("humidity")
        
        return {
            "temperature": latest_temp.get("value") if latest_temp else None,
            "humidity": latest_humidity.get("value") if latest_humidity else None,
            "timestamp": max(
                latest_temp.get("timestamp", datetime.min) if latest_temp else datetime.min,
                latest_humidity.get("timestamp", datetime.min) if latest_humidity else datetime.min
            ).isoformat() if (latest_temp or latest_humidity) else None
        }
    except Exception as e:
        logger.error(f"Error getting local sensor data: {e}")
        return {}