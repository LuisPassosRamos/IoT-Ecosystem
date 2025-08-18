/**
 * IoT-Ecosystem Dashboard Application
 * Main application logic for real-time sensor monitoring
 */

class IoTDashboard {
    constructor() {
        this.apiBaseUrl = '/api';
        this.wsUrl = `ws://${window.location.host}/ws`;
        this.websocket = null;
        this.isRealTimeEnabled = true;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 5000;
        
        // Data storage
        this.latestReadings = {
            temperature: null,
            humidity: null,
            luminosity: null
        };
        
        this.init();
    }

    /**
     * Initialize the dashboard
     */
    async init() {
        try {
            console.log('Initializing IoT Dashboard...');
            
            // Create charts
            this.createCharts();
            
            // Load initial data
            await this.loadInitialData();
            
            // Setup WebSocket connection
            this.connectWebSocket();
            
            // Setup event listeners
            this.setupEventListeners();
            
            // Check API connectivity
            this.checkApiStatus();
            
            console.log('Dashboard initialized successfully');
            
        } catch (error) {
            console.error('Error initializing dashboard:', error);
            this.showError('Failed to initialize dashboard');
        }
    }

    /**
     * Create Chart.js charts
     */
    createCharts() {
        chartUtils.createChart('temperature-chart', 'temperature', '°C');
        chartUtils.createChart('humidity-chart', 'humidity', '%');
        chartUtils.createChart('luminosity-chart', 'luminosity', 'lux');
    }

    /**
     * Load initial sensor data
     */
    async loadInitialData() {
        try {
            // Get latest readings
            const latestResponse = await fetch(`${this.apiBaseUrl}/v1/sensors/latest`);
            if (latestResponse.ok) {
                const latestData = await latestResponse.json();
                this.updateLatestReadings(latestData);
            }

            // Get historical data for charts
            const historyResponse = await fetch(`${this.apiBaseUrl}/v1/sensors/history?limit=100`);
            if (historyResponse.ok) {
                const historyData = await historyResponse.json();
                this.loadHistoricalData(historyData.readings);
            }

            // Update total readings count
            this.updateTotalReadings();

        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showError('Failed to load initial data');
        }
    }

