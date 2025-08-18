/**
 * Chart utility functions for IoT Dashboard
 */

class ChartUtils {
    static createLineChart(ctx, label, color, maxDataPoints = 50) {
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: label,
                    data: [],
                    borderColor: color,
                    backgroundColor: color + '20',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: 'white',
                        bodyColor: 'white',
                        borderColor: color,
                        borderWidth: 1,
                        displayColors: false,
                        callbacks: {
                            title: function(context) {
                                return 'Time: ' + context[0].label;
                            },
                            label: function(context) {
                                return label + ': ' + context.parsed.y;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        display: true,
                        title: {
                            display: true,
                            text: 'Time'
                        },
                        ticks: {
                            maxTicksLimit: 8,
                            callback: function(value, index, values) {
                                const label = this.getLabelForValue(value);
                                return label.split(' ')[1]; // Show only time part
                            }
                        }
                    },
                    y: {
                        display: true,
                        title: {
                            display: true,
                            text: label
                        },
                        beginAtZero: false
                    }
                },
                animation: {
                    duration: 750,
                    easing: 'easeInOutQuart'
                }
            }
        });
    }

    static updateChart(chart, newData, maxDataPoints = 50) {
        const { labels, data } = newData;
        
        // Add new data
        chart.data.labels.push(...labels);
        chart.data.datasets[0].data.push(...data);
        
        // Remove old data if we exceed max points
        if (chart.data.labels.length > maxDataPoints) {
            const excess = chart.data.labels.length - maxDataPoints;
            chart.data.labels.splice(0, excess);
            chart.data.datasets[0].data.splice(0, excess);
        }
        
        chart.update('none'); // Update without animation for real-time feel
    }

    static addSingleDataPoint(chart, label, value, maxDataPoints = 50) {
        chart.data.labels.push(label);
        chart.data.datasets[0].data.push(value);
        
        // Remove old data if we exceed max points
        if (chart.data.labels.length > maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        
        chart.update('none');
    }

    static formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('en-US', { 
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    static formatDate(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleDateString('en-US') + ' ' + 
               date.toLocaleTimeString('en-US', { hour12: false });
    }

    static getColorForSensorType(sensorType) {
        const colors = {
            'temperature': '#e74c3c',
            'humidity': '#3498db',
            'luminosity': '#f39c12',
            'pressure': '#9b59b6',
            'default': '#95a5a6'
        };
        return colors[sensorType] || colors.default;
    }

    static createAnomalyAlert(reading) {
        const alertColor = reading.anomaly ? 'alert-danger' : 'alert-success';
        const iconClass = reading.anomaly ? 'fa-exclamation-triangle' : 'fa-check-circle';
        const status = reading.anomaly ? 'ANOMALY' : 'NORMAL';
        
        return `
            <div class="alert ${alertColor} alert-dismissible fade show" role="alert">
                <i class="fas ${iconClass} me-2"></i>
                <strong>${status}:</strong> 
                ${reading.sensor_type} sensor (${reading.sensor_id}) 
                reading: ${reading.value} ${reading.unit || ''}
                <br>
                <small class="text-muted">
                    ${this.formatDate(reading.timestamp)} | Origin: ${reading.origin}
                </small>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }

    static createWeatherComparisonCard(comparison) {
        if (!comparison.weather || !comparison.sensor) {
            return '<div class="text-muted">No comparison data available</div>';
        }

        const { weather, sensor, differences, alerts } = comparison;
        
        let alertsHtml = '';
        if (alerts && alerts.length > 0) {
            alertsHtml = alerts.map(alert => `
                <div class="alert alert-${alert.severity === 'critical' ? 'danger' : 'warning'} alert-sm">
                    <i class="fas fa-exclamation-triangle me-1"></i>
                    ${alert.message}
                </div>
            `).join('');
        }

        return `
            <div class="row">
                <div class="col-md-6">
                    <h6 class="text-primary">Local Sensors</h6>
                    <ul class="list-unstyled">
                        ${sensor.temperature ? `<li><i class="fas fa-thermometer-half text-danger me-2"></i>${sensor.temperature}°C</li>` : ''}
                        ${sensor.humidity ? `<li><i class="fas fa-tint text-info me-2"></i>${sensor.humidity}%</li>` : ''}
                        ${sensor.pressure ? `<li><i class="fas fa-weight text-secondary me-2"></i>${sensor.pressure} hPa</li>` : ''}
                    </ul>
                </div>
                <div class="col-md-6">
                    <h6 class="text-info">Weather API</h6>
                    <ul class="list-unstyled">
                        <li><i class="fas fa-thermometer-half text-danger me-2"></i>${weather.temperature}°C</li>
                        <li><i class="fas fa-tint text-info me-2"></i>${weather.humidity}%</li>
                        <li><i class="fas fa-weight text-secondary me-2"></i>${weather.pressure} hPa</li>
                    </ul>
                </div>
            </div>
            ${alertsHtml}
            ${alerts.length === 0 ? '<div class="alert alert-success alert-sm"><i class="fas fa-check me-1"></i>All readings within normal range</div>' : ''}
        `;
    }

    static createSystemStatusIndicator(status, label) {
        const statusClass = status ? 'status-connected' : 'status-disconnected';
        const statusText = status ? 'Connected' : 'Disconnected';
        
        return `
            <span class="status-indicator ${statusClass}"></span>
            ${label}: ${statusText}
        `;
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    static formatNumber(num, decimals = 1) {
        if (num === null || num === undefined) return '--';
        return parseFloat(num).toFixed(decimals);
    }

    static calculateAverage(values) {
        if (!values || values.length === 0) return 0;
        const sum = values.reduce((acc, val) => acc + val, 0);
        return sum / values.length;
    }

    static findMinMax(values) {
        if (!values || values.length === 0) return { min: 0, max: 0 };
        return {
            min: Math.min(...values),
            max: Math.max(...values)
        };
    }

    static isRecentReading(timestamp, maxAgeMinutes = 30) {
        const now = new Date();
        const readingTime = new Date(timestamp);
        const ageMinutes = (now - readingTime) / (1000 * 60);
        return ageMinutes <= maxAgeMinutes;
    }

    static createLoadingSpinner(text = 'Loading...') {
        return `
            <div class="text-center text-muted p-3">
                <div class="loading-spinner me-2"></div>
                ${text}
            </div>
        `;
    }

    static createErrorMessage(message, details = '') {
        return `
            <div class="alert alert-danger" role="alert">
                <i class="fas fa-exclamation-circle me-2"></i>
                <strong>Error:</strong> ${message}
                ${details ? `<br><small>${details}</small>` : ''}
            </div>
        `;
    }
}