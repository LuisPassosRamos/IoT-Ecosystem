# IoT-Ecosystem Architecture

## Overview

The IoT-Ecosystem implements a three-tier architecture for environmental monitoring:
- **Edge Layer**: Sensor simulators and data collection
- **Fog Layer**: Protocol bridging and edge intelligence
- **Cloud Layer**: Data processing, storage, and visualization

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   FastAPI   │  │  Frontend   │  │ OpenWeather │            │
│  │   Backend   │  │ Dashboard   │  │     API     │            │
│  │             │  │             │  │             │            │
│  │ • REST API  │  │ • Chart.js  │  │ • Weather   │            │
│  │ • WebSocket │  │ • Real-time │  │   Data      │            │
│  │ • SQLite    │  │ • Anomaly   │  │ • Compare   │            │
│  │ • JWT Auth  │  │   Alerts    │  │   Local     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                │                 │                   │
│         └────────────────┼─────────────────┘                   │
│                          │                                     │
└──────────────────────────┼─────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │                               │
┌─────────────────────────────────────────────────────────────────┐
│                        FOG LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Node-RED   │  │    MQTT     │  │  Optional   │            │
│  │    Flows    │  │   Broker    │  │  Gateway    │            │
│  │             │  │             │  │             │            │
│  │ • CoAP→MQTT │  │ • Eclipse   │  │ • Express   │            │
│  │ • Normalize │  │   Mosquitto │  │ • REST API  │            │
│  │ • Anomaly   │  │ • Pub/Sub   │  │ • Caching   │            │
│  │   Detection │  │ • WebSocket │  │ • Filtering │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│         │                │                                     │
│         └────────────────┼─────────────────────────────────────│
│                          │                                     │
└──────────────────────────┼─────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
┌─────────────────────────────────────────────────────────────────┐
│                        EDGE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Temperature │  │  Humidity   │  │ Luminosity  │            │
│  │   Sensor    │  │   Sensor    │  │   Sensor    │            │
│  │             │  │             │  │             │            │
│  │ • MQTT Pub  │  │ • MQTT Pub  │  │ • MQTT Pub  │            │
│  │ • Anomaly   │  │ • Anomaly   │  │ • Anomaly   │            │
│  │   Detection │  │   Detection │  │   Detection │            │
│  │ • Simulate  │  │ • Simulate  │  │ • Simulate  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                │
│  ┌─────────────┐                                              │
│  │    CoAP     │                                              │
│  │  Simulator  │                                              │
│  │             │                                              │
│  │ • aiocoap   │                                              │
│  │ • REST API  │                                              │
│  │ • Status    │                                              │
│  │   Endpoint  │                                              │
│  └─────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Edge Layer

**Purpose**: Data collection and initial processing at the source

**Components**:
- **MQTT Sensors**: Temperature, humidity, luminosity simulators
- **CoAP Simulator**: Alternative protocol sensor simulation
- **Anomaly Detection**: Real-time threshold and jump detection

**Technologies**:
- Python 3 with paho-mqtt
- aiocoap for CoAP simulation
- Configurable thresholds via environment variables

**Data Flow**:
1. Sensors generate readings every 2-4 seconds
2. Anomaly detection applied immediately
3. Data published to MQTT topics with QoS 1
4. CoAP server provides REST-like endpoints

### Fog Layer

**Purpose**: Protocol bridging and edge intelligence

**Components**:
- **Node-RED Flows**: Visual programming for data bridging
- **MQTT Broker**: Eclipse Mosquitto for reliable messaging
- **Protocol Bridge**: CoAP to MQTT translation
- **Edge Analytics**: Basic anomaly detection and filtering

**Technologies**:
- Node-RED for visual flow programming
- Eclipse Mosquitto MQTT broker
- Optional Node.js/Express gateway

**Data Flow**:
1. Node-RED polls CoAP sensors every 5-7 seconds
2. Data normalized to standard JSON format
3. Additional anomaly detection applied
4. Results published to MQTT broker
5. Status monitoring and error handling

### Cloud Layer

**Purpose**: Data aggregation, processing, storage, and visualization

**Components**:
- **Backend API**: FastAPI with REST and WebSocket endpoints
- **Frontend Dashboard**: Real-time visualization with Chart.js
- **External Integration**: OpenWeatherMap API for comparison
- **Authentication**: JWT-based security

**Technologies**:
- FastAPI with Pydantic for API validation
- SQLite for data persistence
- WebSocket for real-time updates
- Chart.js for data visualization
- NGINX for frontend serving

**Data Flow**:
1. MQTT client subscribes to all sensor topics
2. Incoming data stored in SQLite database
3. Real-time updates sent to WebSocket clients
4. REST API provides historical data access
5. External weather data compared with local sensors

