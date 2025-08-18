# Fog Layer

The Fog layer provides edge intelligence and protocol bridging between IoT devices and the cloud backend.

## Components

### Node-RED Flows
- **flows.json**: Complete Node-RED flow configuration for CoAP→MQTT bridging
- Polls CoAP sensors every 5-7 seconds
- Normalizes data formats between protocols
- Implements basic anomaly detection at the fog level
- Publishes bridged data to MQTT topics

### Gateway (Optional)
- **gateway/**: Optional Node.js/Express gateway for additional fog services
- Currently contains documentation for potential implementation
- Not required for core functionality

## Features

### Protocol Bridging
- **CoAP to MQTT**: Automatic bridging of CoAP sensor data to MQTT
- **Data Normalization**: Converts different sensor data formats to standardized JSON
- **Protocol Translation**: Handles protocol-specific features and limitations

### Edge Intelligence
- **Anomaly Detection**: Basic threshold-based anomaly detection at fog level
- **Data Filtering**: Filters out invalid or corrupted sensor readings
- **Status Monitoring**: Monitors CoAP sensor health and availability

### Error Handling
- **Robust Error Management**: Comprehensive error catching and reporting
- **Automatic Retry**: Retry mechanisms for failed CoAP requests
- **Error Logging**: Publishes errors to MQTT for monitoring

## Node-RED Flow Structure

### Temperature Bridge Flow
1. **Inject Node**: Triggers every 5 seconds
2. **CoAP Request**: Fetches temperature from CoAP sensor
3. **JSON Parser**: Parses CoAP response
4. **Normalizer Function**: Normalizes data format and detects anomalies
5. **MQTT Publisher**: Publishes to `sensors/temperature/fog_bridge`

### Humidity Bridge Flow
1. **Inject Node**: Triggers every 7 seconds
2. **CoAP Request**: Fetches humidity from CoAP sensor
3. **JSON Parser**: Parses CoAP response
4. **Normalizer Function**: Normalizes data format and detects anomalies
5. **MQTT Publisher**: Publishes to `sensors/humidity/fog_bridge`

### Status Monitoring Flow
1. **Inject Node**: Triggers every 30 seconds
2. **CoAP Request**: Fetches status from CoAP sensor
3. **JSON Parser**: Parses status response
4. **Status Processor**: Processes bridge and sensor status
5. **MQTT Publisher**: Publishes to `fog/bridge/status`

### Error Handling Flow
1. **Catch Node**: Catches all errors in the flow
2. **Error Processor**: Formats error information
3. **MQTT Publisher**: Publishes errors to `fog/bridge/errors`
4. **Debug**: Logs errors for troubleshooting

## Data Format

### Input (CoAP)
```json
{
  "ts": "2024-01-01T12:00:00Z",
  "type": "temperature",
  "value": 25.3,
  "unit": "celsius",
  "sensor_id": "coap_temp_001",
  "origin": "coap",
  "protocol": "coap"
}
```

### Output (MQTT)
```json
{
  "ts": "2024-01-01T12:00:00Z",
  "type": "temperature",
  "value": 25.3,
  "unit": "celsius",
  "sensor_id": "coap_temp_001_fog",
  "origin": "fog",
  "protocol": "coap_bridge",
  "anomaly": false,
  "bridge_timestamp": "2024-01-01T12:00:01Z",
  "original_payload": { /* original CoAP data */ }
}
```

## Configuration

### MQTT Broker Configuration
- **Host**: `mosquitto` (Docker service name)
- **Port**: `1883`
- **Client ID**: `node-red-fog-bridge`
- **QoS**: `1` for reliable delivery

### CoAP Endpoints
- **Temperature**: `coap://coap_sensor:5683/temperature`
- **Humidity**: `coap://coap_sensor:5683/humidity`
- **Status**: `coap://coap_sensor:5683/status`

### Polling Intervals
- **Temperature**: Every 5 seconds
- **Humidity**: Every 7 seconds
- **Status**: Every 30 seconds

### Anomaly Thresholds
- **Temperature**: 15-35°C range
- **Humidity**: 30-90% range

## MQTT Topics

### Published Topics
- `sensors/temperature/fog_bridge`: Bridged temperature data
- `sensors/humidity/fog_bridge`: Bridged humidity data
- `fog/bridge/status`: Bridge and sensor status
- `fog/bridge/errors`: Error reports

### Status Messages
- **Online**: Published on connection with retain flag
- **Offline**: Published on clean disconnect with retain flag  
- **Disconnected**: Published as Last Will Testament

## Installation

### Node-RED Setup
1. Import the flows.json file into Node-RED
2. Install required nodes:
   - `node-red-contrib-coap`: For CoAP client functionality
   - `node-red-contrib-mqtt-broker`: MQTT broker integration
3. Configure MQTT broker connection
4. Deploy the flows

### Docker Integration
The Node-RED service is configured in docker-compose.yml:
```yaml
node-red:
  image: nodered/node-red:latest
  ports:
    - "1880:1880"
  volumes:
    - ./fog/node-red/flows.json:/data/flows.json
```

## Monitoring

### Node-RED Dashboard
- Access Node-RED editor at `http://localhost:1880`
- Monitor flow execution and debug messages
- View real-time data processing

### MQTT Monitoring
Subscribe to monitoring topics:
```bash
# Bridge status
mosquitto_sub -h localhost -t "fog/bridge/status"

# Error reports  
mosquitto_sub -h localhost -t "fog/bridge/errors"

# Bridged sensor data
mosquitto_sub -h localhost -t "sensors/+/fog_bridge"
```

## Troubleshooting

### Common Issues
1. **CoAP Connection Failed**: Check if CoAP sensor is running
2. **MQTT Connection Failed**: Verify MQTT broker is accessible
3. **Missing Data**: Check Node-RED debug panel for errors
4. **High Error Rate**: Review CoAP sensor status and network connectivity

### Debug Mode
Enable debug nodes in Node-RED to see detailed message flow and identify issues.

## Integration

The Fog layer integrates with:
- **Edge Layer**: Polls CoAP sensors for data
- **Cloud Backend**: Forwards processed data via MQTT
- **Monitoring**: Provides status and error reporting