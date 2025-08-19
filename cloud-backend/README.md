# Cloud Backend - FastAPI IoT API

This directory contains the cloud layer backend built with FastAPI, providing REST API endpoints, real-time WebSocket communication, and data persistence.

## Components

### Application Structure
```
app/
├── main.py                 # FastAPI application entry point
├── api/v1/
│   ├── auth.py            # Authentication endpoints
│   └── sensors.py         # Sensor data endpoints
├── services/
│   ├── mqtt_client.py     # MQTT subscriber service
│   └── openweather.py     # OpenWeather API integration
└── models/
    └── schemas.py         # Pydantic models and database schemas
```

### Key Features
- **REST API**: Comprehensive sensor data API
- **WebSocket**: Real-time data streaming
- **MQTT Integration**: Automatic sensor data ingestion
- **Authentication**: JWT-based security
- **Database**: SQLite with optional MySQL support
- **External APIs**: OpenWeather integration
- **Documentation**: Auto-generated API docs

## API Endpoints

### Authentication
- `POST /v1/auth/login` - User login
- `GET /v1/auth/me` - Get current user info
- `POST /v1/auth/refresh` - Refresh JWT token

### Sensor Data
- `GET /v1/sensors/latest` - Latest sensor readings
- `GET /v1/sensors/history` - Historical sensor data
- `GET /v1/sensors/anomalies` - Anomalous readings
- `GET /v1/sensors/stats` - System statistics
- `GET /v1/sensors/live` - Live MQTT cache data

### External Integration
- `GET /v1/sensors/external/weather` - OpenWeather data
- `GET /v1/sensors/compare/weather` - Compare sensors with weather

### System
- `GET /health` - Health check
- `GET /api/status` - API status
- `WebSocket /ws` - Real-time updates

## Configuration

### Environment Variables
```bash
# Backend
PORT=8000
JWT_SECRET=your-secret-key
DEMO_USER=admin
DEMO_PASS=admin123

# Database
DB_URL=sqlite:///data/app.db
# DB_URL=mysql+pymysql://user:pass@mysql:3306/iot

# MQTT
MQTT_HOST=mosquitto
MQTT_PORT=1883

# OpenWeather
OPENWEATHER_API_KEY=your-api-key
DEFAULT_CITY=London

# CORS
CORS_ORIGINS=*
```

### Database Setup
The application automatically creates SQLite tables on startup:
```sql
-- Sensor readings table
CREATE TABLE sensor_readings (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME,
    sensor_type VARCHAR(50),
    sensor_id VARCHAR(100), 
    value FLOAT,
    unit VARCHAR(20),
    origin VARCHAR(20),
    source_protocol VARCHAR(20),
    anomaly BOOLEAN,
    raw_data TEXT
);

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    hashed_password VARCHAR(255),
    is_active BOOLEAN,
    created_at DATETIME
);
```

## Running the Backend

### Development
```bash
cd cloud-backend

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export MQTT_HOST=localhost
export JWT_SECRET=your-secret-key

# Run with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Production
```bash
# Build Docker image
docker build -t iot-backend .

# Run container
docker run -p 8000:8000 \
  -e MQTT_HOST=mosquitto \
  -e JWT_SECRET=production-secret \
  iot-backend
```

### With Docker Compose
```bash
# Start all services
docker-compose up --build
```

## API Usage

### Authentication
```bash
# Login
curl -X POST "http://localhost:8000/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer", 
  "expires_in": 86400
}

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/v1/sensors/latest"
```

### Get Latest Sensor Data
```bash
curl "http://localhost:8000/v1/sensors/latest"

# Response
{
  "sensors": {
    "temperature": [
      {
        "id": 1,
        "timestamp": "2024-01-01T12:00:00Z",
        "sensor_type": "temperature",
        "sensor_id": "temp-001",
        "value": 23.5,
        "unit": "°C",
        "origin": "edge",
        "source_protocol": "mqtt",
        "anomaly": false
      }
    ]
  },
  "total_count": 1,
  "last_updated": "2024-01-01T12:00:00Z"
}
```

### Get Sensor History
```bash
curl "http://localhost:8000/v1/sensors/history?sensor_id=temp-001&limit=50&hours=24"

# Response
{
  "readings": [...],
  "sensor_id": "temp-001",
  "count": 50
}
```

### Get Weather Comparison
```bash
curl "http://localhost:8000/v1/sensors/compare/weather?city=London"