## Communication Protocols

### MQTT (Primary)
- **Broker**: Eclipse Mosquitto
- **Topics**: `sensors/{type}/{id}` pattern
- **QoS**: Level 1 for reliable delivery
- **Retain**: False for live data, True for status
- **WebSocket**: Port 9001 for browser clients

### CoAP (Alternative)
- **Server**: aiocoap-based simulation
- **Endpoints**: `/temperature`, `/humidity`, `/status`
- **Method**: GET for all endpoints
- **Format**: JSON responses
- **Polling**: Node-RED polls every 5-7 seconds

### HTTP REST (Management)
- **Backend API**: FastAPI with automatic OpenAPI docs
- **Authentication**: JWT Bearer tokens
- **Endpoints**: CRUD operations for sensor data
- **Status**: Health checks and system status
- **External**: OpenWeatherMap integration

### WebSocket (Real-time)
- **Endpoint**: `/ws` on backend
- **Purpose**: Real-time dashboard updates
- **Protocol**: JSON message format
- **Features**: Heartbeat, reconnection, message types

## Data Models

### Sensor Reading
```json
{
  "ts": "2024-01-01T12:00:00Z",
  "type": "temperature",
  "value": 25.3,
  "unit": "celsius",
  "sensor_id": "temp_sim_001",
  "origin": "edge",
  "anomaly": false,
  "anomaly_details": {
    "out_of_range": false,
    "sudden_jump": false,
    "previous_value": 24.8
  }
}
```

### System Status
```json
{
  "mqtt_connected": true,
  "database_connected": true,
  "total_readings": 15420,
  "active_sensors": ["temp_sim_001", "humidity_sim_001"],
  "uptime_seconds": 3600,
  "last_reading_time": "2024-01-01T12:00:00Z"
}
```

## Scalability Considerations

### Horizontal Scaling
- **Multiple Sensors**: Easy to add new sensor types or instances
- **Load Balancing**: MQTT broker clustering for high availability
- **Database**: Can upgrade from SQLite to PostgreSQL/MySQL
- **API Instances**: FastAPI supports multiple worker processes

### Vertical Scaling
- **Memory**: In-memory data limited to last 10,000 readings
- **CPU**: Asynchronous processing for concurrent connections
- **Storage**: SQLite suitable for millions of readings
- **Network**: MQTT QoS 1 ensures reliable delivery

### Cloud Deployment
- **Containerization**: Full Docker support with docker-compose
- **Orchestration**: Kubernetes-ready container definitions
- **Monitoring**: Comprehensive logging and health checks
- **Security**: JWT authentication and HTTPS-ready

## Security Architecture

### Authentication & Authorization
- **JWT Tokens**: HS256 signed tokens with configurable expiration
- **Demo Credentials**: Configurable via environment variables
- **API Protection**: Bearer token required for sensitive endpoints
- **WebSocket Auth**: Token validation for real-time connections

### Network Security
- **MQTT**: Support for TLS/SSL encryption (configurable)
- **HTTP**: HTTPS support with reverse proxy
- **WebSocket**: Secure WebSocket (WSS) support
- **Internal**: Container-to-container communication

### Data Privacy
- **LGPD Compliance**: Data minimization and retention policies
- **Anonymization**: Sensor IDs don't contain personal information
- **Encryption**: Data in transit and at rest protection
- **Access Control**: Role-based access (extensible)

## Monitoring & Observability

### Logging
- **Structured Logs**: JSON format with timestamps
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Centralized**: Container logs accessible via Docker
- **Rotation**: Automatic log rotation and cleanup

### Metrics
- **System Health**: CPU, memory, disk usage
- **Application**: Request counts, response times
- **Business**: Sensor readings, anomalies, errors
- **Real-time**: WebSocket connection counts

### Alerting
- **Anomaly Detection**: Multiple threshold types
- **System Alerts**: Service failures and disconnections
- **Weather Comparison**: Significant discrepancies
- **Visual Indicators**: Dashboard status lights

## Deployment Architecture

### Development
- **Docker Compose**: Local multi-container deployment
- **Hot Reload**: Development mode with auto-restart
- **Debug Access**: Direct container and log access
- **Port Mapping**: Services accessible on localhost

### Production
- **Container Registry**: Docker images for all services
- **Orchestration**: Kubernetes or Docker Swarm
- **Load Balancing**: NGINX or cloud load balancers
- **SSL Termination**: HTTPS with Let's Encrypt
- **Database**: Managed database services
- **Monitoring**: Prometheus, Grafana, or cloud monitoring

### Backup & Recovery
- **Database**: Regular SQLite backups or replication
- **Configuration**: Version-controlled environment files
- **Logs**: Long-term log storage and analysis
- **Disaster Recovery**: Multi-region deployment capability