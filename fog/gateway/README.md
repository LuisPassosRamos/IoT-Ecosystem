# Fog Layer Gateway

This directory contains an optional Node.js/Express gateway for the Fog layer.

## Purpose

While the main Fog layer functionality is implemented in Node-RED (CoAP→MQTT bridging), this gateway can provide additional services:

- REST API endpoints for Fog layer management
- Additional data processing and filtering
- Local caching and buffering
- Custom protocol adaptations

## Implementation

The gateway is optional and not required for basic functionality. The Node-RED flows handle the core bridging requirements.

## Potential Features

If implemented, the gateway could include:

```javascript
// Example Express.js gateway structure
const express = require('express');
const app = express();

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', layer: 'fog' });
});

// Bridge status endpoint
app.get('/bridge/status', (req, res) => {
    // Return Node-RED bridge status
});

// Local sensor cache endpoint
app.get('/sensors/local', (req, res) => {
    // Return cached sensor data
});

app.listen(3001, () => {
    console.log('Fog gateway running on port 3001');
});
```

## Configuration

Environment variables for the gateway:
- `FOG_GATEWAY_PORT`: Port for the gateway (default: 3001)
- `NODE_RED_URL`: Node-RED instance URL
- `MQTT_HOST`: MQTT broker hostname
- `CACHE_DURATION`: Data cache duration in seconds

## Integration

The gateway would integrate with:
- Node-RED flows for bridge management
- MQTT broker for data access
- Cloud backend for upstream communication
- Local CoAP sensors for direct access