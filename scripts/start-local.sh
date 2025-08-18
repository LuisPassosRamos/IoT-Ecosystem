#!/bin/bash
# Local development startup script for IoT Ecosystem

set -e

echo "🚀 Starting IoT Ecosystem Local Development Environment"
echo "=================================================="

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ Please edit .env file and add your OpenWeather API key if needed"
fi

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p cloud-backend/data
mkdir -p fog/node-red/data
mkdir -p samples/screenshots

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check MQTT broker
if docker-compose exec -T mosquitto mosquitto_sub -h localhost -t '$SYS/broker/version' -C 1 >/dev/null 2>&1; then
    echo "✅ MQTT Broker (Mosquitto) is running"
else
    echo "⚠️  MQTT Broker may not be ready yet"
fi

# Check backend API
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo "✅ Backend API is running"
else
    echo "⚠️  Backend API may not be ready yet"
fi

# Check Node-RED
if curl -s http://localhost:1880 >/dev/null 2>&1; then
    echo "✅ Node-RED is running"
else
    echo "⚠️  Node-RED may not be ready yet"
fi

# Check frontend
if curl -s http://localhost:8080 >/dev/null 2>&1; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend may not be ready yet"
fi

echo ""
echo "🎉 IoT Ecosystem is starting up!"
echo ""
echo "🌐 Service URLs:"
echo "   • Frontend Dashboard: http://localhost:8080"
echo "   • Backend API:        http://localhost:8000"
echo "   • API Documentation:  http://localhost:8000/docs"
echo "   • Node-RED:          http://localhost:1880"
echo "   • MQTT Broker:       localhost:1883"
echo ""
echo "📊 Demo Credentials:"
echo "   • Username: admin"
echo "   • Password: admin123"
echo ""
echo "🚀 To start sensors:"
echo "   cd edge/sensors"
echo "   python temp_sensor.py      # Terminal 1"
echo "   python humidity_sensor.py  # Terminal 2"
echo "   python luminosity_sensor.py # Terminal 3"
echo ""
echo "📱 To start CoAP sensor:"
echo "   cd edge/coap_simulator"
echo "   python coap_sensor.py"
echo ""
echo "📋 To view logs:"
echo "   docker-compose logs -f [service_name]"
echo ""
echo "🛑 To stop:"
echo "   ./scripts/stop-local.sh"
echo ""

# Optional: Start a sensor automatically for demo
read -p "🤖 Start a demo temperature sensor? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🌡️  Starting demo temperature sensor..."
    cd edge/sensors
    python temp_sensor.py &
    SENSOR_PID=$!
    echo "✅ Demo sensor started (PID: $SENSOR_PID)"
    echo "   Kill with: kill $SENSOR_PID"
    cd ../..
fi

echo "✨ Setup complete! Happy monitoring! ✨"