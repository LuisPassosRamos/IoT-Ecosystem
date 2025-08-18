# Edge Layer - Sensor Simulators

This directory contains sensor simulators that represent the edge layer of the IoT ecosystem.

## Components

### MQTT Sensors
- **temp_sensor.py**: Temperature sensor with anomaly detection
- **humidity_sensor.py**: Humidity sensor with anomaly detection  
- **luminosity_sensor.py**: Light sensor with anomaly detection

### CoAP Sensors
- **coap_sensor.py**: CoAP-based environmental sensor simulator

## Features

### Anomaly Detection
All sensors implement intelligent anomaly detection:

- **Range-based**: Values outside normal operating ranges
- **Jump-based**: Sudden changes beyond thresholds
- **Statistical**: Deviation from expected patterns

### MQTT Publishing
Sensors publish to structured topics:
```
sensors/{sensor_type}/{sensor_id}
```

### Realistic Data Generation
- Time-based variations (day/night cycles for luminosity)
- Gradual changes with occasional anomalies
- Configurable normal ranges and thresholds

## Running Sensors

### Prerequisites
```bash
pip install paho-mqtt aiocoap
```

### Environment Variables
```bash
export MQTT_HOST=localhost
export MQTT_PORT=1883
```

### Start Individual Sensors
```bash
# Temperature sensor
python sensors/temp_sensor.py

# Humidity sensor  
python sensors/humidity_sensor.py

# Luminosity sensor
python sensors/luminosity_sensor.py

# CoAP sensor (separate terminal)
python coap_simulator/coap_sensor.py
```

### Testing with MQTT Client
```bash
# Subscribe to all sensor data
mosquitto_sub -h localhost -t "sensors/+/+"

# Subscribe to specific sensor type
mosquitto_sub -h localhost -t "sensors/temperature/+"

# Subscribe to anomalies only
mosquitto_sub -h localhost -t "sensors/+/+" | grep '"anomaly":true'
```

### Testing CoAP Sensor
```bash
# Install CoAP client
pip install aiocoap[all]

# Test environmental data
coap-client -m get coap://localhost:5683/sensor

# Test temperature only
coap-client -m get coap://localhost:5683/temperature

# Resource discovery
coap-client -m get coap://localhost:5683/.well-known/core
```

## Sensor Configuration

### Temperature Sensor
- **Normal Range**: 18°C to 32°C
- **Anomaly Threshold**: ±5°C sudden change
- **Update Interval**: 2 seconds
- **Topic**: `sensors/temperature/temp-001`

### Humidity Sensor  
- **Normal Range**: 30% to 80%
- **Anomaly Threshold**: ±15% sudden change
- **Update Interval**: 3 seconds
- **Topic**: `sensors/humidity/hum-001`

### Luminosity Sensor
- **Normal Range**: 100 to 2000 lux
- **Anomaly Threshold**: ±500 lux sudden change
- **Update Interval**: 4 seconds
- **Topic**: `sensors/luminosity/lum-001`
- **Special**: Day/night cycle simulation

### CoAP Environmental Sensor
- **Combined Data**: Temperature, humidity, pressure
- **Update**: On-demand (CoAP GET requests)
- **Port**: 5683
- **Resources**: `/sensor`, `/temperature`

## Data Format

### MQTT Payload
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

### CoAP Payload
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

## Integration

### With Fog Layer
Sensors automatically connect to the MQTT broker, which Node-RED subscribes to for data processing and forwarding.

### With Cloud Layer
The cloud backend subscribes to all sensor topics and stores data in the database while forwarding real-time updates via WebSocket.

## Monitoring

### Debug Output
All sensors print their published data to console:
```
[NORMAL] Published: {"ts": "2024-01-01T12:00:00Z", "type": "temperature", "value": 23.5, ...}
[ANOMALY] Published: {"ts": "2024-01-01T12:05:00Z", "type": "temperature", "value": 45.2, "anomaly": true, ...}
```

### Health Checks
- MQTT connection status
- Publishing success/failure
- Anomaly detection triggers

## Customization

### Modify Sensor Ranges
Edit the constants in each sensor file:
```python
# Temperature sensor
NORMAL_RANGE = (18.0, 32.0)  # Min, Max °C
ANOMALY_THRESHOLD = 5.0      # °C jump threshold
UPDATE_INTERVAL = 2          # seconds
```

### Add New Sensor Types
1. Copy existing sensor file
2. Modify sensor parameters
3. Update topic and sensor ID
4. Implement specific logic for the new sensor type

### Environment-Specific Behavior
Sensors can be configured for different environments:
- Indoor vs outdoor ranges
- Geographic location adjustments
- Seasonal variations
- Industrial vs residential settings

## Troubleshooting

### Connection Issues
```bash
# Test MQTT broker connectivity
mosquitto_pub -h localhost -t test -m "hello"

# Check if broker is running
docker-compose ps mosquitto
```

### Permission Errors
```bash
# Ensure Python can access network
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/python3
```

### Data Not Appearing
1. Check MQTT broker is running
2. Verify topic subscriptions
3. Check firewall settings
4. Validate JSON format in console output