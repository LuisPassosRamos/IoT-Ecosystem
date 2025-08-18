# Frontend Dashboard

This directory contains the web-based dashboard for visualizing IoT sensor data in real-time.

## Components

### Core Files
- **index.html**: Main dashboard page with responsive layout
- **app.js**: JavaScript application logic and WebSocket handling
- **charts/chart-utils.js**: Chart.js utilities and helper functions

### Features
- **Real-time Charts**: Live updating charts for temperature, humidity, and luminosity
- **WebSocket Integration**: Real-time data streaming from backend
- **Weather Comparison**: Compare local sensors with external weather data
- **Anomaly Alerts**: Visual alerts for sensor anomalies
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **System Status**: Monitor MQTT, backend, and sensor health

## Technology Stack

### Frontend Libraries
- **Chart.js**: Real-time data visualization
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icons and visual indicators
- **Vanilla JavaScript**: No framework dependencies

### Communication
- **WebSocket**: Real-time data streaming
- **REST API**: Historical data and configuration
- **MQTT over WebSocket**: Direct MQTT browser client (optional)

## Dashboard Layout

### Header Section
- **Title**: IoT Ecosystem Dashboard
- **Connection Status**: Real-time connection indicator
- **Last Update**: Timestamp of most recent data

### Status Cards
- **Temperature**: Current reading, status, and sensor count
- **Humidity**: Current reading, status, and sensor count  
- **Luminosity**: Current reading, status, and sensor count
- **Weather**: External weather data for comparison

### Charts Section
- **Temperature Chart**: Real-time line chart with 50 data points
- **Humidity Chart**: Real-time line chart with 50 data points
- **Luminosity Chart**: Real-time line chart with 50 data points

### Alerts and Comparison
- **Recent Alerts**: List of anomalies and system alerts
- **Weather Comparison**: Side-by-side sensor vs weather data

### System Status
- **MQTT Status**: Broker connection status
- **Active Sensors**: Number of reporting sensors
- **Total Readings**: Count of stored readings
- **Anomaly Rate**: Percentage of anomalous readings

## Setup

### Static File Serving
The frontend is served as static files through:

1. **Nginx Container** (recommended):
   ```yaml
   # docker-compose.yml
   frontend:
     image: nginx:alpine
     ports:
       - "8080:80"
     volumes:
       - ./frontend:/usr/share/nginx/html:ro
   ```

2. **Backend Static Files** (alternative):
   ```python
   # In FastAPI main.py
   app.mount("/", StaticFiles(directory="frontend"), name="frontend")
   ```

3. **Development Server** (local):
   ```bash
   cd frontend
   python -m http.server 8080
   ```

### Access URLs
- **Dashboard**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Node-RED**: http://localhost:1880

## Configuration

### Backend Connection
```javascript
// app.js configuration
const config = {
    backendUrl: 'http://localhost:8000',
    websocketUrl: 'ws://localhost:8000/ws',
    updateInterval: 10000,        // 10 seconds
    maxDataPoints: 50,           // Chart data points
    weatherUpdateInterval: 300000 // 5 minutes
};
```

### Chart Settings
```javascript
// Chart.js configuration
const chartConfig = {
    responsive: true,
    maintainAspectRatio: false,
    animation: {
        duration: 750,
        easing: 'easeInOutQuart'
    },
    scales: {
        x: { 
            display: true,
            title: { text: 'Time' }
        },
        y: { 
            display: true,
            beginAtZero: false 
        }
    }
};
```

## Real-time Features

### WebSocket Connection
```javascript
class IoTDashboard {
    connectWebSocket() {
        this.websocket = new WebSocket(this.config.websocketUrl);
        
        this.websocket.onopen = () => {
            console.log('WebSocket connected');
            this.updateConnectionStatus(true);
        };
        
        this.websocket.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleWebSocketMessage(message);
        };
        
        this.websocket.onclose = () => {
            console.log('WebSocket disconnected');
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        };
    }
}
```

### Data Processing
```javascript
handleSensorDataMessage(data) {
    const { sensor_type, value, timestamp, anomaly } = data;
    
    // Update current reading display
    this.updateSingleSensorReading(sensor_type, data);
    
    // Add to real-time chart
    if (this.charts[sensor_type]) {
        const timeLabel = ChartUtils.formatTimestamp(timestamp);
        ChartUtils.addSingleDataPoint(
            this.charts[sensor_type], 
            timeLabel, 
            value, 
            this.config.maxDataPoints
        );
    }
    
    // Show anomaly alert
    if (anomaly) {
        this.showAnomalyAlert(data);
    }
}
```

### Chart Updates
```javascript
// ChartUtils.addSingleDataPoint
static addSingleDataPoint(chart, label, value, maxDataPoints = 50) {
    chart.data.labels.push(label);
    chart.data.datasets[0].data.push(value);
    
    // Remove old data points
    if (chart.data.labels.length > maxDataPoints) {
        chart.data.labels.shift();
        chart.data.datasets[0].data.shift();
    }
    
    chart.update('none'); // Update without animation
}
```

## Visual Features

### Status Indicators
```css
.status-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}

.status-connected {
    background-color: #28a745;
    animation: pulse 2s infinite;
}

.status-disconnected {
    background-color: #dc3545;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}
```

### Anomaly Alerts
```javascript
createAnomalyAlert(reading) {
    const alertColor = reading.anomaly ? 'alert-danger' : 'alert-success';
    const iconClass = reading.anomaly ? 'fa-exclamation-triangle' : 'fa-check-circle';
    const status = reading.anomaly ? 'ANOMALY' : 'NORMAL';
    
    return `
        <div class="alert ${alertColor} alert-dismissible fade show">
            <i class="fas ${iconClass} me-2"></i>
            <strong>${status}:</strong> 
            ${reading.sensor_type} sensor reading: ${reading.value} ${reading.unit}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}
