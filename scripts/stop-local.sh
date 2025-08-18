#!/bin/bash
# Stop local development environment for IoT Ecosystem

set -e

echo "🛑 Stopping IoT Ecosystem Local Development Environment"
echo "====================================================="

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed."
    exit 1
fi

# Stop and remove containers
echo "🐳 Stopping Docker services..."
docker-compose down

# Optional: Remove volumes and clean up
read -p "🗑️  Remove data volumes? This will delete all sensor data! (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removing volumes..."
    docker-compose down -v
    echo "✅ Volumes removed"
fi

# Optional: Remove images
read -p "📦 Remove built images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧹 Removing images..."
    docker-compose down --rmi local
    echo "✅ Images removed"
fi

# Kill any running sensor processes
echo "🔍 Checking for running sensor processes..."
if pgrep -f "temp_sensor.py\|humidity_sensor.py\|luminosity_sensor.py\|coap_sensor.py" > /dev/null; then
    echo "🛑 Stopping sensor processes..."
    pkill -f "temp_sensor.py" 2>/dev/null || true
    pkill -f "humidity_sensor.py" 2>/dev/null || true
    pkill -f "luminosity_sensor.py" 2>/dev/null || true
    pkill -f "coap_sensor.py" 2>/dev/null || true
    echo "✅ Sensor processes stopped"
else
    echo "ℹ️  No sensor processes running"
fi

echo ""
echo "✅ IoT Ecosystem stopped successfully!"
echo ""
echo "🚀 To start again:"
echo "   ./scripts/start-local.sh"
echo ""