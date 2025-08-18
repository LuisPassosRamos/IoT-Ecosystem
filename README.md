# 🌐 IoT-Ecosystem

A complete, modular IoT environment monitoring system implementing **Edge-Fog-Cloud** architecture with multiple protocols (MQTT, HTTP REST, CoAP), real-time frontend (Chart.js), and basic security (JWT).

![IoT Architecture](https://img.shields.io/badge/Architecture-Edge%20%7C%20Fog%20%7C%20Cloud-blue)
![Protocols](https://img.shields.io/badge/Protocols-MQTT%20%7C%20CoAP%20%7C%20HTTP%20%7C%20WebSocket-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)

## 🎯 Overview

IoT-Ecosystem demonstrates a **production-ready IoT architecture** with:
- **Edge Layer**: Python sensor simulators with intelligent anomaly detection
- **Fog Layer**: Node-RED flows for protocol bridging (CoAP ↔ MQTT)  
- **Cloud Layer**: FastAPI backend with real-time dashboard
- **Multi-Protocol**: MQTT, HTTP REST, CoAP, WebSocket support
- **Real-time**: Live data streaming with Chart.js visualization
- **Security**: JWT authentication with configurable access control
- **External APIs**: OpenWeatherMap integration for data comparison

## 🚀 Quick Start

### Prerequisites
- **Docker & Docker Compose** (required)
- **Python 3.11+** (for running sensors locally)
- **OpenWeatherMap API key** (optional, for weather comparison)

### 1. Clone and Start
```bash
git clone https://github.com/LuisPassosRamos/IoT-Ecosystem.git
cd IoT-Ecosystem

# Copy environment configuration
cp .env.example .env

# Start all services
./scripts/start-local.sh
```

### 2. Access Services
- 📊 **Frontend Dashboard**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000
- 📖 **API Documentation**: http://localhost:8000/docs
- 🔄 **Node-RED**: http://localhost:1880

### 3. Demo Credentials
- **Username**: `admin`
- **Password**: `password123`

### 4. Start Sensors (Optional)
```bash
# Terminal 1: Temperature sensor
cd edge/sensors && python3 temp_sensor.py

# Terminal 2: Humidity sensor  
cd edge/sensors && python3 humidity_sensor.py

# Terminal 3: Luminosity sensor
cd edge/sensors && python3 luminosity_sensor.py

# Terminal 4: CoAP simulator
cd edge/coap_simulator && python3 coap_sensor.py
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   FastAPI   │  │  Frontend   │  │ OpenWeather │            │
│  │   Backend   │  │ Dashboard   │  │     API     │            │
│  │ • REST API  │  │ • Chart.js  │  │ • Weather   │            │
│  │ • WebSocket │  │ • Real-time │  │   Data      │            │
│  │ • SQLite    │  │ • Anomaly   │  │ • Compare   │            │
│  │ • JWT Auth  │  │   Alerts    │  │   Local     │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│                        FOG LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Node-RED   │  │    MQTT     │  │  Optional   │            │
│  │    Flows    │  │   Broker    │  │  Gateway    │            │
│  │ • CoAP→MQTT │  │ • Eclipse   │  │ • Express   │            │
│  │ • Normalize │  │   Mosquitto │  │ • REST API  │            │
│  │ • Bridge    │  │ • Pub/Sub   │  │ • Caching   │            │
│  │ • Filter    │  │ • WebSocket │  │ • Filter    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────────┐
│                        EDGE LAYER                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Temperature │  │  Humidity   │  │ Luminosity  │            │
│  │   Sensor    │  │   Sensor    │  │   Sensor    │            │
│  │ • MQTT Pub  │  │ • MQTT Pub  │  │ • MQTT Pub  │            │
│  │ • Anomaly   │  │ • Anomaly   │  │ • Anomaly   │            │
│  │   Detection │  │   Detection │  │   Detection │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                │
│  ┌─────────────┐                                              │
│  │    CoAP     │  Alternative protocol for Fog bridging      │
│  │  Simulator  │                                              │
│  │ • aiocoap   │                                              │
│  │ • Endpoints │                                              │
│  └─────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
IoT-Ecosystem/
├── 📋 README.md                    # This file
├── 🔧 .env.example                 # Environment configuration template
├── 📄 LICENSE                      # MIT License
├── 🐳 docker-compose.yml           # Container orchestration
├── 
├── 🌐 edge/                        # Edge Layer - Sensor simulators
│   ├── sensors/
│   │   ├── temp_sensor.py          # Temperature sensor with anomaly detection
│   │   ├── humidity_sensor.py      # Humidity sensor with anomaly detection
│   │   └── luminosity_sensor.py    # Luminosity sensor with anomaly detection
│   ├── coap_simulator/
│   │   └── coap_sensor.py          # CoAP server simulation
│   └── README.md
├── 
├── 🌫️ fog/                         # Fog Layer - Protocol bridging
│   ├── node-red/
│   │   └── flows.json              # Node-RED flow configuration
│   ├── gateway/
│   │   └── README.md               # Optional gateway documentation
│   └── README.md
├── 
├── ☁️ cloud-backend/               # Cloud Layer - Backend API
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── api/v1/
│   │   │   ├── sensors.py          # Sensor data endpoints
│   │   │   └── auth.py             # Authentication endpoints
│   │   ├── services/
│   │   │   ├── mqtt_client.py      # MQTT integration service
│   │   │   └── openweather.py      # OpenWeatherMap integration
│   │   └── models/
│   │       └── schemas.py          # Pydantic data models
│   ├── requirements.txt            # Python dependencies
│   ├── Dockerfile                  # Container configuration
│   └── README.md
├── 
├── 🎨 frontend/                    # Frontend Dashboard
│   ├── index.html                  # Main dashboard page
│   ├── app.js                      # Application logic
│   ├── charts/
│   │   └── chart-utils.js          # Chart.js utilities
│   └── README.md
├── 
├── 🔧 infra/                       # Infrastructure configuration
│   ├── mqtt/
│   │   └── mosquitto.conf          # MQTT broker configuration
│   └── nginx.conf                  # Web server configuration
├── 
├── 📚 docs/                        # Documentation
│   ├── architecture.md             # System architecture details
│   ├── protocols_table.md          # Protocol comparison and usage
│   └── security.md                 # Security and LGPD compliance
├── 
├── 📊 samples/                     # Sample data and examples
│   ├── payloads.json               # Example sensor payloads
│   └── screenshots/                # System screenshots
├── 
├── 🔧 scripts/                     # Utility scripts
│   ├── start-local.sh              # Start all services
│   └── stop-local.sh               # Stop all services
└── 
└── 🧪 tests/                       # Test suites
    ├── test_backend.py             # Backend API tests
    └── test_sensors.py             # Sensor logic tests
```

## 🛠️ Technology Stack

### Edge Layer
- **Python 3.11+** with asyncio
- **paho-mqtt** for MQTT communication
- **aiocoap** for CoAP server simulation
- **Intelligent anomaly detection** (threshold & jump-based)

### Fog Layer  
- **Node-RED** for visual programming flows
- **Eclipse Mosquitto** MQTT broker
- **Protocol bridging** (CoAP ↔ MQTT)
- **Data normalization** and filtering

### Cloud Layer
- **FastAPI** with automatic OpenAPI docs
- **Pydantic** for data validation
- **SQLAlchemy** with SQLite/MySQL support
- **WebSocket** for real-time communication
- **JWT authentication** with configurable expiration

### Frontend
- **Vanilla JavaScript** (ES6+)
- **Chart.js** for data visualization
- **CSS Grid** responsive design
- **WebSocket** real-time updates

### Infrastructure
- **Docker Compose** for local development
- **NGINX** for production deployment
- **Environment-based** configuration
- **Health monitoring** and logging

## 🔌 Protocol Implementation

| Protocol | Port | Purpose | Implementation |
|----------|------|---------|----------------|
| **MQTT** | 1883, 9001 | Primary sensor communication | Eclipse Mosquitto |
| **CoAP** | 5683 | Lightweight sensor endpoints | aiocoap (Python) |
| **HTTP REST** | 8000 | API management & external integration | FastAPI |
| **WebSocket** | 8000/ws | Real-time frontend updates | FastAPI native |

### MQTT Topics Structure
```
sensors/temperature/sim001     # Direct MQTT sensor
sensors/humidity/sim001        # Direct MQTT sensor
sensors/luminosity/sim001      # Direct MQTT sensor
sensors/temperature/fog_bridge # CoAP→MQTT bridged
sensors/humidity/fog_bridge    # CoAP→MQTT bridged
fog/bridge/status             # Fog layer status
fog/bridge/errors             # Error reporting
```

## 🎛️ Configuration

### Environment Variables
```bash
# MQTT Configuration
MQTT_HOST=localhost
MQTT_PORT=1883

# Database
DATABASE_URL=sqlite:///./sensor_data.db

# Authentication  
JWT_SECRET=your-secret-key-here
DEMO_USERNAME=admin
DEMO_PASSWORD=password123

# External APIs
OPENWEATHER_API_KEY=your-api-key-here

# Anomaly Detection Thresholds
TEMP_MIN=15.0
TEMP_MAX=35.0
TEMP_JUMP_THRESHOLD=5.0
HUMIDITY_MIN=30.0
HUMIDITY_MAX=90.0
WEATHER_DIFF_THRESHOLD=5.0
```

## 🧪 Testing

### Run Backend Tests
```bash
cd tests
python -m pytest test_backend.py -v
```

### Run Sensor Tests  
```bash
cd tests
python -m pytest test_sensors.py -v
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password123"}'

# Get latest readings
curl -X GET http://localhost:8000/v1/sensors/latest \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### MQTT Testing
```bash
# Subscribe to all sensors
mosquitto_sub -h localhost -t "sensors/+/+" -v

# Subscribe to specific sensor
mosquitto_sub -h localhost -t "sensors/temperature/+" -v

# Publish test message
mosquitto_pub -h localhost -t "sensors/test/manual" \
  -m '{"ts":"2024-01-01T12:00:00Z","type":"test","value":42}'
```

## 📊 Features & Capabilities

### 🔍 Anomaly Detection
- **Range-based**: Values outside min/max thresholds
- **Jump-based**: Sudden changes exceeding jump thresholds  
- **Multi-layer**: Detection at Edge, Fog, and Cloud layers
- **Configurable**: Thresholds via environment variables
- **Visual alerts**: Dashboard highlighting and notifications

### 📈 Real-time Dashboard
- **Live charts**: Temperature, humidity, luminosity with Chart.js
- **WebSocket streaming**: Sub-second data updates
- **Anomaly highlighting**: Visual indicators for unusual readings
- **Historical data**: Configurable time ranges and filtering
- **Responsive design**: Mobile-friendly interface

### 🌐 External Integration
- **OpenWeatherMap API**: Weather data comparison
- **Discrepancy alerts**: Local vs external data differences
- **Configurable thresholds**: Alert sensitivity control
- **Multiple cities**: Support for different locations

### 🔒 Security & Compliance
- **JWT authentication**: Configurable expiration and secrets
- **LGPD compliance**: Data protection and privacy by design
- **Input validation**: Pydantic models with strict validation
- **CORS configuration**: Cross-origin request control
- **Audit logging**: Comprehensive activity tracking

## 🚀 Deployment

### Development (Local)
```bash
# Start all services
./scripts/start-local.sh

# View logs
docker-compose logs -f

# Stop all services
./scripts/stop-local.sh
```

### Production
```bash
# Set production environment
export JWT_SECRET=$(openssl rand -base64 32)
export OPENWEATHER_API_KEY=your-production-key

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up --scale backend=3
```

### Kubernetes (Example)
```bash
# Create namespace
kubectl create namespace iot-ecosystem

# Deploy services
kubectl apply -f k8s/
```

## 📖 Documentation

### 📋 Component Documentation
- [**Edge Layer**](edge/README.md) - Sensor simulators and CoAP
- [**Fog Layer**](fog/README.md) - Node-RED flows and bridging
- [**Cloud Backend**](cloud-backend/README.md) - FastAPI and services
- [**Frontend**](frontend/README.md) - Dashboard and real-time UI

### 🏗️ Architecture Documentation
- [**System Architecture**](docs/architecture.md) - Complete system design
- [**Protocol Comparison**](docs/protocols_table.md) - MQTT, CoAP, HTTP, WebSocket
- [**Security & LGPD**](docs/security.md) - Security measures and compliance

### 📊 Sample Data
- [**Payload Examples**](samples/payloads.json) - Example sensor data and API responses

## 🤝 Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines
- Follow **PEP 8** for Python code
- Use **TypeScript** for complex JavaScript
- Include **tests** for new features
- Update **documentation** as needed
- Ensure **Docker** compatibility

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Eclipse Mosquitto** - MQTT broker
- **Node-RED** - Visual programming for IoT
- **FastAPI** - Modern Python web framework
- **Chart.js** - Beautiful charts for the web
- **Docker** - Containerization platform
- **OpenWeatherMap** - Weather data API

## 📞 Support

For questions, issues, or contributions:

- 📫 **Email**: [GitHub Issues](https://github.com/LuisPassosRamos/IoT-Ecosystem/issues)
- 📚 **Documentation**: [Project Docs](docs/)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/LuisPassosRamos/IoT-Ecosystem/issues)
- 💡 **Feature Requests**: [GitHub Issues](https://github.com/LuisPassosRamos/IoT-Ecosystem/issues)

---

**🌟 Star this project if you find it useful!**

Built with ❤️ for the IoT community

