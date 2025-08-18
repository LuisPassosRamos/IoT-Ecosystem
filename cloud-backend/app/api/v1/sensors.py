"""
Sensors API endpoints
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from models.schemas import (
    get_db, SensorReading, SensorReadingResponse, 
    SensorLatestResponse, SensorHistoryResponse, WeatherResponse
)
from services.mqtt_client import get_mqtt_service
from services.openweather import get_openweather_service
from api.v1.auth import verify_token

router = APIRouter(prefix="/v1/sensors", tags=["sensors"])

@router.get("/latest", response_model=SensorLatestResponse)
async def get_latest_sensors(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get latest sensor readings grouped by sensor type"""
    
    # Get latest reading for each sensor
    subquery = db.query(
        SensorReading.sensor_id,
        SensorReading.sensor_type,
        db.func.max(SensorReading.timestamp).label('max_timestamp')
    ).group_by(
        SensorReading.sensor_id,
        SensorReading.sensor_type
    ).subquery()
    
    # Get full records for latest readings
    latest_readings = db.query(SensorReading).join(
        subquery,
        and_(
            SensorReading.sensor_id == subquery.c.sensor_id,
            SensorReading.timestamp == subquery.c.max_timestamp
        )
    ).order_by(desc(SensorReading.timestamp)).limit(limit).all()
    
    # Group by sensor type
    sensors_by_type: Dict[str, List[SensorReadingResponse]] = {}
    last_updated = None
    
    for reading in latest_readings:
        sensor_type = reading.sensor_type
        if sensor_type not in sensors_by_type:
            sensors_by_type[sensor_type] = []
        
        sensors_by_type[sensor_type].append(SensorReadingResponse.from_orm(reading))
        
        if last_updated is None or reading.timestamp > last_updated:
            last_updated = reading.timestamp
    
    return SensorLatestResponse(
        sensors=sensors_by_type,
        total_count=len(latest_readings),
        last_updated=last_updated
    )

@router.get("/history", response_model=SensorHistoryResponse)
async def get_sensor_history(
    sensor_id: str = Query(..., description="Sensor ID to get history for"),
    limit: int = Query(default=100, ge=1, le=1000),
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history to retrieve"),
    db: Session = Depends(get_db)
):
    """Get historical sensor readings for a specific sensor"""
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Query historical data
    readings = db.query(SensorReading).filter(
        and_(
            SensorReading.sensor_id == sensor_id,
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp <= end_time
        )
    ).order_by(desc(SensorReading.timestamp)).limit(limit).all()
    
    if not readings:
        raise HTTPException(
            status_code=404,
            detail=f"No readings found for sensor {sensor_id}"
        )
    
    return SensorHistoryResponse(
        readings=[SensorReadingResponse.from_orm(reading) for reading in readings],
        sensor_id=sensor_id,
        count=len(readings)
    )

