from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class SensorReading(BaseModel):
    """Sensor reading data model."""
    ts: str = Field(..., description="ISO 8601 timestamp")
    type: str = Field(..., description="Sensor type (temperature, humidity, luminosity)")
    value: float = Field(..., description="Sensor value")
    unit: str = Field(..., description="Unit of measurement")
    sensor_id: str = Field(..., description="Unique sensor identifier")
    origin: str = Field(..., description="Data origin (edge, fog, coap)")
    anomaly: bool = Field(default=False, description="Whether reading is anomalous")
    anomaly_details: Optional[Dict[str, Any]] = Field(default=None, description="Anomaly details")
    protocol: Optional[str] = Field(default=None, description="Protocol used")
    reading_count: Optional[int] = Field(default=None, description="Reading sequence number")

class SensorReadingResponse(BaseModel):
    """Response model for sensor readings."""
    id: int
    timestamp: datetime
    sensor_type: str
    sensor_id: str
    value: float
    unit: str
    origin: str
    anomaly: bool
    anomaly_details: Optional[Dict[str, Any]] = None
    created_at: datetime

class LatestReadingsResponse(BaseModel):
    """Response model for latest readings."""
    temperature: Optional[SensorReadingResponse] = None
    humidity: Optional[SensorReadingResponse] = None
    luminosity: Optional[SensorReadingResponse] = None
    total_readings: int

class HistoryQueryParams(BaseModel):
    """Query parameters for history endpoint."""
    sensor_id: Optional[str] = Field(default=None, description="Filter by sensor ID")
    sensor_type: Optional[str] = Field(default=None, description="Filter by sensor type")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of readings")
    anomalies_only: bool = Field(default=False, description="Return only anomalous readings")

class HistoryResponse(BaseModel):
    """Response model for sensor history."""
    readings: List[SensorReadingResponse]
    total_count: int
    filters_applied: Dict[str, Any]

class LoginRequest(BaseModel):
    """Login request model."""
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    """Login response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: str

class WeatherResponse(BaseModel):
    """OpenWeatherMap API response model."""
    city: str
    country: str
    temperature: float
    humidity: float
    description: str
    timestamp: str
    comparison: Optional[Dict[str, Any]] = Field(default=None, description="Comparison with local sensors")

class WSMessage(BaseModel):
    """WebSocket message model."""
    type: str = Field(..., description="Message type (sensor_data, system_status, etc.)")
    data: Dict[str, Any] = Field(..., description="Message payload")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class SystemStatus(BaseModel):
    """System status model."""
    mqtt_connected: bool
    database_connected: bool
    total_readings: int
    active_sensors: List[str]
    uptime_seconds: int
    last_reading_time: Optional[str] = None

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())