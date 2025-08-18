/**
 * Chart.js utilities for IoT-Ecosystem Dashboard
 * Handles chart creation, updates, and styling
 */

class ChartUtils {
    constructor() {
        this.charts = {};
        this.maxDataPoints = 50; // Maximum points to display
        this.colors = {
            temperature: {
                line: 'rgba(255, 99, 132, 1)',
                fill: 'rgba(255, 99, 132, 0.1)',
                anomaly: 'rgba(255, 0, 0, 1)'
            },
            humidity: {
                line: 'rgba(54, 162, 235, 1)', 
                fill: 'rgba(54, 162, 235, 0.1)',
                anomaly: 'rgba(255, 0, 0, 1)'
            },
            luminosity: {
                line: 'rgba(255, 206, 86, 1)',
                fill: 'rgba(255, 206, 86, 0.1)',
                anomaly: 'rgba(255, 0, 0, 1)'
            }
        };
    }

    /**
     * Create a chart for a specific sensor type
     */
    createChart(canvasId, sensorType, unit) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        const colors = this.colors[sensorType];

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: `${sensorType.charAt(0).toUpperCase() + sensorType.slice(1)} (${unit})`,
                    data: [],
                    borderColor: colors.line,
                    backgroundColor: colors.fill,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    pointBorderWidth: 2,
                    pointBackgroundColor: colors.line
                }, {
                    label: 'Anomalies',
                    data: [],
                    borderColor: colors.anomaly,
                    backgroundColor: colors.anomaly,
                    borderWidth: 0,
                    pointRadius: 8,
                    pointHoverRadius: 10,
                    pointStyle: 'triangle',
                    showLine: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            title: function(context) {
                                const label = context[0].label;
                                return new Date(label).toLocaleString();
                            },
                            label: function(context) {
                                const datasetLabel = context.dataset.label;
                                const value = context.parsed.y;
                                if (datasetLabel === 'Anomalies') {
                                    return `⚠️ Anomaly detected: ${value} ${unit}`;
                                }
                                return `${datasetLabel}: ${value} ${unit}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            displayFormats: {
                                minute: 'HH:mm',
                                hour: 'HH:mm',
                                day: 'MMM DD'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Time'
                        }
                    },
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: `${sensorType.charAt(0).toUpperCase() + sensorType.slice(1)} (${unit})`
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                },
                animation: {
                    duration: 300
                }
            }
        });

        this.charts[sensorType] = chart;
        return chart;
    }

    /**
     * Update chart with new data point
     */
    updateChart(sensorType, timestamp, value, isAnomaly = false) {
        const chart = this.charts[sensorType];
        if (!chart) return;

        const time = new Date(timestamp);
        
        // Add to normal data
        chart.data.labels.push(time);
        chart.data.datasets[0].data.push(value);

        // Add to anomaly data if needed
        if (isAnomaly) {
            chart.data.datasets[1].data.push(value);
        } else {
            chart.data.datasets[1].data.push(null);
        }

        // Keep only recent data points
        if (chart.data.labels.length > this.maxDataPoints) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
            chart.data.datasets[1].data.shift();
        }

        chart.update('none'); // Update without animation for real-time
    }

    /**
     * Load historical data into chart
     */
    loadHistoricalData(sensorType, readings) {
        const chart = this.charts[sensorType];
        if (!chart) return;

        // Clear existing data
        chart.data.labels = [];
        chart.data.datasets[0].data = [];
        chart.data.datasets[1].data = [];

        // Sort readings by timestamp
        const sortedReadings = readings.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

        // Add data points
        sortedReadings.forEach(reading => {
            const time = new Date(reading.timestamp);
            chart.data.labels.push(time);
            chart.data.datasets[0].data.push(reading.value);
            
            // Add anomaly point if needed
            if (reading.anomaly) {
                chart.data.datasets[1].data.push(reading.value);
            } else {
                chart.data.datasets[1].data.push(null);
            }
        });

        chart.update();
    }

    /**
     * Get chart instance
     */
    getChart(sensorType) {
        return this.charts[sensorType];
    }

    /**
     * Update chart Y-axis range based on data
     */
    updateYAxisRange(sensorType, min, max) {
        const chart = this.charts[sensorType];
        if (!chart) return;

        const padding = (max - min) * 0.1; // Add 10% padding
        chart.options.scales.y.min = Math.max(0, min - padding);
        chart.options.scales.y.max = max + padding;
        chart.update();
    }

    /**
     * Set chart animation enabled/disabled
     */
    setAnimationEnabled(enabled) {
        Object.values(this.charts).forEach(chart => {
            chart.options.animation.duration = enabled ? 300 : 0;
        });
    }

    /**
     * Destroy all charts
     */
    destroyAllCharts() {
        Object.values(this.charts).forEach(chart => {
            chart.destroy();
        });
        this.charts = {};
    }

    /**
     * Get color value for anomaly highlighting
     */
    getAnomalyColor(sensorType) {
        return this.colors[sensorType]?.anomaly || 'rgba(255, 0, 0, 1)';
    }

    /**
     * Get normal color value
     */
    getNormalColor(sensorType) {
        return this.colors[sensorType]?.line || 'rgba(75, 192, 192, 1)';
    }

    /**
     * Update chart theme (for dark/light mode)
     */
    updateTheme(isDark = false) {
        const textColor = isDark ? '#ffffff' : '#333333';
        const gridColor = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)';

        Object.values(this.charts).forEach(chart => {
            // Update text colors
            chart.options.scales.x.title.color = textColor;
            chart.options.scales.y.title.color = textColor;
            chart.options.scales.x.ticks.color = textColor;
            chart.options.scales.y.ticks.color = textColor;
            chart.options.plugins.legend.labels.color = textColor;
            
            // Update grid colors
            chart.options.scales.x.grid.color = gridColor;
            chart.options.scales.y.grid.color = gridColor;
            
            chart.update();
        });
    }
}

// Global chart utilities instance
window.chartUtils = new ChartUtils();