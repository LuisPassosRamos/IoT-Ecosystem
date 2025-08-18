# IoT Ecosystem - Environmental Monitoring Platform

A complete, modular IoT environmental monitoring system implementing Edge-Fog-Cloud architecture with multiple protocols, real-time visualization, and intelligent anomaly detection.

## 🌟 Features

- **Multi-Protocol Support**: MQTT, HTTP REST, CoAP sensor integration
- **Real-time Dashboard**: Live data visualization with Chart.js
- **Anomaly Detection**: Intelligent sensor anomaly detection and alerting  
- **Weather Integration**: Compare local sensors with OpenWeather API
- **Protocol Bridging**: Node-RED flows for seamless protocol translation
- **JWT Authentication**: Secure API access with role-based permissions
- **WebSocket Streaming**: Real-time data updates to frontend
- **Docker Deployment**: Complete containerized environment
- **Comprehensive Testing**: Backend and sensor logic testing

## 🏗️ Architecture

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

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+ (for running sensors locally)
- Git

### 1. Clone Repository
```bash
git clone https://github.com/LuisPassosRamos/IoT-Ecosystem.git
cd IoT-Ecosystem
```

### 2. Start Services
```bash
# Start all services with Docker Compose
./scripts/start-local.sh

# Or manually
docker-compose up --build -d
```

### 3. Access Dashboard
- **Frontend Dashboard**: http://localhost:8080
- **Backend API**: http://localhost:8000/docs
- **Node-RED**: http://localhost:1880

### 4. Start Sensors
```bash
# Terminal 1: Temperature sensor
cd edge/sensors
python temp_sensor.py

# Terminal 2: Humidity sensor  
python humidity_sensor.py

# Terminal 3: Luminosity sensor
python luminosity_sensor.py

# Terminal 4: CoAP sensor
cd ../coap_simulator
python coap_sensor.py
```

### 5. Login to Dashboard
- **Username**: `admin`
- **Password**: `admin123`

## 📋 Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend Dashboard | http://localhost:8080 | Real-time monitoring dashboard |
| Backend API | http://localhost:8000 | REST API endpoints |
| API Documentation | http://localhost:8000/docs | Interactive API documentation |
| Node-RED | http://localhost:1880 | Protocol bridging flows |
| MQTT Broker | localhost:1883 | Message broker (internal) |
| MQTT WebSocket | localhost:9001 | MQTT over WebSocket |

## 🌡️ Sensor Data

### MQTT Topics
```
sensors/temperature/temp-001    # Temperature readings
sensors/humidity/hum-001        # Humidity readings  
sensors/luminosity/lum-001      # Light level readings
sensors/+/+                     # All sensor data
```

### Payload Format
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

### CoAP Endpoints
```
coap://localhost:5683/sensor      # Full environmental data
coap://localhost:5683/temperature # Temperature only
```

## 🔌 API Endpoints

### Authentication
- `POST /v1/auth/login` - User authentication
- `GET /v1/auth/me` - Current user info

### Sensor Data
- `GET /v1/sensors/latest` - Latest readings from all sensors
- `GET /v1/sensors/history` - Historical sensor data
- `GET /v1/sensors/anomalies` - Anomalous readings
- `GET /v1/sensors/stats` - System statistics

### Weather Integration
- `GET /v1/sensors/external/weather` - OpenWeather API data
- `GET /v1/sensors/compare/weather` - Compare sensors with weather

### Real-time
- `WebSocket /ws` - Real-time sensor data stream

## 🧪 Testing

### Run Backend Tests
```bash
cd tests
python -m pytest test_backend.py -v
```

### Run Sensor Tests
```bash
python -m pytest test_sensors.py -v
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/health

# Get latest sensor data
curl http://localhost:8000/v1/sensors/latest

# Login and get token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

## 📊 Monitoring

### MQTT Monitoring
```bash
# Subscribe to all sensor data
mosquitto_sub -h localhost -t "sensors/+/+"

# Monitor anomalies only
mosquitto_sub -h localhost -t "sensors/+/+" | grep '"anomaly":true'

# Monitor specific sensor type
mosquitto_sub -h localhost -t "sensors/temperature/+"
```

### Logs
```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f mosquitto
docker-compose logs -f node-red
```

### System Status
```bash
# Check service health
curl http://localhost:8000/health

# API status
curl http://localhost:8000/api/status

