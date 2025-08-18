/**
 * IoT Dashboard Main Application
 */

class IoTDashboard {
    constructor() {
        this.config = {
            backendUrl: window.location.hostname === 'localhost' 
                ? 'http://localhost:8000' 
                : `${window.location.protocol}//${window.location.hostname}:8000`,
            websocketUrl: window.location.hostname === 'localhost'
                ? 'ws://localhost:8000/ws'
                : `ws://${window.location.hostname}:8000/ws`,
            updateInterval: 10000, // 10 seconds
            maxDataPoints: 50,
            weatherUpdateInterval: 300000 // 5 minutes
        };
        
        this.charts = {};
        this.websocket = null;
        this.isConnected = false;
        this.lastUpdate = null;
        this.retryCount = 0;
        this.maxRetries = 5;
        
        this.sensorData = {
            temperature: [],
            humidity: [],
            luminosity: []
        };
        
        this.init();
    }

    async init() {
        console.log('Initializing IoT Dashboard...');
        
        // Initialize charts
        this.initializeCharts();
        
        // Start periodic updates
        this.startPeriodicUpdates();
        
        // Load initial data
        await this.loadInitialData();
        
        // Connect WebSocket
        this.connectWebSocket();
        
        // Load weather comparison
        this.loadWeatherComparison();
        
        console.log('Dashboard initialized successfully');
    }

    initializeCharts() {
        // Temperature Chart
        const tempCtx = document.getElementById('temperatureChart').getContext('2d');
        this.charts.temperature = ChartUtils.createLineChart(
            tempCtx, 
            'Temperature (°C)', 
            ChartUtils.getColorForSensorType('temperature'),
            this.config.maxDataPoints
        );

        // Humidity Chart
        const humCtx = document.getElementById('humidityChart').getContext('2d');
        this.charts.humidity = ChartUtils.createLineChart(
            humCtx, 
            'Humidity (%)', 
            ChartUtils.getColorForSensorType('humidity'),
            this.config.maxDataPoints
        );

        // Luminosity Chart
        const lumCtx = document.getElementById('luminosityChart').getContext('2d');
        this.charts.luminosity = ChartUtils.createLineChart(
            lumCtx, 
            'Luminosity (lux)', 
            ChartUtils.getColorForSensorType('luminosity'),
            this.config.maxDataPoints
        );

        console.log('Charts initialized');
    }

