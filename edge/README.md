# Edge Layer Sensors

This directory contains the edge layer sensors and simulators for the IoT-Ecosystem project.

## Components

### MQTT Sensors
- **temp_sensor.py**: Temperature sensor simulator with anomaly detection
- **humidity_sensor.py**: Humidity sensor simulator with anomaly detection  
- **luminosity_sensor.py**: Luminosity sensor simulator with anomaly detection

### CoAP Simulator
- **coap_sensor.py**: CoAP server that provides temperature and humidity readings

## Features

### Anomaly Detection
All MQTT sensors implement intelligent anomaly detection:
- **Range-based**: Values outside configured min/max thresholds
- **Jump-based**: Sudden changes exceeding configured jump thresholds
- **Configurable**: Thresholds set via environment variables

### Data Format
All sensors publish standardized JSON payloads:
```json
{
  "ts": "2024-01-01T12:00:00Z",
  "type": "temperature",
  "value": 25.3,
  "unit": "celsius",
  "sensor_id": "temp_sim_001", 
  "origin": "edge",
  "anomaly": false
}
```

When anomalies are detected, additional details are included:
```json
{
  "anomaly": true,
  "anomaly_details": {
    "out_of_range": false,
    "sudden_jump": true,
    "previous_value": 22.1
  }
}
```

## Running the Sensors

### Prerequisites
```bash
pip install paho-mqtt aiocoap
```

### MQTT Sensors
```bash
# Set environment variables (optional)
export MQTT_HOST=localhost
export MQTT_PORT=1883

# Run individual sensors
python3 sensors/temp_sensor.py
python3 sensors/humidity_sensor.py  
python3 sensors/luminosity_sensor.py
```

### CoAP Simulator
```bash
# Run CoAP server
python3 coap_simulator/coap_sensor.py

# Test CoAP endpoints
coap-client -m get coap://localhost:5683/temperature
coap-client -m get coap://localhost:5683/humidity
coap-client -m get coap://localhost:5683/status
```

## Configuration

### Environment Variables
- `MQTT_HOST`: MQTT broker hostname (default: localhost)
- `MQTT_PORT`: MQTT broker port (default: 1883)
- `TEMP_MIN/MAX`: Temperature thresholds (default: 15.0/35.0°C)
- `TEMP_JUMP_THRESHOLD`: Temperature jump threshold (default: 5.0°C)
- `HUMIDITY_MIN/MAX`: Humidity thresholds (default: 30.0/90.0%)
- `HUMIDITY_JUMP_THRESHOLD`: Humidity jump threshold (default: 20.0%)
- `LUMINOSITY_MIN/MAX`: Luminosity thresholds (default: 0.0/1000.0 lux)
- `LUMINOSITY_JUMP_THRESHOLD`: Luminosity jump threshold (default: 200.0 lux)
- `COAP_HOST`: CoAP server host (default: localhost)
- `COAP_PORT`: CoAP server port (default: 5683)

### MQTT Topics
- Temperature: `sensors/temperature/sim001`
- Humidity: `sensors/humidity/sim001`  
- Luminosity: `sensors/luminosity/sim001`

## Integration

These sensors integrate with:
- **Fog Layer**: Node-RED flows bridge CoAP to MQTT
- **Cloud Backend**: FastAPI service subscribes to MQTT topics
- **Frontend**: Real-time dashboard displays sensor data