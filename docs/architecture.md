# IoT Ecosystem Architecture

## Overview

The IoT Ecosystem is a three-tier architecture designed for scalable environmental monitoring:

- **Edge Layer**: Sensor nodes that collect environmental data
- **Fog Layer**: Protocol bridging and data normalization 
- **Cloud Layer**: Data processing, storage, and visualization

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   EDGE LAYER    │    │   FOG LAYER     │    │  CLOUD LAYER    │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Temperature │ │    │ │   Node-RED  │ │    │ │   FastAPI   │ │
│ │   Sensors   │ │───▶│ │   Flows     │ │───▶│ │   Backend   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │  Humidity   │ │    │ │  Protocol   │ │    │ │   SQLite    │ │
│ │   Sensors   │ │───▶│ │  Gateway    │ │───▶│ │  Database   │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │ Luminosity  │ │    │ │    MQTT     │ │    │ │  WebSocket  │ │
│ │   Sensors   │ │───▶│ │   Broker    │ │───▶│ │   Server    │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
│                 │    │                 │    │                 │
│ ┌─────────────┐ │    │                 │    │ ┌─────────────┐ │
│ │    CoAP     │ │    │                 │    │ │  Frontend   │ │
│ │   Sensors   │ │───▶│                 │    │ │ Dashboard   │ │
│ └─────────────┘ │    │                 │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Component Details

### Edge Layer

**Purpose**: Data collection from physical sensors

**Components**:
- **Temperature Sensors**: Monitor ambient temperature (18-32°C)
- **Humidity Sensors**: Monitor relative humidity (30-80%)
- **Luminosity Sensors**: Monitor light levels (100-2000 lux)
- **CoAP Sensors**: Alternative protocol sensors for environmental data

**Protocols**:
- Primary: MQTT (publish to topics `sensors/{type}/{id}`)
- Alternative: CoAP (for bridge demonstration)

**Data Format**:
```json
{
  "ts": "2024-01-01T12:00:00Z",
  "type": "temperature",
  "value": 23.5,
  "unit": "°C",
  "sensor_id": "temp-001",
  "origin": "edge",
  "anomaly": false
}
```

**Anomaly Detection**:
- Out-of-range values (configurable thresholds)
- Sudden value jumps (>5°C for temperature, >15% for humidity, >500 lux for luminosity)
- Sensor malfunction indicators

### Fog Layer

**Purpose**: Protocol bridging, data normalization, and edge processing

**Components**:
- **Node-RED Flows**: Visual flow-based programming for data processing
- **MQTT Broker (Mosquitto)**: Message routing and queuing
- **Protocol Gateway**: HTTP to MQTT bridging

**Key Functions**:
- Convert CoAP sensor data to MQTT format
- Normalize different sensor payload formats
- Basic data validation and filtering
- Protocol translation (HTTP ↔ MQTT ↔ CoAP)

**Node-RED Flows**:
1. **CoAP to MQTT Bridge**: Polls CoAP sensors and publishes to MQTT
2. **HTTP Sensor Bridge**: Accepts HTTP POST sensor data and forwards to MQTT
3. **Data Normalization**: Ensures consistent payload format

### Cloud Layer

**Purpose**: Data persistence, processing, analysis, and visualization

**Components**:
- **FastAPI Backend**: REST API server with real-time WebSocket support
- **SQLite Database**: Sensor data storage with optional MySQL support
- **MQTT Client**: Subscribes to sensor topics for data ingestion
- **OpenWeather Integration**: External weather data for comparison
- **JWT Authentication**: Secure API access
- **WebSocket Server**: Real-time data streaming to frontend

**API Endpoints**:
- `GET /v1/sensors/latest` - Latest sensor readings
- `GET /v1/sensors/history` - Historical sensor data
- `GET /v1/sensors/anomalies` - Anomalous readings
- `GET /v1/sensors/stats` - System statistics
- `GET /v1/sensors/external/weather` - External weather data
- `GET /v1/sensors/compare/weather` - Compare sensors with weather
- `POST /v1/auth/login` - User authentication
- `WebSocket /ws` - Real-time data streaming

**Database Schema**:
- `sensor_readings`: Main table for all sensor data
- `users`: Authentication and user management

## Data Flow

1. **Edge → Fog**:
   - Sensors publish data to MQTT topics
   - CoAP sensors polled by Node-RED
   - HTTP sensors POST data to Node-RED

2. **Fog → Cloud**:
   - Node-RED normalizes and forwards data to MQTT
   - Cloud backend subscribes to MQTT topics
   - Data validated and stored in database

3. **Cloud → Frontend**:
   - REST APIs provide historical data
   - WebSocket streams real-time updates
   - Frontend renders charts and alerts

## Deployment Architecture

### Development (Docker Compose)
```yaml
services:
  mosquitto:    # MQTT Broker
  node-red:     # Fog Layer
  backend:      # Cloud API
  frontend:     # Web Dashboard
```

### Production Considerations
- Container orchestration (Kubernetes)
- Load balancing for API endpoints
- Database clustering (PostgreSQL/MySQL)
- Message queue scaling (Redis/RabbitMQ)
- CDN for frontend assets
- SSL/TLS termination
- Monitoring and logging (Prometheus/Grafana)

## Scalability Design

### Horizontal Scaling
- Multiple sensor instances per type
- Load-balanced API servers
- Database read replicas
- Message broker clustering

### Vertical Scaling
- Configurable data retention policies
- Batch processing for historical analysis
- Connection pooling
- Caching layers (Redis)

## Security Architecture

### Edge Security
- Sensor authentication (certificates)
- Encrypted communication (TLS)
- Device management and provisioning

### Cloud Security
- JWT-based API authentication
- Role-based access control (RBAC)
- API rate limiting
- Input validation and sanitization
- CORS configuration

### Network Security
- VPN/WireGuard for sensor communication
- Firewall rules and network segmentation
- MQTT authentication and ACLs

## Monitoring and Observability

### Metrics
- Sensor data ingestion rates
- API response times
- Database performance
- Message queue depths
- System resource usage

### Logging
- Structured logging (JSON format)
- Centralized log aggregation
- Error tracking and alerting
- Audit trails for security events

### Health Checks
- Service availability monitoring
- Database connectivity checks
- Message broker health
- External API dependency status

## Technology Choices

### Backend: FastAPI + Python
- **Pros**: Rapid development, excellent async support, automatic API documentation
- **Cons**: GIL limitations for CPU-intensive tasks
- **Alternatives**: Node.js/Express, Go, Rust

### Database: SQLite (dev) / PostgreSQL (prod)
- **Pros**: Simple setup, ACID compliance, JSON support
- **Cons**: SQLite limited concurrency
- **Alternatives**: InfluxDB (time-series), MongoDB (document)

### Message Broker: Eclipse Mosquitto
- **Pros**: Lightweight, MQTT 5.0 support, wide compatibility
- **Cons**: Limited clustering capabilities
- **Alternatives**: Apache Kafka, RabbitMQ, Redis Streams

### Frontend: Vanilla JS + Chart.js
- **Pros**: No build step, fast loading, simple deployment
- **Cons**: Limited component reusability
- **Alternatives**: React, Vue.js, Angular

### Containerization: Docker + Docker Compose
- **Pros**: Environment consistency, easy deployment, service isolation
- **Cons**: Resource overhead, complexity for simple deployments
- **Alternatives**: Native deployment, VM-based deployment