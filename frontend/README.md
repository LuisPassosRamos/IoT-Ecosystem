# Frontend Dashboard

Real-time IoT sensor monitoring dashboard built with vanilla JavaScript and Chart.js.

## Features

### Real-time Data Visualization
- **Chart.js Integration**: Interactive charts for temperature, humidity, and luminosity
- **Live Updates**: WebSocket connection for real-time sensor data streaming
- **Anomaly Alerts**: Visual indicators and notifications for anomalous readings
- **Historical Data**: Load and display sensor history with configurable time ranges

### Interactive Dashboard
- **Responsive Design**: Mobile-friendly layout with CSS Grid
- **Dark/Light Theme**: Automatic theme detection and manual toggle
- **Status Indicators**: Real-time connection status for MQTT, WebSocket, and API
- **Control Panel**: Start/stop real-time updates, refresh data, configure settings

### Weather Comparison
- **External API Integration**: Compare local sensors with OpenWeatherMap data
- **Discrepancy Alerts**: Highlight significant differences between local and external data
- **City Selection**: Configurable city for weather comparison
- **Threshold Configuration**: Adjustable alert thresholds

## Architecture

### Frontend Components
```
frontend/
├── index.html              # Main dashboard page
├── app.js                  # Main application logic
├── charts/
│   └── chart-utils.js      # Chart.js utilities and management
└── README.md              # This file
```

### Technology Stack
- **HTML5**: Semantic markup with accessibility features
- **CSS3**: Modern styling with Grid, Flexbox, and animations
- **JavaScript ES6+**: Vanilla JavaScript with async/await
- **Chart.js**: Professional charting library for data visualization
- **WebSocket API**: Real-time bidirectional communication

## Data Flow

```
Sensors → MQTT → Backend → WebSocket → Frontend Charts
                    ↓
               REST API ← Frontend Controls
                    ↓
            External APIs ← Weather Comparison
```

### WebSocket Messages
```javascript
// Connection established
{
  "type": "connection_established",
  "data": {
    "message": "Connected to IoT-Ecosystem real-time stream",
    "features": ["sensor_data", "system_status", "anomaly_alerts"]
  }
}

// Real-time sensor data
{
  "type": "sensor_data",
  "data": {
    "sensor_type": "temperature",
    "value": 25.3,
    "anomaly": false,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}

// Heartbeat
{
  "type": "ping",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Chart Configuration

### Chart Types
- **Line Charts**: Time-series data with smooth curves
- **Point Markers**: Individual data points with hover details
- **Anomaly Indicators**: Special markers for anomalous readings
- **Real-time Updates**: Streaming data with automatic scaling

### Chart Features
```javascript
// Chart configuration example
{
  type: 'line',
  data: {
    datasets: [{
      label: 'Temperature (°C)',
      borderColor: 'rgba(255, 99, 132, 1)',
      backgroundColor: 'rgba(255, 99, 132, 0.1)',
      tension: 0.4,
      fill: true
    }, {
      label: 'Anomalies',
      pointStyle: 'triangle',
      pointRadius: 8,
      showLine: false
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      x: { type: 'time' },
      y: { beginAtZero: false }
    }
  }
}
```

## API Integration

### REST Endpoints
```javascript
// Get latest readings
GET /api/v1/sensors/latest

// Get historical data
GET /api/v1/sensors/history?limit=100&sensor_type=temperature

// Authentication
POST /api/v1/auth/login
{
  "username": "admin",
  "password": "password123"
}

// Weather comparison
GET /api/v1/external/weather?city=London
```

### Error Handling
```javascript
class IoTDashboard {
  async loadData() {
    try {
      const response = await fetch('/api/v1/sensors/latest');
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      this.updateCharts(data);
    } catch (error) {
      this.showError(`Failed to load data: ${error.message}`);
      this.scheduleRetry();
    }
  }
}
```

## Real-time Updates

### WebSocket Connection Management
```javascript
class IoTDashboard {
  connectWebSocket() {
    this.websocket = new WebSocket('ws://localhost:8000/ws');
    
    this.websocket.onopen = () => {
      console.log('WebSocket connected');
      this.updateConnectionStatus('ws', true);
    };
    
    this.websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleWebSocketMessage(message);
    };
    
    this.websocket.onclose = () => {
      console.log('WebSocket disconnected');
      this.scheduleReconnect();
    };
  }
}
```

### Auto-reconnection
- **Exponential Backoff**: Increasing delay between reconnection attempts
- **Max Attempts**: Configurable maximum reconnection attempts
- **Status Indicators**: Visual feedback for connection state
- **Manual Retry**: User-initiated reconnection option

## User Interface

### Dashboard Layout
```css
.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
}

