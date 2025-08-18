# Fog Layer - Protocol Bridging

This directory contains the fog layer components that provide protocol bridging and data normalization between edge devices and the cloud.

## Components

### Node-RED Flows
- **flows.json**: Pre-configured flows for protocol bridging
- **CoAP to MQTT Bridge**: Polls CoAP sensors and publishes to MQTT
- **HTTP to MQTT Bridge**: Accepts HTTP sensor data and forwards to MQTT

### Gateway (Optional)
- **gateway/**: Directory for additional gateway components if needed

## Features

### Protocol Bridging
- **CoAP → MQTT**: Converts CoAP sensor readings to MQTT messages
- **HTTP → MQTT**: Accepts REST API calls and publishes to MQTT
- **Data Normalization**: Ensures consistent payload format across protocols

### Node-RED Flows
1. **CoAP Polling Flow**: Periodically requests data from CoAP sensors
2. **HTTP Input Flow**: Accepts POST requests from HTTP sensors
3. **Data Processing Flow**: Normalizes and validates sensor data
4. **MQTT Publishing Flow**: Publishes formatted data to MQTT topics

## Setup

### Node-RED Access
- **URL**: http://localhost:1880
- **Username**: (none - open access for development)
- **Flows**: Auto-imported from flows.json

### Import Flows
1. Open Node-RED at http://localhost:1880
2. Go to Menu → Import
3. Copy contents of `flows.json`
4. Click Import

## Flow Descriptions

### CoAP to MQTT Bridge Flow

```
[Inject Timer] → [CoAP Request] → [Parse JSON] → [Normalize Data] → [MQTT Publish]
      ↓              ↓              ↓              ↓               ↓
   Every 5s      GET /sensor    JSON Parser    Format for     Publish to
                                              MQTT topic    sensors/{type}/{id}
```

**Configuration**:
- **Timer**: 5-second intervals
- **CoAP URL**: `coap://host.docker.internal:5683/sensor`
- **Output**: Multiple MQTT messages for each measurement

### HTTP to MQTT Bridge Flow

```
[HTTP Input] → [Validate Data] → [Format Message] → [MQTT Publish] → [HTTP Response]
      ↓              ↓               ↓                ↓                ↓
POST /sensors/   Check required    Add metadata    Publish to      Return 200 OK
{type}/{id}        fields        & timestamp     MQTT topic     or error status
```

**Endpoints**:
- `POST /sensors/temperature/{id}` 
- `POST /sensors/humidity/{id}`
- `POST /sensors/luminosity/{id}`

## Data Flow

### Input Formats

#### CoAP Response
```json
{
  "sensor_id": "coap-env-001",
  "timestamp": "2024-01-01T12:00:00Z",
  "measurements": {
    "temperature": {"value": 22.1, "unit": "°C"},
    "humidity": {"value": 65.2, "unit": "%"},
    "pressure": {"value": 1013.25, "unit": "hPa"}
  },
  "protocol": "coap",
  "origin": "edge"
}
```

#### HTTP Request
```bash
POST /sensors/temperature/temp-002
Content-Type: application/json

{
  "value": 24.1,
  "unit": "°C",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### Output Format (MQTT)
```json
{
  "ts": "2024-01-01T12:00:00Z",
  "type": "temperature",
  "value": 22.1,
  "unit": "°C",
  "sensor_id": "coap-env-001-temperature",
  "origin": "fog",
  "source_protocol": "coap"
}
```

## Testing

### Test CoAP Bridge
```bash
# Start CoAP sensor
cd ../edge/coap_simulator
python coap_sensor.py

# Check Node-RED debug output for CoAP data
# Monitor MQTT for bridged messages
mosquitto_sub -h localhost -t "sensors/+/coap-env-001-+"
```

### Test HTTP Bridge
```bash
# Send HTTP sensor data
curl -X POST "http://localhost:1880/sensors/temperature/temp-http-001" \
  -H "Content-Type: application/json" \
  -d '{
    "value": 25.5,
    "unit": "°C",
    "timestamp": "2024-01-01T12:00:00Z"
  }'

# Monitor MQTT for bridged messages
mosquitto_sub -h localhost -t "sensors/temperature/temp-http-001"
```

### Debug in Node-RED
1. Open Node-RED UI at http://localhost:1880
2. Enable debug nodes in flows
3. View debug messages in the right panel
4. Monitor data flow through each step

## Customization

### Add New Protocol Support
1. Create new flow in Node-RED
2. Add input node for the protocol (e.g., UDP, Serial)
3. Add data parsing and normalization logic
4. Connect to MQTT output node

### Modify Data Processing
1. Edit the "Normalize Data" function nodes
2. Add validation logic
3. Implement custom transformations
4. Add error handling

### Configure MQTT Settings
1. Edit MQTT broker node settings
2. Update connection parameters
3. Configure QoS and retention policies
4. Set up authentication if needed

## Flow Configuration

### MQTT Broker Node
```javascript
{
  "broker": "mosquitto",
  "port": 1883,
  "clientid": "nodered-bridge",
  "keepalive": 60,
  "cleansession": true
}
```

### CoAP Request Function
```javascript
// CoAP request to environmental sensor
const coapUrl = "coap://host.docker.internal:5683/sensor";
msg.url = coapUrl;
msg.method = "GET";
return msg;
```

### Data Normalization Function
```javascript
// Convert CoAP data to MQTT sensor format
const coapData = msg.payload;
const messages = [];

for (const [measureType, measurement] of Object.entries(coapData.measurements)) {
  const mqttPayload = {
    ts: coapData.timestamp,
    type: measureType,
    value: measurement.value,
    unit: measurement.unit,
    sensor_id: `${coapData.sensor_id}-${measureType}`,
    origin: "fog",
    source_protocol: "coap"
  };
  
  messages.push({
    topic: `sensors/${measureType}/${mqttPayload.sensor_id}`,
    payload: JSON.stringify(mqttPayload)
  });
}

return messages;
```

## Monitoring

### Node-RED Dashboard
- **Flow Status**: Visual indication of active flows
- **Debug Output**: Real-time message inspection
- **Error Handling**: Failed message notifications

### MQTT Monitoring
```bash
# Monitor all bridged messages
mosquitto_sub -h localhost -t "sensors/+/+" | grep '"origin":"fog"'

# Monitor specific protocol sources
mosquitto_sub -h localhost -t "sensors/+/+" | grep '"source_protocol":"coap"'
```

### System Health
```bash
# Check Node-RED container status
docker-compose ps node-red

# View Node-RED logs
docker-compose logs -f node-red

# Check MQTT broker connectivity
mosquitto_pub -h localhost -t "test/nodered" -m "ping"
```

## Troubleshooting

### CoAP Bridge Issues
1. **CoAP sensor not responding**:
   - Check if CoAP sensor is running
   - Verify network connectivity
   - Check firewall settings for UDP port 5683

2. **No MQTT output**:
   - Verify MQTT broker connection
   - Check function node for errors
   - Enable debug output

### HTTP Bridge Issues
1. **HTTP requests failing**:
   - Check Node-RED HTTP input node configuration
   - Verify request format matches expected schema
   - Check response status in debug panel

2. **Data not normalized**:
   - Review normalization function logic
   - Check for JavaScript errors in function nodes
   - Validate input data format

### General Issues
1. **Flows not working**:
   - Re-import flows.json
   - Check all nodes are properly connected
   - Verify MQTT broker configuration

2. **Performance issues**:
   - Adjust polling intervals
   - Check system resources
   - Monitor Node-RED memory usage

## Integration

### With Edge Layer
- Automatically receives data from CoAP sensors
- Accepts HTTP POST requests from sensors
- Bridges protocols transparently

### With Cloud Layer
- Publishes normalized data to MQTT topics
- Cloud backend subscribes to these topics
- Provides consistent data format for processing