# Cloud Backend

FastAPI-based cloud backend for IoT sensor data processing, storage, and real-time streaming.

## Features

### API Endpoints
- **REST API**: Complete CRUD operations for sensor data
- **WebSocket**: Real-time data streaming to frontend clients
- **Authentication**: JWT-based security with configurable expiration
- **External Integration**: OpenWeatherMap API for weather comparison
- **Health Monitoring**: System status and health check endpoints

### Data Processing
- **MQTT Integration**: Subscribe to all sensor topics with automatic reconnection
- **Data Validation**: Pydantic models for strict input validation
- **Anomaly Detection**: Server-side anomaly analysis and alerting
- **Data Aggregation**: Statistical analysis and historical data processing

### Storage & Persistence
- **SQLite**: Local database for development and small deployments
- **MySQL Support**: Optional configuration for production deployments
- **Data Retention**: Automatic cleanup of old sensor readings
- **Backup**: Regular database backup and recovery procedures

## Architecture

### Application Structure
```
cloud-backend/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/v1/
│   │   ├── sensors.py          # Sensor data endpoints
│   │   └── auth.py             # Authentication endpoints
│   ├── services/
│   │   ├── mqtt_client.py      # MQTT client service
│   │   └── openweather.py      # OpenWeatherMap integration
│   └── models/
│       └── schemas.py          # Pydantic data models
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build configuration
└── README.md                   # This file
```

### Technology Stack
- **FastAPI**: Modern Python web framework with automatic OpenAPI docs
- **Pydantic**: Data validation using Python type annotations
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **paho-mqtt**: MQTT client library for IoT communication
- **python-jose**: JWT token creation and validation
- **uvicorn**: ASGI server for production deployment

## API Documentation

### Sensor Data Endpoints

#### Get Latest Readings
```http
GET /v1/sensors/latest
```
Returns the most recent reading from each sensor type.

**Response:**
```json
{
  "temperature": {
    "id": 1543,
    "timestamp": "2024-01-01T12:00:00Z",
    "sensor_type": "temperature",
    "sensor_id": "temp_sim_001",
    "value": 25.3,
    "unit": "celsius",
    "origin": "edge",
    "anomaly": false,
    "created_at": "2024-01-01T12:00:01Z"
  },
  "humidity": { /* ... */ },
  "luminosity": { /* ... */ },
  "total_readings": 2048
}
```

#### Get Sensor History
```http
GET /v1/sensors/history?sensor_type=temperature&limit=100&anomalies_only=false
```

**Query Parameters:**
- `sensor_id` (optional): Filter by specific sensor ID
- `sensor_type` (optional): Filter by sensor type (temperature, humidity, luminosity)
- `limit` (default: 100): Maximum number of readings to return
- `anomalies_only` (default: false): Return only anomalous readings

**Response:**
```json
{
  "readings": [
    {
      "id": 1543,
      "timestamp": "2024-01-01T12:00:00Z",
      "sensor_type": "temperature",
      "sensor_id": "temp_sim_001",
      "value": 25.3,
      "unit": "celsius",
      "origin": "edge",
      "anomaly": false,
      "anomaly_details": null,
      "created_at": "2024-01-01T12:00:01Z"
    }
  ],
  "total_count": 1,
  "filters_applied": {
    "sensor_type": "temperature",
    "limit": 100,
    "anomalies_only": false
  }
}
```

#### Get Sensor Statistics
```http
GET /v1/sensors/stats
```

**Response:**
```json
{
  "total_readings": 2048,
  "anomalous_readings": 23,
  "anomaly_rate": 1.12,
  "sensor_types": ["temperature", "humidity", "luminosity"],
  "active_sensors": ["temp_sim_001", "humidity_sim_001", "luminosity_sim_001"],
  "readings_by_type": {
    "temperature": {
      "count": 680,
      "anomalies": 8,
      "latest_value": 25.3
    }
  },
  "time_range": {
    "earliest": "2024-01-01T00:00:00Z",
    "latest": "2024-01-01T12:00:00Z"
  }
}
```

### Authentication Endpoints

#### Login
```http
POST /v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": "admin"
}
```

#### Verify Token
```http
GET /v1/auth/verify
Authorization: Bearer <jwt_token>
```

**Response:**
```json
{
  "authenticated": true,
  "user": "admin",
  "token_type": "access_token",
  "expires": 1640995200,
  "issued_at": 1640908800
}
```

### External Integration

#### Weather Comparison
```http
GET /v1/external/weather?city=London
```

**Response:**
```json
{
  "city": "London",
  "country": "GB",
  "temperature": 18.5,
  "humidity": 72.0,
  "description": "light rain",
  "timestamp": "2024-01-01T12:00:00Z",
  "comparison": {
    "weather_api": {
      "temperature": 18.5,
      "humidity": 72.0
    },
    "local_sensors": {
      "temperature": 25.3,
      "humidity": 65.2
    },
    "differences": {
      "temperature": {
        "absolute_difference": 6.8,
        "percentage_difference": 36.8
      }
    },
    "alerts": [
      {
        "type": "temperature_discrepancy",
        "message": "Local temperature differs from weather API by 6.8°C (threshold: 5.0°C)",
        "severity": "high"
      }
    ],
    "has_alerts": true
  }
}
```

### System Endpoints

#### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "mqtt_connected": true,
  "active_websockets": 3,
  "total_readings": 2048
}
```

#### System Status
```http
GET /v1/system/status
```

**Response:**
```json
{
  "mqtt_connected": true,
  "database_connected": true,
  "total_readings": 2048,
  "active_sensors": ["temp_sim_001", "humidity_sim_001"],
  "uptime_seconds": 3600,
  "last_reading_time": "2024-01-01T12:00:00Z"
}
```

## WebSocket API

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
```