```

### Weather Comparison
```javascript
updateWeatherComparison(comparison) {
    const { weather, sensor, differences, alerts } = comparison;
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6>Local Sensors</h6>
                <ul>
                    <li>Temperature: ${sensor.temperature}°C</li>
                    <li>Humidity: ${sensor.humidity}%</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>Weather API</h6>
                <ul>
                    <li>Temperature: ${weather.temperature}°C</li>
                    <li>Humidity: ${weather.humidity}%</li>
                </ul>
            </div>
        </div>
    `;
    
    // Add alerts if differences are significant
    if (alerts && alerts.length > 0) {
        html += alerts.map(alert => `
            <div class="alert alert-warning">
                <i class="fas fa-exclamation-triangle"></i>
                ${alert.message}
            </div>
        `).join('');
    }
    
    document.getElementById('weatherComparison').innerHTML = html;
}
```

## Data Display

### Sensor Cards
```html
<div class="card text-center">
    <div class="card-body">
        <i class="fas fa-thermometer-half fa-2x text-danger mb-2"></i>
        <h5 class="card-title">Temperature</h5>
        <h3 class="text-primary" id="currentTemp">--°C</h3>
        <small class="text-muted" id="tempStatus">Waiting for data...</small>
    </div>
</div>
```

### Chart Containers
```html
<div class="card sensor-card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
            <i class="fas fa-thermometer-half text-danger me-2"></i>
            Temperature
        </h5>
        <span class="badge bg-secondary" id="tempCount">0 readings</span>
    </div>
    <div class="card-body">
        <div class="chart-container">
            <canvas id="temperatureChart"></canvas>
        </div>
    </div>
</div>
```

## API Integration

### REST API Calls
```javascript
async loadInitialData() {
    try {
        // Load latest sensor readings
        const response = await fetch(`${this.config.backendUrl}/v1/sensors/latest`);
        const data = await response.json();
        this.processSensorData(data);
        
        // Load historical data for charts
        await this.loadHistoricalData();
        
        // Load system stats
        await this.loadSystemStats();
        
    } catch (error) {
        console.error('Error loading initial data:', error);
        this.showError('Failed to load initial data', error.message);
    }
}
```

### Error Handling
```javascript
showError(title, message) {
    const alertHtml = `
        <div class="alert alert-danger alert-dismissible fade show">
            <i class="fas fa-exclamation-circle me-2"></i>
            <strong>${title}</strong><br>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', alertHtml);
}
```

## Performance Optimization

### Efficient Updates
- **Throttled WebSocket**: Limit update frequency to prevent UI flooding
- **Chart Animation**: Disable animations for real-time updates
- **Data Limits**: Cap chart data points to prevent memory issues
- **Lazy Loading**: Load historical data only when needed

### Memory Management
```javascript
// Limit chart data points
if (chart.data.labels.length > this.config.maxDataPoints) {
    chart.data.labels.splice(0, excess);
    chart.data.datasets[0].data.splice(0, excess);
}

// Clean up WebSocket connections
window.addEventListener('beforeunload', () => {
    if (this.websocket) {
        this.websocket.close();
    }
});
```

## Responsive Design

### Breakpoints
- **Mobile**: < 768px (stacked layout)
- **Tablet**: 768px - 1024px (2-column layout)
- **Desktop**: > 1024px (3-column layout)

### Mobile Optimizations
```css
@media (max-width: 767.98px) {
    .chart-container {
        height: 250px; /* Smaller charts on mobile */
    }
    
    .card {
        margin-bottom: 1rem;
    }
    
    .row {
        --bs-gutter-x: 0.5rem; /* Tighter spacing */
    }
}
```

## Customization

### Add New Chart Types
1. Create new chart in `initializeCharts()`
2. Add chart container in HTML
3. Handle data updates in WebSocket message handler
4. Style chart according to sensor type

### Modify Chart Appearance
```javascript
// Custom color schemes
static getColorForSensorType(sensorType) {
    const colors = {
        'temperature': '#e74c3c',  // Red
        'humidity': '#3498db',     // Blue
        'luminosity': '#f39c12',   // Orange
        'pressure': '#9b59b6',     // Purple
        'co2': '#27ae60'           // Green
    };
    return colors[sensorType] || '#95a5a6';
}
```

### Add New Widgets
1. Create HTML structure
2. Add JavaScript logic in dashboard class
3. Connect to WebSocket data stream
4. Style with CSS

## Troubleshooting

### Common Issues
1. **Charts not updating**:
   - Check WebSocket connection status
   - Verify backend is sending data
   - Check browser console for errors

2. **Data not loading**:
   - Verify backend API is accessible
   - Check CORS configuration
   - Confirm sensor data is being generated

3. **WebSocket connection failed**:
   - Check backend WebSocket endpoint
   - Verify network connectivity
   - Check firewall settings

### Debug Tools
```javascript
// Enable debug mode
window.DEBUG = true;

// Monitor WebSocket messages
this.websocket.onmessage = (event) => {
    if (window.DEBUG) {
        console.log('WebSocket message:', JSON.parse(event.data));
    }
    this.handleWebSocketMessage(JSON.parse(event.data));
};

// Monitor API calls
const originalFetch = window.fetch;
window.fetch = function(...args) {
    if (window.DEBUG) {
        console.log('API call:', args[0]);
    }
    return originalFetch.apply(this, args);
};
```

### Browser Console
Use browser developer tools to:
- Monitor network requests
- Debug JavaScript errors
- Inspect WebSocket messages
- View performance metrics
- Test responsive design