    /**
     * Setup WebSocket connection for real-time updates
     */
    connectWebSocket() {
        try {
            this.websocket = new WebSocket(this.wsUrl);
            
            this.websocket.onopen = () => {
                console.log('WebSocket connected');
                this.updateConnectionStatus('ws', true);
                this.reconnectAttempts = 0;
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
                this.updateConnectionStatus('ws', false);
                this.scheduleReconnect();
            };

            this.websocket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.updateConnectionStatus('ws', false);
            };

        } catch (error) {
            console.error('Error creating WebSocket connection:', error);
            this.updateConnectionStatus('ws', false);
        }
    }

    /**
     * Handle WebSocket messages
     */
    handleWebSocketMessage(message) {
        switch (message.type) {
            case 'sensor_data':
                if (this.isRealTimeEnabled) {
                    this.processSensorData(message.data);
                }
                break;
                
            case 'connection_established':
                console.log('WebSocket connection established:', message.data.message);
                break;
                
            case 'pong':
                console.log('Received pong');
                break;
                
            case 'latest_data':
                this.updateLatestReadings(message.data);
                break;
                
            case 'error':
                console.error('WebSocket error message:', message.data);
                break;
                
            default:
                console.log('Unknown WebSocket message type:', message.type);
        }
    }

    /**
     * Process new sensor data
     */
    processSensorData(data) {
        const { payload, sensor_type } = data;
        
        if (!payload || !sensor_type) return;

        // Update chart
        chartUtils.updateChart(
            sensor_type,
            payload.ts,
            payload.value,
            payload.anomaly
        );

        // Update latest reading display
        this.updateSensorValue(sensor_type, payload.value, payload.unit, payload.anomaly);
        
        // Update last update time
        this.updateLastUpdateTime();
        
        // Store latest reading
        this.latestReadings[sensor_type] = payload;
    }

    /**
     * Update latest readings display
     */
    updateLatestReadings(data) {
        if (data.temperature) {
            this.updateSensorValue('temperature', data.temperature.value, '°C', data.temperature.anomaly);
            this.latestReadings.temperature = data.temperature;
        }
        
        if (data.humidity) {
            this.updateSensorValue('humidity', data.humidity.value, '%', data.humidity.anomaly);
            this.latestReadings.humidity = data.humidity;
        }
        
        if (data.luminosity) {
            this.updateSensorValue('luminosity', data.luminosity.value, 'lux', data.luminosity.anomaly);
            this.latestReadings.luminosity = data.luminosity;
        }

        // Update total readings
        if (data.total_readings) {
            document.getElementById('total-readings').textContent = data.total_readings;
        }
    }

    /**
     * Update sensor value display
     */
    updateSensorValue(sensorType, value, unit, isAnomaly = false) {
        const elementId = `${sensorType}-value`;
        const element = document.getElementById(elementId);
        
        if (element) {
            const formattedValue = typeof value === 'number' ? value.toFixed(1) : value;
            element.innerHTML = `<span>${formattedValue}${unit}</span>`;
            
            // Update styling based on anomaly
            element.className = 'chart-value';
            if (isAnomaly) {
                element.classList.add('value-danger');
                element.innerHTML += '<span class="anomaly-badge">ANOMALY</span>';
            } else {
                element.classList.add('value-normal');
            }
        }
    }

    /**
     * Load historical data into charts
     */
    loadHistoricalData(readings) {
        const groupedReadings = {
            temperature: [],
            humidity: [],
            luminosity: []
        };

        // Group readings by sensor type
        readings.forEach(reading => {
            if (groupedReadings[reading.sensor_type]) {
                groupedReadings[reading.sensor_type].push(reading);
            }
        });

        // Load data into charts
        Object.keys(groupedReadings).forEach(sensorType => {
            if (groupedReadings[sensorType].length > 0) {
                chartUtils.loadHistoricalData(sensorType, groupedReadings[sensorType]);
            }
        });
    }

    /**
     * Update connection status indicators
     */
    updateConnectionStatus(type, isConnected) {
        const element = document.getElementById(`${type}-status`);
        if (element) {
            element.className = `status-indicator ${isConnected ? 'status-connected' : 'status-disconnected'}`;
        }
    }

    /**
     * Update last update time
     */
    updateLastUpdateTime() {
        const element = document.getElementById('last-update');
        if (element) {
            element.textContent = new Date().toLocaleTimeString();
        }
    }

    /**
     * Update total readings count
     */
    async updateTotalReadings() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/v1/sensors/stats`);
            if (response.ok) {
                const stats = await response.json();
                document.getElementById('total-readings').textContent = stats.total_readings || 0;
            }
        } catch (error) {
            console.error('Error updating total readings:', error);
        }
    }

    /**
     * Check API status
     */
    async checkApiStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const isHealthy = response.ok;
            
            this.updateConnectionStatus('api', isHealthy);
            
            if (isHealthy) {
                const healthData = await response.json();
                this.updateConnectionStatus('mqtt', healthData.mqtt_connected);
            }
            
        } catch (error) {
            console.error('Error checking API status:', error);
            this.updateConnectionStatus('api', false);
        }
    }

    /**
     * Schedule WebSocket reconnection
     */
    scheduleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect WebSocket (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
            
            setTimeout(() => {
                this.connectWebSocket();
            }, this.reconnectDelay);
        } else {
            console.error('Max reconnection attempts reached');
            this.showError('WebSocket connection failed. Please refresh the page.');
        }
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Refresh data button
        window.refreshData = () => this.refreshData();
        
        // Toggle real-time button
        window.toggleRealTime = () => this.toggleRealTime();
        
        // Get weather data button
        window.getWeatherData = () => this.getWeatherData();
        
        // Periodic status check
        setInterval(() => {
            this.checkApiStatus();
        }, 30000); // Check every 30 seconds
    }

    /**
     * Refresh all data
     */
    async refreshData() {
        try {
            await this.loadInitialData();
            console.log('Data refreshed');
        } catch (error) {
            console.error('Error refreshing data:', error);
            this.showError('Failed to refresh data');
        }
    }

    /**
     * Toggle real-time updates
     */
    toggleRealTime() {
        this.isRealTimeEnabled = !this.isRealTimeEnabled;
        const button = document.getElementById('realtime-btn');
        
        if (this.isRealTimeEnabled) {
            button.textContent = '⏸️ Pause Real-time';
            button.style.background = '#667eea';
        } else {
            button.textContent = '▶️ Resume Real-time';
            button.style.background = '#28a745';
        }
        
        console.log(`Real-time updates ${this.isRealTimeEnabled ? 'enabled' : 'disabled'}`);
    }

    /**
     * Get weather data and comparison
     */
    async getWeatherData() {
        try {
            const cityInput = document.getElementById('city-input');
            const city = cityInput.value.trim();
            
            if (!city) {
                this.showError('Please enter a city name');
                return;
            }

            // Show loading
            const weatherPanel = document.getElementById('weather-panel');
            const externalWeather = document.getElementById('external-weather');
            const localSensors = document.getElementById('local-sensors');
            const weatherAlerts = document.getElementById('weather-alerts');
            
            weatherPanel.style.display = 'block';
            externalWeather.innerHTML = '<div class="loading">Loading weather data...</div>';
            
            // Fetch weather data
            const response = await fetch(`${this.apiBaseUrl}/v1/external/weather?city=${encodeURIComponent(city)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const weatherData = await response.json();
            
            // Display external weather
            externalWeather.innerHTML = `
                <strong>${weatherData.city}, ${weatherData.country}</strong><br>
                Temperature: ${weatherData.temperature}°C<br>
                Humidity: ${weatherData.humidity}%<br>
                Condition: ${weatherData.description}<br>
                <small>Updated: ${new Date(weatherData.timestamp).toLocaleString()}</small>
            `;
            
            // Display local sensor data
            const tempReading = this.latestReadings.temperature;
            const humidityReading = this.latestReadings.humidity;
            
            if (tempReading || humidityReading) {
                localSensors.innerHTML = `
                    ${tempReading ? `Temperature: ${tempReading.value}°C<br>` : ''}
                    ${humidityReading ? `Humidity: ${humidityReading.value}%<br>` : ''}
                    <small>Last reading: ${tempReading ? new Date(tempReading.ts).toLocaleString() : 'No data'}</small>
                `;
            } else {
                localSensors.innerHTML = '<div class="loading">No local sensor data available</div>';
            }
            
            // Display comparison alerts
            if (weatherData.comparison && weatherData.comparison.alerts && weatherData.comparison.alerts.length > 0) {
                const alertsHtml = weatherData.comparison.alerts.map(alert => `
                    <div class="comparison-alert ${alert.severity}">
                        <strong>${alert.type.replace('_', ' ').toUpperCase()}</strong><br>
                        ${alert.message}
                    </div>
                `).join('');
                
                weatherAlerts.innerHTML = alertsHtml;
            } else {
                weatherAlerts.innerHTML = '<div class="comparison-alert">No significant differences detected between local sensors and weather API.</div>';
            }
            
        } catch (error) {
            console.error('Error getting weather data:', error);
            this.showError(`Failed to get weather data: ${error.message}`);
            
            const externalWeather = document.getElementById('external-weather');
            externalWeather.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        }
    }

    /**
     * Show error message
     */
    showError(message) {
        // You could implement a toast notification or modal here
        console.error(message);
        
        // Simple alert for now (in production, use a better UI)
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error';
        errorDiv.textContent = message;
        errorDiv.style.position = 'fixed';
        errorDiv.style.top = '20px';
        errorDiv.style.right = '20px';
        errorDiv.style.zIndex = '1000';
        errorDiv.style.maxWidth = '300px';
        
        document.body.appendChild(errorDiv);
        
        // Remove after 5 seconds
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.parentNode.removeChild(errorDiv);
            }
        }, 5000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new IoTDashboard();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden, reduce update frequency
        console.log('Page hidden, reducing update frequency');
    } else {
        // Page is visible, resume normal updates
        console.log('Page visible, resuming normal updates');
        if (window.dashboard) {
            window.dashboard.checkApiStatus();
        }
    }
});