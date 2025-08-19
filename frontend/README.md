# Painel Frontend

Este diretório contém o dashboard web para visualizar dados de sensores IoT em tempo real.

## Componentes

### Arquivos Centrais
- **index.html**: Main dashboard page with responsive layout
- **app.js**: JavaScript application logic and WebSocket handling
- **charts/chart-utils.js**: Chart.js utilities and helper functions

### Recursos
- **Gráficos em Tempo Real**: Live updating charts for temperature, humidity, and luminosity
- **Integração WebSocket**: Real-time data streaming from backend
- **Comparação com Clima**: Compare local sensors with external weather data
- **Alertas de Anomalia**: Visual alerts for sensor anomalies
- **Design Responsivo**: Works on desktop, tablet, and mobile devices
- **Status do Sistema**: Monitor MQTT, backend, and sensor health

## Stack de Tecnologia

### Bibliotecas Frontend
- **Chart.js**: Real-time data visualization
- **Bootstrap 5**: Responsive UI framework
- **Font Awesome**: Icons and visual indicators
- **Vanilla JavaScript**: No framework dependencies

### Comunicação
- **WebSocket**: Real-time data streaming
- **REST API**: Historical data and configuration
- **MQTT over WebSocket**: Direct MQTT browser client (optional)

## Layout do Dashboard

### Seção de Cabeçalho
- **Título**: IoT Ecosystem Dashboard
- **Status da Conexão**: Real-time connection indicator
- **Última Atualização**: Timestamp of most recent data

### Cards de Status
- **Temperatura**: Current reading, status, and sensor count
- **Umidade**: Current reading, status, and sensor count  
- **Luminosidade**: Current reading, status, and sensor count
- **Clima**: External weather data for comparison

### Seção de Gráficos
- **Gráfico de Temperatura**: Real-time line chart with 50 data points
- **Gráfico de Umidade**: Real-time line chart with 50 data points
- **Gráfico de Luminosidade**: Real-time line chart with 50 data points

### Alertas e Comparação
- **Alertas Recentes**: List of anomalies and system alerts
- **Comparação com Clima**: Side-by-side sensor vs weather data

### Status do Sistema
- **Status do MQTT**: Broker connection status
- **Sensores Ativos**: Number of reporting sensors
- **Total de Leituras**: Count of stored readings
- **Taxa de Anomalia**: Percentage of anomalous readings

## Setup

### Servindo Arquivos Estáticos
O frontend é servido como arquivos estáticos através de:

1. **Container Nginx** (recomendado):
   ```yaml
   # docker-compose.yml
   frontend:
     image: nginx:alpine
     ports:
       - "8080:80"
     volumes:
       - ./frontend:/usr/share/nginx/html:ro
   ```

2. **Arquivos Estáticos do Backend** (alternativa):
   ```python
   # In FastAPI main.py
   app.mount("/", StaticFiles(directory="frontend"), name="frontend")
   ```

3. **Servidor de Desenvolvimento** (local):
   ```bash
   cd frontend
   python -m http.server 8080
   ```

### URLs de Acesso
- **Dashboard**: http://localhost:8080
- **Backend API**: http://localhost:8000
- **Node-RED**: http://localhost:1880

## Configuração

### Conexão com Backend
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

### Configurações do Gráfico
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

## Recursos em Tempo Real

### Conexão WebSocket
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

### Processamento de Dados
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

### Atualizações de Gráfico
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

## Recursos Visuais

### Indicadores de Status
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

### Alertas de Anomalia
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

### Comparação com Clima
```javascript
updateWeatherComparison(comparison) {
    const { weather, sensor, differences, alerts } = comparison;
    
    let html = `
        <div class="row">
            <div class="col-md-6">
                <h6>Sensor Local</h6>
                <ul>
                    <li>Temperatura: ${sensor.temperature}°C</li>
                    <li>Umidade: ${sensor.humidity}%</li>
                </ul>
            </div>
            <div class="col-md-6">
                <h6>API de Clima</h6>
                <ul>
                    <li>Temperatura: ${weather.temperature}°C</li>
                    <li>Umidade: ${weather.humidity}%</li>
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

## Exibição de Dados

### Cards de Sensor
```html
<div class="card text-center">
    <div class="card-body">
        <i class="fas fa-thermometer-half fa-2x text-danger mb-2"></i>
        <h5 class="card-title">Temperatura</h5>
        <h3 class="text-primary" id="currentTemp">--°C</h3>
        <small class="text-muted" id="tempStatus">Aguardando dados...</small>
    </div>
</div>
```

### Containers de Gráfico
```html
<div class="card sensor-card">
    <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
            <i class="fas fa-thermometer-half text-danger me-2"></i>
            Temperatura
        </h5>
        <span class="badge bg-secondary" id="tempCount">0 leituras</span>
    </div>
    <div class="card-body">
        <div class="chart-container">
            <canvas id="temperatureChart"></canvas>
        </div>
    </div>
</div>
```

## Integração com API

### Chamadas REST
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

### Tratamento de Erros
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

## Otimização de Desempenho

### Atualizações Eficientes
- **WebSocket com Limitação**: Limit update frequency to prevent UI flooding
- **Desativar Animações de Gráfico**: Disable animations for real-time updates
- **Limites de Dados**: Cap chart data points to prevent memory issues
- **Carregamento Preguiçoso**: Load historical data only when needed

### Gerenciamento de Memória
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

## Design Responsivo

### Breakpoints
- **Mobile**: < 768px (stacked layout)
- **Tablet**: 768px - 1024px (2-column layout)
- **Desktop**: > 1024px (3-column layout)

### Otimizações para Mobile
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

## Customização

### Adicionar Novos Tipos de Gráfico
1. Create new chart in `initializeCharts()`
2. Add chart container in HTML
3. Handle data updates in WebSocket message handler
4. Style chart according to sensor type

### Modificar Aparência do Gráfico
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

### Adicionar Novos Widgets
1. Create HTML structure
2. Add JavaScript logic in dashboard class
3. Connect to WebSocket data stream
4. Style with CSS

## Solução de Problemas

### Problemas Comuns
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

### Ferramentas de Debug
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

### Console do Navegador
Use browser developer tools to:
- Monitor network requests
- Debug JavaScript errors
- Inspect WebSocket messages
- View performance metrics
- Test responsive design