    async loadInitialData() {
        try {
            console.log('Loading initial sensor data...');
            
            // Load latest sensor readings
            const response = await fetch(`${this.config.backendUrl}/v1/sensors/latest`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const data = await response.json();
            this.processSensorData(data);
            
            // Load historical data for charts
            await this.loadHistoricalData();
            
            // Load system stats
            await this.loadSystemStats();
            
            console.log('Initial data loaded successfully');
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data', error.message);
        }
    }

    async loadHistoricalData() {
        const sensorTypes = ['temperature', 'humidity', 'luminosity'];
        
        for (const sensorType of sensorTypes) {
            try {
                // Find the most recent sensor ID for this type
                const latestResponse = await fetch(`${this.config.backendUrl}/v1/sensors/latest`);
                const latestData = await latestResponse.json();
                
                const sensorTypeData = latestData.sensors[sensorType];
                if (!sensorTypeData || sensorTypeData.length === 0) {
                    console.log(`No sensors found for type: ${sensorType}`);
                    continue;
                }
                
                const sensorId = sensorTypeData[0].sensor_id;
                
                // Load historical data for this sensor
                const historyResponse = await fetch(
                    `${this.config.backendUrl}/v1/sensors/history?sensor_id=${sensorId}&limit=50&hours=6`
                );
                
                if (historyResponse.ok) {
                    const historyData = await historyResponse.json();
                    this.updateChartWithHistory(sensorType, historyData.readings);
                }
                
            } catch (error) {
                console.error(`Error loading historical data for ${sensorType}:`, error);
            }
        }
    }

    updateChartWithHistory(sensorType, readings) {
        if (!this.charts[sensorType] || !readings) return;
        
        // Sort readings by timestamp (oldest first)
        const sortedReadings = readings.reverse();
        
        const labels = sortedReadings.map(reading => 
            ChartUtils.formatTimestamp(reading.timestamp)
        );
        const values = sortedReadings.map(reading => reading.value);
        
        // Clear existing data and add historical data
        this.charts[sensorType].data.labels = labels;
        this.charts[sensorType].data.datasets[0].data = values;
        this.charts[sensorType].update();
        
        console.log(`Updated ${sensorType} chart with ${readings.length} historical points`);
    }

    async loadSystemStats() {
        try {
            const response = await fetch(`${this.config.backendUrl}/v1/sensors/stats?hours=24`);
            if (response.ok) {
                const stats = await response.json();
                this.updateSystemStatus(stats);
            }
        } catch (error) {
            console.error('Error loading system stats:', error);
        }
    }

    processSensorData(data) {
        const { sensors, last_updated } = data;
        
        // Update current readings display
        this.updateCurrentReadings(sensors);
        
        // Update last update time
        if (last_updated) {
            this.lastUpdate = new Date(last_updated);
            this.updateLastUpdateDisplay();
        }
        
        console.log('Sensor data processed:', Object.keys(sensors));
    }

    updateCurrentReadings(sensors) {
        // Temperature
        if (sensors.temperature && sensors.temperature.length > 0) {
            const latest = sensors.temperature[0];
            document.getElementById('currentTemp').textContent = `${ChartUtils.formatNumber(latest.value, 1)}°C`;
            document.getElementById('tempStatus').textContent = latest.anomaly ? 'ANOMALY DETECTED' : 'Normal';
            document.getElementById('tempStatus').className = latest.anomaly ? 'text-danger' : 'text-success';
            document.getElementById('tempCount').textContent = `${sensors.temperature.length} sensors`;
        }

        // Humidity
        if (sensors.humidity && sensors.humidity.length > 0) {
            const latest = sensors.humidity[0];
            document.getElementById('currentHumidity').textContent = `${ChartUtils.formatNumber(latest.value, 1)}%`;
            document.getElementById('humidityStatus').textContent = latest.anomaly ? 'ANOMALY DETECTED' : 'Normal';
            document.getElementById('humidityStatus').className = latest.anomaly ? 'text-danger' : 'text-success';
            document.getElementById('humidityCount').textContent = `${sensors.humidity.length} sensors`;
        }

        // Luminosity
        if (sensors.luminosity && sensors.luminosity.length > 0) {
            const latest = sensors.luminosity[0];
            document.getElementById('currentLuminosity').textContent = `${ChartUtils.formatNumber(latest.value, 0)} lux`;
            document.getElementById('luminosityStatus').textContent = latest.anomaly ? 'ANOMALY DETECTED' : 'Normal';
            document.getElementById('luminosityStatus').className = latest.anomaly ? 'text-danger' : 'text-success';
            document.getElementById('luminosityCount').textContent = `${sensors.luminosity.length} sensors`;
        }
    }

    updateSystemStatus(stats) {
        // Update counters
        document.getElementById('totalReadings').textContent = stats.total_readings || 0;
        document.getElementById('anomalyRate').textContent = `${stats.anomaly_rate || 0}%`;
        
        // Count active sensors
        const activeSensors = stats.by_sensor_type ? stats.by_sensor_type.length : 0;
        document.getElementById('activeSensors').textContent = activeSensors;
    }

    connectWebSocket() {
        if (this.websocket) {
            this.websocket.close();
        }

        console.log('Connecting to WebSocket:', this.config.websocketUrl);
        
        try {
            this.websocket = new WebSocket(this.config.websocketUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.isConnected = true;
                this.retryCount = 0;
                this.updateConnectionStatus(true);
                
                // Send ping to keep connection alive
                this.startPingInterval();
            };
            
            this.websocket.onmessage = (event) => {
                try {
                    const message = JSON.parse(event.data);
                    this.handleWebSocketMessage(message);
                } catch (error) {
                    console.error('Error parsing WebSocket message:', error);
                }
            };
            
            this.websocket.onclose = () => {
                console.log('WebSocket disconnected');
                this.isConnected = false;
                this.updateConnectionStatus(false);
                
                // Attempt to reconnect
                this.scheduleReconnect();
            };
            
            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus(false);
            };
            
        } catch (error) {
            console.error('Error creating WebSocket:', error);
            this.updateConnectionStatus(false);
            this.scheduleReconnect();
        }
    }

    handleWebSocketMessage(message) {
        console.log('WebSocket message received:', message.type);
        
        switch (message.type) {
            case 'sensor_data':
                this.handleSensorDataMessage(message.data);
                break;
            case 'weather_data':
                this.handleWeatherDataMessage(message.data);
                break;
            case 'alert':
                this.handleAlertMessage(message.data);
                break;
            case 'system_status':
                this.handleSystemStatusMessage(message.data);
                break;
            case 'pong':
                // Keep-alive response
                break;
            default:
                console.log('Unknown message type:', message.type);
        }
    }

    handleSensorDataMessage(data) {
        const { sensor_type, sensor_id, value, timestamp, anomaly } = data;
        
        // Update current reading display
        this.updateSingleSensorReading(sensor_type, data);
        
        // Add to chart
        if (this.charts[sensor_type]) {
            const timeLabel = ChartUtils.formatTimestamp(timestamp);
            ChartUtils.addSingleDataPoint(
                this.charts[sensor_type], 
                timeLabel, 
                value, 
                this.config.maxDataPoints
            );
        }
        
        // Show alert if anomaly
        if (anomaly) {
            this.showAnomalyAlert(data);
        }
        
        // Update last update time
        this.lastUpdate = new Date();
        this.updateLastUpdateDisplay();
    }