# Container status
docker-compose ps
```

## 🛠️ Configuration

### Environment Variables
Copy `.env.example` to `.env` and configure:

```bash
# Backend Configuration
PORT=8000
JWT_SECRET=your-secret-key
DEMO_USER=admin
DEMO_PASS=admin123

# Database
DB_URL=sqlite:///data/app.db

# MQTT Broker
MQTT_HOST=mosquitto
MQTT_PORT=1883
MQTT_WS_PORT=9001

# OpenWeather API (optional)
OPENWEATHER_API_KEY=your-api-key
DEFAULT_CITY=London

# CORS
CORS_ORIGINS=*
```

### Sensor Configuration
Edit sensor parameters in Python files:

```python
# Temperature sensor ranges
NORMAL_RANGE = (18.0, 32.0)  # °C
ANOMALY_THRESHOLD = 5.0      # °C jump
UPDATE_INTERVAL = 2          # seconds
```

## 🐳 Docker Services

### Service Composition
```yaml
services:
  mosquitto:     # MQTT Broker
  node-red:      # Fog Layer  
  backend:       # Cloud API
  frontend:      # Web Dashboard
```

### Data Persistence
- **Backend Data**: `./cloud-backend/data`
- **Node-RED Data**: `./fog/node-red/data`
- **Database**: SQLite file in backend data volume

## 📚 Documentation

- **[Architecture](docs/architecture.md)**: System design and components
- **[Protocols](docs/protocols_table.md)**: MQTT, HTTP, CoAP comparison
- **[Security](docs/security.md)**: Security measures and GDPR compliance
- **[Edge README](edge/README.md)**: Sensor implementation details
- **[Fog README](fog/README.md)**: Node-RED flow configuration  
- **[Cloud README](cloud-backend/README.md)**: Backend API documentation
- **[Frontend README](frontend/README.md)**: Dashboard features and customization

## 🔧 Development

### Local Development Setup
```bash
# Install Python dependencies for sensors
cd edge/sensors
pip install paho-mqtt aiocoap

# Install backend dependencies  
cd ../../cloud-backend
pip install -r requirements.txt

# Run backend locally
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Adding New Sensor Types
1. Create sensor script in `edge/sensors/`
2. Implement anomaly detection logic
3. Configure MQTT publishing
4. Add to Node-RED flows if needed
5. Update frontend dashboard

### Custom Protocol Integration
1. Add protocol client to edge layer
2. Create Node-RED flow for protocol bridging
3. Update backend to handle new data format
4. Add frontend visualization

## 🛡️ Security Features

- **JWT Authentication**: Secure API access
- **Input Validation**: Pydantic model validation
- **CORS Configuration**: Cross-origin request handling
- **TLS Support**: Encrypted communications
- **Anomaly Detection**: Intelligent threat detection
- **Rate Limiting**: API abuse prevention

## 🌍 Compliance

- **GDPR**: Data protection and privacy
- **LGPD**: Brazilian data protection law
- **Security Headers**: XSS, CSRF protection
- **Audit Logging**: Security event logging

## 🚫 Stop Services

```bash
# Stop all services
./scripts/stop-local.sh

# Or manually
docker-compose down

# Remove volumes (deletes data)
docker-compose down -v
```

## 📈 Scaling Considerations

### Horizontal Scaling
- Multiple sensor instances per type
- Load-balanced API servers  
- Database read replicas
- Message broker clustering

### Performance Optimization
- Configurable data retention
- Connection pooling
- Caching layers
- Batch processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement changes with tests
4. Submit a pull request

### Development Guidelines
- Follow existing code style
- Add tests for new features
- Update documentation
- Keep dependencies minimal

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎯 Use Cases

- **Smart Buildings**: Temperature, humidity, light monitoring
- **Industrial IoT**: Equipment monitoring and anomaly detection
- **Environmental Research**: Climate data collection and analysis
- **Smart Agriculture**: Greenhouse and field monitoring
- **Home Automation**: Smart home sensor integration

## 🔮 Future Enhancements

- [ ] Machine learning anomaly detection
- [ ] Time-series database integration (InfluxDB)
- [ ] Mobile application
- [ ] Advanced alerting (email, SMS)
- [ ] Multi-tenant support
- [ ] Kubernetes deployment
- [ ] Advanced analytics dashboard
- [ ] Edge AI processing

---

**Happy Monitoring! 🚀**

For questions or support, please open an issue or contact the development team.