@router.get("/anomalies")
async def get_anomalies(
    hours: int = Query(default=24, ge=1, le=168),
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Get recent anomalous sensor readings"""
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Query anomalous readings
    anomalies = db.query(SensorReading).filter(
        and_(
            SensorReading.anomaly == True,
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp <= end_time
        )
    ).order_by(desc(SensorReading.timestamp)).limit(limit).all()
    
    return {
        "anomalies": [SensorReadingResponse.from_orm(reading) for reading in anomalies],
        "count": len(anomalies),
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours
        }
    }

@router.get("/stats")
async def get_sensor_stats(
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """Get sensor statistics for the specified time period"""
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    # Count total readings
    total_readings = db.query(SensorReading).filter(
        and_(
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp <= end_time
        )
    ).count()
    
    # Count anomalies
    anomaly_count = db.query(SensorReading).filter(
        and_(
            SensorReading.anomaly == True,
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp <= end_time
        )
    ).count()
    
    # Count by sensor type
    type_stats = db.query(
        SensorReading.sensor_type,
        db.func.count(SensorReading.id).label('count'),
        db.func.count(db.case([(SensorReading.anomaly == True, 1)])).label('anomalies')
    ).filter(
        and_(
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp <= end_time
        )
    ).group_by(SensorReading.sensor_type).all()
    
    # Count by origin
    origin_stats = db.query(
        SensorReading.origin,
        db.func.count(SensorReading.id).label('count')
    ).filter(
        and_(
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp <= end_time
        )
    ).group_by(SensorReading.origin).all()
    
    # Count by protocol
    protocol_stats = db.query(
        SensorReading.source_protocol,
        db.func.count(SensorReading.id).label('count')
    ).filter(
        and_(
            SensorReading.timestamp >= start_time,
            SensorReading.timestamp <= end_time
        )
    ).group_by(SensorReading.source_protocol).all()
    
    return {
        "time_range": {
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "hours": hours
        },
        "total_readings": total_readings,
        "anomaly_count": anomaly_count,
        "anomaly_rate": round((anomaly_count / total_readings * 100) if total_readings > 0 else 0, 2),
        "by_sensor_type": [
            {
                "type": stat.sensor_type,
                "count": stat.count,
                "anomalies": stat.anomalies
            }
            for stat in type_stats
        ],
        "by_origin": [
            {
                "origin": stat.origin,
                "count": stat.count
            }
            for stat in origin_stats
        ],
        "by_protocol": [
            {
                "protocol": stat.source_protocol,
                "count": stat.count
            }
            for stat in protocol_stats
        ]
    }

@router.get("/live")
async def get_live_readings():
    """Get latest readings from MQTT cache"""
    try:
        mqtt_service = get_mqtt_service()
        latest_readings = mqtt_service.get_latest_readings()
        
        return {
            "live_readings": latest_readings,
            "count": len(latest_readings),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"MQTT service unavailable: {str(e)}"
        )

@router.get("/external/weather", response_model=WeatherResponse)
async def get_external_weather(
    city: str = Query(default=None, description="City name for weather data")
):
    """Get external weather data from OpenWeatherMap"""
    try:
        weather_service = get_openweather_service()
        weather_data = await weather_service.get_weather(city)
        
        if not weather_data:
            raise HTTPException(
                status_code=404,
                detail=f"Weather data not found for city: {city}"
            )
        
        return weather_data
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Weather service unavailable: {str(e)}"
        )

@router.get("/compare/weather")
async def compare_with_weather(
    city: str = Query(default=None, description="City name for weather comparison"),
    db: Session = Depends(get_db)
):
    """Compare local sensor data with external weather data"""
    try:
        # Get weather data
        weather_service = get_openweather_service()
        weather_data = await weather_service.get_weather(city)
        
        if not weather_data:
            raise HTTPException(
                status_code=404,
                detail=f"Weather data not found for city: {city}"
            )
        
        # Get latest sensor readings
        latest_temp = db.query(SensorReading).filter(
            SensorReading.sensor_type == "temperature"
        ).order_by(desc(SensorReading.timestamp)).first()
        
        latest_humidity = db.query(SensorReading).filter(
            SensorReading.sensor_type == "humidity"
        ).order_by(desc(SensorReading.timestamp)).first()
        
        # Prepare sensor data for comparison
        sensor_data = {}
        if latest_temp:
            sensor_data["temperature"] = latest_temp.value
        if latest_humidity:
            sensor_data["humidity"] = latest_humidity.value
        
        # Compare data
        comparison = weather_service.compare_with_sensor(weather_data, sensor_data)
        
        return {
            "weather_data": weather_data,
            "sensor_data": {
                "temperature": {
                    "value": latest_temp.value if latest_temp else None,
                    "timestamp": latest_temp.timestamp.isoformat() if latest_temp else None,
                    "sensor_id": latest_temp.sensor_id if latest_temp else None
                },
                "humidity": {
                    "value": latest_humidity.value if latest_humidity else None,
                    "timestamp": latest_humidity.timestamp.isoformat() if latest_humidity else None,
                    "sensor_id": latest_humidity.sensor_id if latest_humidity else None
                }
            },
            "comparison": comparison,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Comparison service unavailable: {str(e)}"
        )