    updateSingleSensorReading(sensorType, data) {
        const elementMap = {
            temperature: { 
                value: 'currentTemp', 
                status: 'tempStatus',
                unit: '°C'
            },
            humidity: { 
                value: 'currentHumidity', 
                status: 'humidityStatus',
                unit: '%'
            },
            luminosity: { 
                value: 'currentLuminosity', 
                status: 'luminosityStatus',
                unit: ' lux'
            }
        };
        
        const elements = elementMap[sensorType];
        if (!elements) return;
        
        const valueElement = document.getElementById(elements.value);
        const statusElement = document.getElementById(elements.status);
        
        if (valueElement) {
            valueElement.textContent = `${ChartUtils.formatNumber(data.value, 1)}${elements.unit}`;
        }
        
        if (statusElement) {
            statusElement.textContent = data.anomaly ? 'ANOMALY DETECTED' : 'Normal';
            statusElement.className = data.anomaly ? 'text-danger' : 'text-success';
        }
    }

    showAnomalyAlert(data) {
        const alertsContainer = document.getElementById('alertsList');
        const alertHtml = ChartUtils.createAnomalyAlert(data);
        
        // Add new alert at the top
        alertsContainer.insertAdjacentHTML('afterbegin', alertHtml);
        
        // Keep only the 5 most recent alerts
        const alerts = alertsContainer.querySelectorAll('.alert');
        if (alerts.length > 5) {
            for (let i = 5; i < alerts.length; i++) {
                alerts[i].remove();
            }
        }
    }

    async loadWeatherComparison() {
        try {
            const response = await fetch(`${this.config.backendUrl}/v1/sensors/compare/weather`);
            if (response.ok) {
                const comparison = await response.json();
                this.updateWeatherComparison(comparison);
            }
        } catch (error) {
            console.error('Error loading weather comparison:', error);
            document.getElementById('weatherComparison').innerHTML = 
                ChartUtils.createErrorMessage('Failed to load weather comparison');
        }
    }

    updateWeatherComparison(comparison) {
        // Update weather display
        if (comparison.weather_data) {
            const weather = comparison.weather_data;
            document.getElementById('weatherTemp').textContent = `${ChartUtils.formatNumber(weather.temperature, 1)}°C`;
            document.getElementById('weatherLocation').textContent = weather.city;
        }
        
        // Update comparison display
        if (comparison.comparison) {
            const comparisonHtml = ChartUtils.createWeatherComparisonCard(comparison.comparison);
            document.getElementById('weatherComparison').innerHTML = comparisonHtml;
        }
    }

    startPeriodicUpdates() {
        // Update sensor data every 10 seconds
        setInterval(() => {
            if (!this.isConnected) {
                this.loadInitialData();
            }
        }, this.config.updateInterval);
        
        // Update weather comparison every 5 minutes
        setInterval(() => {
            this.loadWeatherComparison();
        }, this.config.weatherUpdateInterval);
        
        // Update system stats every 30 seconds
        setInterval(() => {
            this.loadSystemStats();
        }, 30000);
    }

    startPingInterval() {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
        }
        
        this.pingInterval = setInterval(() => {
            if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
                this.websocket.send(JSON.stringify({ type: 'ping' }));
            }
        }, 30000); // Ping every 30 seconds
    }

    scheduleReconnect() {
        if (this.retryCount >= this.maxRetries) {
            console.log('Max reconnection attempts reached');
            return;
        }
        
        this.retryCount++;
        const delay = Math.min(1000 * Math.pow(2, this.retryCount), 30000); // Exponential backoff, max 30s
        
        console.log(`Scheduling reconnection attempt ${this.retryCount} in ${delay}ms`);
        
        setTimeout(() => {
            this.connectWebSocket();
        }, delay);
    }

    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        const textElement = document.getElementById('connectionText');
        
        if (connected) {
            statusElement.className = 'status-indicator status-connected';
            textElement.textContent = 'Connected';
        } else {
            statusElement.className = 'status-indicator status-disconnected';
            textElement.textContent = 'Disconnected';
        }
        
        // Update MQTT status
        const mqttStatusElement = document.getElementById('mqttStatus');
        if (mqttStatusElement) {
            mqttStatusElement.innerHTML = ChartUtils.createSystemStatusIndicator(connected, 'MQTT');
        }
    }

    updateLastUpdateDisplay() {
        const element = document.getElementById('lastUpdate');
        if (this.lastUpdate && element) {
            element.textContent = `Last updated: ${ChartUtils.formatDate(this.lastUpdate)}`;
        }
    }

    showError(title, message) {
        console.error(`${title}: ${message}`);
        
        // You could show a toast notification here
        const alertHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>${title}</strong><br>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        document.body.insertAdjacentHTML('afterbegin', alertHtml);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new IoTDashboard();
});

// Handle page visibility changes to pause/resume updates
document.addEventListener('visibilitychange', () => {
    if (window.dashboard) {
        if (document.hidden) {
            console.log('Page hidden - reducing update frequency');
        } else {
            console.log('Page visible - resuming normal updates');
            window.dashboard.loadInitialData();
        }
    }
});