# Response
{
  "weather_data": {
    "city": "London",
    "temperature": 18.2,
    "humidity": 72.0,
    "pressure": 1015.3,
    "description": "scattered clouds",
    "timestamp": "2024-01-01T12:00:00Z"
  },
  "sensor_data": {
    "temperature": {
      "value": 23.5,
      "timestamp": "2024-01-01T11:58:00Z",
      "sensor_id": "temp-001"
    }
  },
  "comparison": {
    "differences": {
      "temperature": 5.3
    },
    "alerts": [
      {
        "type": "temperature_discrepancy",
        "message": "Large temperature difference: sensor 23.5°C vs weather 18.2°C",
        "severity": "warning"
      }
    ]
  }
}
```

## WebSocket Integration

### Connect to WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    console.log('Connected to IoT WebSocket');
    
    // Send ping to keep connection alive
    ws.send(JSON.stringify({type: 'ping'}));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'sensor_data':
            updateSensorDisplay(message.data);
            break;
        case 'alert':
            showAlert(message.data);
            break;
        case 'pong':
            console.log('Pong received');
            break;
    }
};
```

### Message Types
```javascript
// Sensor data update
{
  "type": "sensor_data",
  "data": {
    "timestamp": "2024-01-01T12:00:00Z",
    "sensor_type": "temperature",
    "sensor_id": "temp-001", 
    "value": 24.2,
    "unit": "°C",
    "origin": "edge",
    "anomaly": false
  },
  "timestamp": "2024-01-01T12:00:00Z"
}

// Anomaly alert
{
  "type": "alert",
  "data": {
    "sensor_id": "temp-001",
    "sensor_type": "temperature",
    "value": 45.8,
    "message": "Temperature reading exceeds normal range",
    "severity": "warning"
  },
  "timestamp": "2024-01-01T12:05:00Z"
}
```

## Services

### MQTT Client Service
Automatically subscribes to sensor topics and processes incoming data:

```python
# Topics subscribed to:
sensors/+/+          # All sensor data
nodered/status       # Node-RED status
system/+             # System messages

# Processes and stores data in database
# Forwards real-time updates to WebSocket clients
```

### OpenWeather Service
Integrates with OpenWeather API for external weather data:

```python
# Features:
- Fetches current weather data
- Compares with local sensor readings
- Generates alerts for large discrepancies
- Falls back to mock data if API unavailable
```

## Database Models

### SensorReading
```python
class SensorReading(Base):
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, index=True)
    sensor_type = Column(String(50), index=True)
    sensor_id = Column(String(100), index=True)
    value = Column(Float)
    unit = Column(String(20))
    origin = Column(String(20))
    source_protocol = Column(String(20))
    anomaly = Column(Boolean, index=True)
    raw_data = Column(Text)
```

### User
```python
class User(Base):
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    hashed_password = Column(String(255))
    is_active = Column(Boolean)
    created_at = Column(DateTime)
```

## Security

### JWT Authentication
- HS256 algorithm
- 24-hour token expiration
- Automatic token refresh
- Secure password hashing with bcrypt

### API Security
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention
- Rate limiting headers
- Security headers (XSS, CSRF protection)

### Environment Security
- Secrets via environment variables
- Database connection encryption
- TLS support for production

## Testing

### Run Tests
```bash
cd tests
python -m pytest test_backend.py -v
```

### Test Coverage
- Authentication endpoints
- Sensor data endpoints
- Error handling
- Data validation
- Performance testing

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs

# Interactive API testing
open http://localhost:8000/redoc
```

## Monitoring

### Health Endpoints
```bash
# Basic health check
GET /health
{
  "status": "healthy",
  "services": {
    "mqtt": "connected",
    "database": "available",
    "weather": "available"
  }
}

# Detailed API status
GET /api/status
{
  "api_version": "1.0.0",
  "mqtt_connected": true,
  "active_websockets": 3,
  "latest_readings_count": 15,
  "uptime": "System running"
}
```

### Logging
```python
# Structured logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Log levels:
# - INFO: Normal operations
# - WARNING: Potential issues
# - ERROR: Operation failures
# - DEBUG: Detailed debugging info
```

## Deployment

### Docker Build
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ ./app/
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Considerations
- Use PostgreSQL instead of SQLite
- Configure reverse proxy (nginx)
- Set up SSL/TLS certificates
- Enable proper logging
- Configure monitoring and alerting
- Set strong JWT secrets
- Enable database backups

### Environment-Specific Configs
```bash
# Development
DB_URL=sqlite:///data/app.db
CORS_ORIGINS=*

# Production  
DB_URL=postgresql://user:pass@db:5432/iot
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET=strong-production-secret
```

## Troubleshooting

### Common Issues
1. **MQTT Connection Failed**:
   - Check MQTT_HOST environment variable
   - Verify Mosquitto container is running
   - Check network connectivity

2. **Database Errors**:
   - Ensure data directory exists and is writable
   - Check database URL format
   - Verify database permissions

3. **WebSocket Connection Issues**:
   - Check firewall settings
   - Verify WebSocket URL
   - Monitor browser console for errors

4. **Authentication Problems**:
   - Check JWT_SECRET is set
   - Verify token expiration
   - Ensure demo user exists

### Debug Mode
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with detailed output
uvicorn app.main:app --log-level debug --reload
```