### Message Types

#### Connection Established
```json
{
  "type": "connection_established",
  "data": {
    "message": "Connected to IoT-Ecosystem real-time stream",
    "features": ["sensor_data", "system_status", "anomaly_alerts"]
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Sensor Data Update
```json
{
  "type": "sensor_data",
  "data": {
    "topic": "sensors/temperature/sim001",
    "payload": {
      "ts": "2024-01-01T12:00:00Z",
      "type": "temperature",
      "value": 25.3,
      "anomaly": false
    },
    "sensor_type": "temperature",
    "value": 25.3,
    "anomaly": false
  },
  "timestamp": "2024-01-01T12:00:01Z"
}
```

#### Client Heartbeat
```json
{
  "type": "ping",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Server Response
```json
{
  "type": "pong",
  "data": {
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## MQTT Integration

### Configuration
```python
# MQTT settings
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_USERNAME = None  # Optional
MQTT_PASSWORD = None  # Optional

# Subscription topics
TOPICS = [
    "sensors/temperature/+",
    "sensors/humidity/+",
    "sensors/luminosity/+"
]
```

### Message Processing
```python
async def handle_mqtt_message(topic: str, payload: Dict[str, Any]):
    """Process incoming MQTT messages."""
    # Validate payload
    try:
        sensor_reading = SensorReading(**payload)
    except ValidationError as e:
        logger.error(f"Invalid sensor data: {e}")
        return
    
    # Store in database
    await store_sensor_reading(sensor_reading)
    
    # Broadcast to WebSocket clients
    await broadcast_to_websockets(sensor_reading)
    
    # Check for anomalies
    if sensor_reading.anomaly:
        await send_anomaly_alert(sensor_reading)
```

### Auto-reconnection
```python
class MQTTClientService:
    async def connect_with_retry(self, max_attempts=5):
        """Connect to MQTT broker with automatic retry."""
        for attempt in range(max_attempts):
            try:
                await self.client.connect(self.host, self.port)
                logger.info("MQTT connected successfully")
                return True
            except Exception as e:
                logger.warning(f"MQTT connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error("Failed to connect to MQTT broker after all attempts")
        return False
```

## Data Models

### Sensor Reading
```python
class SensorReading(BaseModel):
    ts: str = Field(..., description="ISO 8601 timestamp")
    type: str = Field(..., regex=r'^(temperature|humidity|luminosity)$')
    value: float = Field(..., ge=-50, le=1000)
    unit: str = Field(..., max_length=20)
    sensor_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$', max_length=50)
    origin: str = Field(..., description="Data origin (edge, fog, coap)")
    anomaly: bool = Field(default=False)
    anomaly_details: Optional[Dict[str, Any]] = None
    protocol: Optional[str] = None
    reading_count: Optional[int] = None
```

### Authentication
```python
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: str
```

### System Status
```python
class SystemStatus(BaseModel):
    mqtt_connected: bool
    database_connected: bool
    total_readings: int
    active_sensors: List[str]
    uptime_seconds: int
    last_reading_time: Optional[str] = None
```

## Configuration

### Environment Variables
```bash
# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

# Database Configuration
DATABASE_URL=sqlite:///./sensor_data.db

# JWT Configuration
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Demo User Credentials
DEMO_USERNAME=admin
DEMO_PASSWORD=password123

# OpenWeatherMap API
OPENWEATHER_API_KEY=your-api-key-here

# Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
```

### Database Configuration
```python
# SQLite (development)
DATABASE_URL = "sqlite:///./sensor_data.db"

# MySQL (production)
DATABASE_URL = "mysql+pymysql://user:password@host:3306/iot_ecosystem"

# PostgreSQL (production)
DATABASE_URL = "postgresql://user:password@host:5432/iot_ecosystem"
```

## Deployment

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run with environment variables
export MQTT_HOST=localhost
export JWT_SECRET=dev-secret-key
uvicorn app.main:app --reload
```

### Docker
```bash
# Build image
docker build -t iot-backend .

# Run container
docker run -p 8000:8000 \
  -e MQTT_HOST=mosquitto \
  -e JWT_SECRET=production-secret \
  iot-backend

# Use docker-compose
docker-compose up backend
```

### Production
```bash
# Install production dependencies
pip install -r requirements.txt gunicorn

# Run with Gunicorn
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

## Monitoring

### Logging
```python
import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
```

### Health Checks
```python
@app.get("/health")
async def health_check():
    """Comprehensive health check."""
    checks = {
        "api": True,
        "mqtt": mqtt_client.is_connected(),
        "database": await check_database_connection(),
        "external_apis": await check_external_apis()
    }
    
    status = "healthy" if all(checks.values()) else "degraded"
    
    return {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Metrics
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

sensor_readings_total = Counter('sensor_readings_total', 'Total sensor readings', ['sensor_type'])
request_duration = Histogram('request_duration_seconds', 'Request duration')
active_websockets = Gauge('active_websockets', 'Number of active WebSocket connections')
```

## Security

### Input Validation
```python
# Pydantic validation with custom validators
class SensorReading(BaseModel):
    value: float = Field(..., ge=-50, le=1000)
    sensor_id: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('ts')
    def validate_timestamp(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Invalid timestamp format')
```

### CORS Configuration
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Production: specific origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    # Login logic
    pass
```

This backend provides a robust, scalable foundation for IoT data processing with enterprise-grade features and security.