.chart-container {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 15px;
  backdrop-filter: blur(10px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}
```

### Responsive Design
- **Mobile-First**: Optimized for mobile devices
- **Breakpoints**: Tablet and desktop layouts
- **Touch-Friendly**: Large buttons and touch targets
- **Accessible**: ARIA labels and keyboard navigation

### Status Indicators
```javascript
// Connection status colors
.status-connected { background-color: #4CAF50; }    // Green
.status-disconnected { background-color: #f44336; } // Red  
.status-warning { background-color: #ff9800; }      // Orange
```

## Configuration

### Environment Variables
```javascript
// API configuration
const config = {
  apiBaseUrl: window.location.origin + '/api',
  wsUrl: `ws://${window.location.host}/ws`,
  refreshInterval: 30000,
  maxReconnectAttempts: 5,
  reconnectDelay: 5000
};
```

### Chart Settings
```javascript
// Chart display settings
const chartConfig = {
  maxDataPoints: 50,
  updateInterval: 1000,
  anomalyHighlight: true,
  smoothCurves: true,
  showAnimations: true
};
```

## Development

### Local Development
```bash
# Serve static files with Python
cd frontend
python3 -m http.server 3000

# Or with Node.js
npx http-server -p 3000 -c-1

# Or use the full Docker setup
docker-compose up frontend
```

### Debug Mode
```javascript
// Enable debug logging
localStorage.setItem('iot-debug', 'true');

// View WebSocket messages
window.addEventListener('iot-websocket-message', (event) => {
  console.log('WebSocket:', event.detail);
});
```

### Performance Monitoring
```javascript
// Monitor chart performance
class ChartPerformanceMonitor {
  measureChartUpdate(chartType, startTime) {
    const duration = performance.now() - startTime;
    if (duration > 100) {
      console.warn(`Slow chart update: ${chartType} took ${duration}ms`);
    }
  }
}
```

## Browser Compatibility

### Supported Browsers
- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

### Polyfills
```html
<!-- For older browsers -->
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6,fetch,Promise"></script>
```

### Progressive Enhancement
- **Core Functionality**: Works without JavaScript (basic HTML)
- **Enhanced Experience**: Real-time updates with JavaScript
- **Offline Support**: Service worker for basic offline functionality

## Security

### Content Security Policy
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' https://cdn.jsdelivr.net; 
               connect-src 'self' ws: wss:;">
```

### XSS Prevention
```javascript
// Sanitize user input
function sanitizeInput(input) {
  const div = document.createElement('div');
  div.textContent = input;
  return div.innerHTML;
}
```

## Deployment

### Production Build
```bash
# Minify CSS and JavaScript
npm install -g clean-css-cli uglify-js

# Minify files
cleancss -o style.min.css style.css
uglifyjs app.js charts/chart-utils.js -o app.min.js
```

### NGINX Configuration
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host $host;
    }
    
    location /ws {
        proxy_pass http://backend:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### CDN Integration
```html
<!-- Production CDN resources -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
```

## Monitoring

### Analytics
```javascript
// Track user interactions
function trackEvent(category, action, label) {
  if (window.gtag) {
    gtag('event', action, {
      event_category: category,
      event_label: label
    });
  }
}
```

### Error Tracking
```javascript
// Report errors to monitoring service
window.addEventListener('error', (event) => {
  const errorReport = {
    message: event.message,
    filename: event.filename,
    lineno: event.lineno,
    colno: event.colno,
    timestamp: new Date().toISOString()
  };
  
  // Send to monitoring service
  sendErrorReport(errorReport);
});
```

## Accessibility

### ARIA Labels
```html
<div class="chart-container" role="img" aria-label="Temperature sensor data chart">
  <canvas id="temperature-chart" aria-describedby="temp-description"></canvas>
  <div id="temp-description" class="sr-only">
    Real-time temperature readings from sensor network
  </div>
</div>
```

### Keyboard Navigation
```javascript
// Enable keyboard controls
document.addEventListener('keydown', (event) => {
  if (event.key === 'r' && event.ctrlKey) {
    event.preventDefault();
    this.refreshData();
  }
});
```

This frontend provides a comprehensive, real-time dashboard for monitoring IoT sensor data with professional-grade features and user experience.