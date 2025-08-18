#!/bin/bash

# IoT-Ecosystem Local Development Shutdown Script
# This script stops all services and cleans up resources

set -e

echo "🛑 Stopping IoT-Ecosystem Local Development Environment"
echo "====================================================="

# Function to stop a process by name
stop_process() {
    local process_name=$1
    local pids=$(pgrep -f "$process_name" 2>/dev/null || true)
    
    if [ -n "$pids" ]; then
        echo "🔌 Stopping $process_name processes..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        
        # Force kill if still running
        local remaining_pids=$(pgrep -f "$process_name" 2>/dev/null || true)
        if [ -n "$remaining_pids" ]; then
            echo "🔥 Force stopping $process_name processes..."
            echo "$remaining_pids" | xargs kill -KILL 2>/dev/null || true
        fi
        echo "✅ $process_name processes stopped"
    fi
}

# Stop sensor simulators if running
echo "🔌 Stopping sensor simulators..."
stop_process "temp_sensor.py"
stop_process "humidity_sensor.py"
stop_process "luminosity_sensor.py"
stop_process "coap_sensor.py"

# Stop Docker containers
echo "🐳 Stopping Docker containers..."
if command -v docker-compose > /dev/null 2>&1; then
    docker-compose down
    echo "✅ Docker containers stopped"
else
    echo "⚠️  Docker Compose not found, skipping container shutdown"
fi

# Optional: Remove containers and volumes (uncomment if you want full cleanup)
# echo "🧹 Removing containers and volumes..."
# docker-compose down -v --remove-orphans
# docker system prune -f

# Check if any containers are still running
running_containers=$(docker ps --filter "name=iot-" --format "table {{.Names}}" 2>/dev/null | grep -v NAMES || true)
if [ -n "$running_containers" ]; then
    echo "⚠️  Some IoT-Ecosystem containers are still running:"
    echo "$running_containers"
    echo "📝 You may want to stop them manually with: docker stop <container_name>"
else
    echo "✅ All IoT-Ecosystem containers stopped"
fi

# Show current status
echo ""
echo "📊 Current Status:"
echo "=================="

# Check ports
echo "🔍 Checking if ports are still in use..."
ports=(1883 8000 3000 1880 9001 5683)
any_ports_in_use=false

for port in "${ports[@]}"; do
    if lsof -i :$port > /dev/null 2>&1; then
        echo "⚠️  Port $port is still in use"
        any_ports_in_use=true
    fi
done

if [ "$any_ports_in_use" = false ]; then
    echo "✅ All IoT-Ecosystem ports are free"
fi

# Check Docker status
echo ""
echo "🐳 Docker Status:"
echo "================"
if docker ps --filter "name=iot-" --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | grep -v NAMES; then
    echo "⚠️  Some IoT-Ecosystem containers may still be running"
else
    echo "✅ No IoT-Ecosystem containers running"
fi

# Show cleanup options
echo ""
echo "🧹 Cleanup Options:"
echo "=================="
echo "To perform additional cleanup:"
echo ""
echo "• Remove all stopped containers:"
echo "  docker container prune -f"
echo ""
echo "• Remove unused images:"
echo "  docker image prune -f"
echo ""
echo "• Remove all unused Docker resources:"
echo "  docker system prune -f"
echo ""
echo "• Remove volumes (⚠️  will delete all data):"
echo "  docker volume prune -f"
echo ""
echo "• Complete reset (⚠️  will delete all data and containers):"
echo "  docker-compose down -v --remove-orphans"
echo "  docker system prune -a -f --volumes"
echo ""

# Show restart instructions
echo "🔄 To restart the system:"
echo "========================"
echo "  ./scripts/start-local.sh"
echo ""

echo "✅ IoT-Ecosystem shutdown complete!"