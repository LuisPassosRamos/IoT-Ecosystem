#!/bin/bash

# IoT-Ecosystem Local Development Startup Script
# This script starts all services using Docker Compose

set -e

echo "🚀 Starting IoT-Ecosystem Local Development Environment"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please review and update the configuration as needed."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p cloud-backend/data
mkdir -p samples/screenshots

# Set appropriate permissions
chmod 755 cloud-backend/data

echo "🐳 Starting Docker containers..."

# Start services with Docker Compose
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Function to check if a service is healthy
check_service() {
    local service_name=$1
    local url=$2
    local max_attempts=30
    local attempt=1
    
    echo "🔍 Checking $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo "✅ $service_name is ready!"
            return 0
        fi
        
        echo "⏳ Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo "❌ $service_name failed to start within expected time"
    return 1
}

# Check service health
echo ""
echo "🔍 Checking service health..."

# Check MQTT broker
if ! nc -z localhost 1883; then
    echo "❌ MQTT broker is not responding on port 1883"
else
    echo "✅ MQTT broker is ready!"
fi

# Check backend API
check_service "Backend API" "http://localhost:8000/health"

# Check frontend
check_service "Frontend" "http://localhost:3000"

# Check Node-RED
check_service "Node-RED" "http://localhost:1880"

echo ""
echo "🎉 IoT-Ecosystem is starting up!"
echo "================================"
echo ""
echo "📊 Service URLs:"
echo "  • Frontend Dashboard: http://localhost:3000"
echo "  • Backend API:        http://localhost:8000"
echo "  • API Documentation:  http://localhost:8000/docs"
echo "  • Node-RED:          http://localhost:1880"
echo ""
echo "🔧 Service Ports:"
echo "  • MQTT Broker:       localhost:1883"
echo "  • MQTT WebSocket:    localhost:9001"
echo "  • Frontend:          localhost:3000"
echo "  • Backend API:       localhost:8000"
echo "  • Node-RED:          localhost:1880"
echo ""
echo "📱 Demo Credentials:"
echo "  • Username: admin"
echo "  • Password: password123"
echo ""
echo "🧪 Quick Tests:"
echo "  • Health Check:      curl http://localhost:8000/health"
echo "  • Login:             curl -X POST http://localhost:8000/v1/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"password123\"}'"
echo "  • MQTT Subscribe:    mosquitto_sub -h localhost -t 'sensors/+/+' -v"
echo ""
echo "📚 Next Steps:"
echo "  1. Open the dashboard at http://localhost:3000"
echo "  2. Start some sensors:"
echo "     cd edge/sensors"
echo "     python3 temp_sensor.py &"
echo "     python3 humidity_sensor.py &"
echo "     python3 luminosity_sensor.py &"
echo "  3. Start CoAP simulator:"
echo "     cd edge/coap_simulator"
echo "     python3 coap_sensor.py &"
echo "  4. Monitor logs:"
echo "     docker-compose logs -f"
echo ""
echo "🛑 To stop all services:"
echo "  ./scripts/stop-local.sh"
echo ""

# Check if Python is available for sensors
if command -v python3 > /dev/null 2>&1; then
    echo "🐍 Python 3 is available for running sensor simulators"
    
    # Check if required Python packages are installed
    if python3 -c "import paho.mqtt.client" 2>/dev/null; then
        echo "✅ paho-mqtt is installed"
    else
        echo "⚠️  paho-mqtt is not installed. Install with: pip3 install paho-mqtt"
    fi
    
    if python3 -c "import aiocoap" 2>/dev/null; then
        echo "✅ aiocoap is installed"
    else
        echo "⚠️  aiocoap is not installed. Install with: pip3 install aiocoap"
    fi
else
    echo "⚠️  Python 3 is not available. Install Python 3 to run sensor simulators."
fi

echo ""
echo "✨ IoT-Ecosystem is ready! Happy monitoring! 🌐"