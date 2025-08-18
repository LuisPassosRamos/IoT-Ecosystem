# Fog Gateway

This directory is reserved for additional gateway components if needed beyond Node-RED flows.

## Purpose

While Node-RED handles most protocol bridging requirements, this directory can be used for:

- **Custom Protocol Gateways**: Protocols not supported by Node-RED
- **Edge Computing**: Local data processing before forwarding to cloud
- **Security Gateways**: Additional authentication and encryption layers
- **Performance Optimization**: High-throughput data processing

## Potential Components

### Custom Gateway Service
```python
# Example: Custom UDP to MQTT gateway
import socket
import json
import paho.mqtt.client as mqtt

class UDPGateway:
    def __init__(self):
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mqtt_client = mqtt.Client()
        
    def start(self):
        # Listen for UDP packets and forward to MQTT
        pass
```

### Data Aggregation Service
```javascript
// Example: Node.js data aggregation service
const mqtt = require('mqtt');

class DataAggregator {
    constructor() {
        this.client = mqtt.connect('mqtt://mosquitto:1883');
        this.buffer = [];
    }
    
    aggregate() {
        // Aggregate multiple sensor readings
        // Apply filtering and compression
        // Forward to cloud
    }
}
```

## Integration

### With Node-RED
- Complementary to Node-RED flows
- Handle specialized protocols
- Process high-frequency data streams

### With Cloud Backend
- Forward aggregated data via MQTT
- Maintain consistent API contracts
- Provide health monitoring endpoints

## Implementation Notes

For most use cases, Node-RED provides sufficient protocol bridging capabilities. This directory should only be used when:

1. **Performance Requirements**: Node-RED cannot handle the data throughput
2. **Custom Protocols**: Protocols not available in Node-RED
3. **Complex Processing**: Logic too complex for Node-RED flows
4. **Security Requirements**: Additional security layers needed

## Configuration

If implementing custom gateways:

```yaml
# docker-compose.yml extension
services:
  custom-gateway:
    build: ./fog/gateway
    environment:
      - MQTT_HOST=mosquitto
      - CLOUD_API=http://backend:8000
    depends_on:
      - mosquitto
      - backend
```

## Current Status

Currently, all protocol bridging is handled by Node-RED flows in the parent directory. This gateway directory is available for future expansion if needed.