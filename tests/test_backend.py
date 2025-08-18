#!/usr/bin/env python3
"""
Test suite for IoT-Ecosystem backend API endpoints.
Basic functional tests for the FastAPI application.
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import the FastAPI app (adjust import path as needed)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cloud-backend'))

from app.main import app
from app.api.v1.sensors import sensor_readings

# Test client
client = TestClient(app)

class TestBackendAPI:
    """Test cases for the backend API."""
    
    def setup_method(self):
        """Setup test environment."""
        # Clear sensor readings for each test
        sensor_readings.clear()
        
    def test_root_endpoint(self):
        """Test the root endpoint returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert data["service"] == "IoT-Ecosystem Cloud Backend"
        assert data["status"] == "running"
    
    def test_health_check(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "mqtt_connected" in data
        assert "total_readings" in data
    
    def test_login_valid_credentials(self):
        """Test login with valid credentials."""
        login_data = {
            "username": "admin",
            "password": "password123"
        }
        
        response = client.post("/v1/auth/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "expires_in" in data
        assert "user" in data
        assert data["token_type"] == "bearer"
        assert data["user"] == "admin"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            "username": "admin",
            "password": "wrongpassword"
        }
        
        response = client.post("/v1/auth/login", json=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "Incorrect username or password" in data["detail"]
    
    def test_latest_readings_empty(self):
        """Test latest readings endpoint with no data."""
        response = client.get("/v1/sensors/latest")
        assert response.status_code == 200
        
        data = response.json()
        assert "temperature" in data
        assert "humidity" in data
        assert "luminosity" in data
        assert "total_readings" in data
        assert data["temperature"] is None
        assert data["humidity"] is None
        assert data["luminosity"] is None
        assert data["total_readings"] == 0
    
    def test_latest_readings_with_data(self):
        """Test latest readings endpoint with sample data."""
        # Add sample sensor readings
        sample_reading = {
            "id": 1,
            "timestamp": datetime.utcnow(),
            "sensor_type": "temperature",
            "sensor_id": "test_sensor_001",
            "value": 25.3,
            "unit": "celsius",
            "origin": "test",
            "anomaly": False,
            "created_at": datetime.utcnow()
        }
        sensor_readings.append(sample_reading)
        
        response = client.get("/v1/sensors/latest")
        assert response.status_code == 200
        
        data = response.json()
        assert data["temperature"] is not None
        assert data["temperature"]["value"] == 25.3
        assert data["temperature"]["sensor_id"] == "test_sensor_001"
        assert data["total_readings"] == 1
    
    def test_sensor_history_empty(self):
        """Test sensor history endpoint with no data."""
        response = client.get("/v1/sensors/history")
        assert response.status_code == 200
        
        data = response.json()
        assert "readings" in data
        assert "total_count" in data
        assert "filters_applied" in data
        assert len(data["readings"]) == 0
        assert data["total_count"] == 0
    
    def test_sensor_history_with_filters(self):
        """Test sensor history endpoint with filters."""
        # Add sample data
        sample_readings = [
            {
                "id": 1,
                "timestamp": datetime.utcnow(),
                "sensor_type": "temperature",
                "sensor_id": "temp_001",
                "value": 25.3,
                "unit": "celsius",
                "origin": "test",
                "anomaly": False,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "timestamp": datetime.utcnow(),
                "sensor_type": "humidity",
                "sensor_id": "humid_001",
                "value": 65.2,
                "unit": "percent",
                "origin": "test",
                "anomaly": True,
                "created_at": datetime.utcnow()
            }
        ]
        sensor_readings.extend(sample_readings)
        
        # Test filtering by sensor type
        response = client.get("/v1/sensors/history?sensor_type=temperature&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["readings"]) == 1
        assert data["readings"][0]["sensor_type"] == "temperature"
        assert data["filters_applied"]["sensor_type"] == "temperature"
        assert data["filters_applied"]["limit"] == 10
        
        # Test filtering by anomalies only
        response = client.get("/v1/sensors/history?anomalies_only=true")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["readings"]) == 1
        assert data["readings"][0]["anomaly"] is True
    
    def test_sensor_stats(self):
        """Test sensor statistics endpoint."""
        # Add sample data with anomalies
        sample_readings = [
            {
                "id": 1,
                "timestamp": datetime.utcnow(),
                "sensor_type": "temperature",
                "sensor_id": "temp_001",
                "value": 25.3,
                "unit": "celsius",
                "origin": "test",
                "anomaly": False,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "timestamp": datetime.utcnow(),
                "sensor_type": "temperature",
                "sensor_id": "temp_001",
                "value": 45.8,
                "unit": "celsius",
                "origin": "test",
                "anomaly": True,
                "created_at": datetime.utcnow()
            }
        ]
        sensor_readings.extend(sample_readings)
        
        response = client.get("/v1/sensors/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_readings" in data
        assert "anomalous_readings" in data
        assert "anomaly_rate" in data
        assert "sensor_types" in data
        assert "active_sensors" in data
        assert "readings_by_type" in data
        
        assert data["total_readings"] == 2
        assert data["anomalous_readings"] == 1
        assert data["anomaly_rate"] == 50.0
        assert "temperature" in data["sensor_types"]
        assert "temp_001" in data["active_sensors"]
    
    @patch('app.services.openweather.openweather_service.get_weather')
    def test_weather_endpoint_success(self, mock_get_weather):
        """Test weather endpoint with successful API response."""
        mock_weather_data = {
            "city": "London",
            "country": "GB",
            "temperature": 18.5,
            "humidity": 72.0,
            "description": "light rain",
            "timestamp": "2024-01-01T12:00:00Z"
        }
        mock_get_weather.return_value = mock_weather_data
        
        response = client.get("/v1/external/weather?city=London")
        assert response.status_code == 200
        
        data = response.json()
        assert data["city"] == "London"
        assert data["country"] == "GB"
        assert data["temperature"] == 18.5
        assert data["humidity"] == 72.0
        assert "comparison" in data
    
    @patch('app.services.openweather.openweather_service.get_weather')
    def test_weather_endpoint_city_not_found(self, mock_get_weather):
        """Test weather endpoint with city not found."""
        mock_get_weather.return_value = {
            "error": "City not found",
            "city": "NonexistentCity"
        }
        
        response = client.get("/v1/external/weather?city=NonexistentCity")
        assert response.status_code == 404
    
    def test_system_status(self):
        """Test system status endpoint."""
        response = client.get("/v1/system/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "mqtt_connected" in data
        assert "database_connected" in data
        assert "total_readings" in data
        assert "active_sensors" in data
        assert "uptime_seconds" in data
        assert data["database_connected"] is True  # Always true for in-memory storage
    
    def test_protected_route_without_token(self):
        """Test protected route without authentication token."""
        response = client.get("/v1/auth/verify")
        assert response.status_code == 403  # Should be forbidden without token
    
    def test_protected_route_with_valid_token(self):
        """Test protected route with valid authentication token."""
        # First login to get token
        login_data = {
            "username": "admin",
            "password": "password123"
        }
        
        login_response = client.post("/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        token = login_response.json()["access_token"]
        
        # Use token to access protected route
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/v1/auth/verify", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["authenticated"] is True
        assert data["user"] == "admin"
    
    def test_invalid_sensor_type_filter(self):
        """Test history endpoint with invalid sensor type filter."""
        response = client.get("/v1/sensors/history?sensor_type=invalid_type")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["readings"]) == 0
        assert data["filters_applied"]["sensor_type"] == "invalid_type"

class TestSensorDataProcessing:
    """Test sensor data processing functions."""
    
    def setup_method(self):
        """Setup test environment."""
        sensor_readings.clear()
    
    @pytest.mark.asyncio
    async def test_add_sensor_reading(self):
        """Test adding a sensor reading via MQTT handler."""
        from app.api.v1.sensors import add_sensor_reading
        
        topic = "sensors/temperature/test001"
        payload = {
            "ts": "2024-01-01T12:00:00Z",
            "type": "temperature",
            "value": 25.3,
            "unit": "celsius",
            "sensor_id": "test_sensor_001",
            "origin": "test",
            "anomaly": False
        }
        
        await add_sensor_reading(topic, payload)
        
        assert len(sensor_readings) == 1
        reading = sensor_readings[0]
        assert reading["sensor_type"] == "temperature"
        assert reading["value"] == 25.3
        assert reading["sensor_id"] == "test_sensor_001"
        assert reading["anomaly"] is False
        assert reading["mqtt_topic"] == topic
    
    @pytest.mark.asyncio
    async def test_add_anomalous_sensor_reading(self):
        """Test adding an anomalous sensor reading."""
        from app.api.v1.sensors import add_sensor_reading
        
        topic = "sensors/temperature/test001"
        payload = {
            "ts": "2024-01-01T12:00:00Z",
            "type": "temperature",
            "value": 45.8,
            "unit": "celsius",
            "sensor_id": "test_sensor_001",
            "origin": "test",
            "anomaly": True,
            "anomaly_details": {
                "out_of_range": True,
                "threshold_max": 35.0
            }
        }
        
        await add_sensor_reading(topic, payload)
        
        assert len(sensor_readings) == 1
        reading = sensor_readings[0]
        assert reading["anomaly"] is True
        assert reading["anomaly_details"]["out_of_range"] is True
    
    def test_get_local_sensor_data(self):
        """Test getting local sensor data for weather comparison."""
        from app.api.v1.sensors import get_local_sensor_data
        
        # Add sample temperature and humidity readings
        sample_readings = [
            {
                "id": 1,
                "timestamp": datetime.utcnow() - timedelta(minutes=1),
                "sensor_type": "temperature",
                "sensor_id": "temp_001",
                "value": 25.3,
                "unit": "celsius",
                "origin": "test",
                "anomaly": False,
                "created_at": datetime.utcnow()
            },
            {
                "id": 2,
                "timestamp": datetime.utcnow(),
                "sensor_type": "humidity",
                "sensor_id": "humid_001",
                "value": 65.2,
                "unit": "percent",
                "origin": "test",
                "anomaly": False,
                "created_at": datetime.utcnow()
            }
        ]
        sensor_readings.extend(sample_readings)
        
        local_data = get_local_sensor_data()
        
        assert "temperature" in local_data
        assert "humidity" in local_data
        assert "timestamp" in local_data
        assert local_data["temperature"] == 25.3
        assert local_data["humidity"] == 65.2

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])