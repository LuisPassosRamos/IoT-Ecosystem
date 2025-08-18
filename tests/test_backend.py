"""
Tests for IoT Backend API endpoints
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import the main app and dependencies
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'cloud-backend', 'app'))

from main import app
from models.schemas import get_db, Base, SensorReading, User
from api.v1.auth import get_password_hash

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_iot.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    # Create test client
    client = TestClient(app)
    
    # Setup test data
    setup_test_data()
    
    yield client
    
    # Cleanup
    Base.metadata.drop_all(bind=engine)

def setup_test_data():
    """Setup test data for the test database"""
    db = TestingSessionLocal()
    
    # Create test user
    test_user = User(
        username="testuser",
        hashed_password=get_password_hash("testpassword"),
        is_active=True
    )
    db.add(test_user)
    
    # Create test sensor readings
    now = datetime.utcnow()
    test_readings = [
        SensorReading(
            timestamp=now - timedelta(minutes=i),
            sensor_type="temperature",
            sensor_id="temp-test-001",
            value=20.0 + i * 0.1,
            unit="°C",
            origin="edge",
            source_protocol="mqtt",
            anomaly=i % 10 == 0,  # Every 10th reading is anomalous
            raw_data=json.dumps({"test": True})
        )
        for i in range(50)
    ]
    
    test_readings.extend([
        SensorReading(
            timestamp=now - timedelta(minutes=i),
            sensor_type="humidity",
            sensor_id="hum-test-001",
            value=50.0 + i * 0.2,
            unit="%",
            origin="edge",
            source_protocol="mqtt",
            anomaly=i % 15 == 0,
            raw_data=json.dumps({"test": True})
        )
        for i in range(30)
    ])
    
    for reading in test_readings:
        db.add(reading)
    
    db.commit()
    db.close()

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self, client):
        """Test successful login"""
        response = client.post("/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post("/v1/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user"""
        response = client.post("/v1/auth/login", json={
            "username": "nonexistent",
            "password": "password"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self, client):
        """Test getting current user info"""
        # First login to get token
        login_response = client.post("/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        
        # Use token to get user info
        response = client.get("/v1/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["is_active"] == True
    
    def test_invalid_token(self, client):
        """Test using invalid token"""
        response = client.get("/v1/auth/me", headers={
            "Authorization": "Bearer invalid_token"
        })
        assert response.status_code == 401

class TestSensorEndpoints:
    """Test sensor data endpoints"""
    
    @pytest.fixture
    def auth_headers(self, client):
        """Get authentication headers for protected endpoints"""
        login_response = client.post("/v1/auth/login", json={
            "username": "testuser",
            "password": "testpassword"
        })
        token = login_response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_latest_sensors(self, client):
        """Test getting latest sensor readings"""
        response = client.get("/v1/sensors/latest")
        assert response.status_code == 200
        data = response.json()
        
        assert "sensors" in data
        assert "total_count" in data
        assert data["total_count"] > 0
        
        # Check if we have temperature and humidity data
        sensors = data["sensors"]
        assert "temperature" in sensors
        assert "humidity" in sensors
        
        # Verify temperature sensor data structure
        temp_sensors = sensors["temperature"]
        assert len(temp_sensors) > 0
        temp_reading = temp_sensors[0]
        
        required_fields = ["id", "timestamp", "sensor_type", "sensor_id", "value", "unit", "origin"]
        for field in required_fields:
            assert field in temp_reading
        
        assert temp_reading["sensor_type"] == "temperature"
        assert temp_reading["unit"] == "°C"
    
    def test_get_sensor_history(self, client):
        """Test getting sensor history"""
        response = client.get("/v1/sensors/history?sensor_id=temp-test-001&limit=20&hours=24")
        assert response.status_code == 200
        data = response.json()
        
        assert "readings" in data
        assert "sensor_id" in data
        assert "count" in data
        assert data["sensor_id"] == "temp-test-001"
        assert data["count"] > 0
        
        # Verify readings are sorted by timestamp (newest first)
        readings = data["readings"]
        for i in range(1, len(readings)):
            current_time = datetime.fromisoformat(readings[i]["timestamp"].replace('Z', '+00:00'))
            previous_time = datetime.fromisoformat(readings[i-1]["timestamp"].replace('Z', '+00:00'))
            assert current_time <= previous_time
    
    def test_get_sensor_history_nonexistent(self, client):
        """Test getting history for nonexistent sensor"""
        response = client.get("/v1/sensors/history?sensor_id=nonexistent&limit=20&hours=24")
        assert response.status_code == 404
        assert "No readings found" in response.json()["detail"]
    
    def test_get_anomalies(self, client):
        """Test getting anomalous readings"""
        response = client.get("/v1/sensors/anomalies?hours=24&limit=10")
        assert response.status_code == 200
        data = response.json()
        
        assert "anomalies" in data
        assert "count" in data
        assert "time_range" in data
        
        # Verify all returned readings are anomalous
        anomalies = data["anomalies"]
        for anomaly in anomalies:
            assert anomaly["anomaly"] == True
    
    def test_get_sensor_stats(self, client):
        """Test getting sensor statistics"""
        response = client.get("/v1/sensors/stats?hours=24")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["time_range", "total_readings", "anomaly_count", "anomaly_rate", "by_sensor_type"]
        for field in required_fields:
            assert field in data
        
        assert data["total_readings"] > 0
        assert 0 <= data["anomaly_rate"] <= 100
        assert len(data["by_sensor_type"]) > 0
        
        # Check sensor type statistics
        sensor_type_stats = data["by_sensor_type"]
        for stat in sensor_type_stats:
            assert "type" in stat
            assert "count" in stat
            assert "anomalies" in stat
            assert stat["count"] > 0
    
    def test_get_live_readings(self, client):
        """Test getting live readings from MQTT cache"""
        response = client.get("/v1/sensors/live")
        # This might return 503 if MQTT service is not running in tests
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            data = response.json()
            assert "live_readings" in data
            assert "count" in data
            assert "timestamp" in data
    
    def test_get_external_weather(self, client):
        """Test getting external weather data"""
        response = client.get("/v1/sensors/external/weather?city=London")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["city", "temperature", "humidity", "pressure", "description", "timestamp"]
        for field in required_fields:
            assert field in data
        
        assert data["city"] == "London"
        assert isinstance(data["temperature"], (int, float))
        assert isinstance(data["humidity"], (int, float))
        assert isinstance(data["pressure"], (int, float))
    
    def test_compare_with_weather(self, client):
        """Test comparing sensor data with weather data"""
        response = client.get("/v1/sensors/compare/weather?city=London")
        assert response.status_code == 200
        data = response.json()
        
        required_fields = ["weather_data", "sensor_data", "comparison", "timestamp"]
        for field in required_fields:
            assert field in data
        
        weather_data = data["weather_data"]
        assert weather_data["city"] == "London"
        
        sensor_data = data["sensor_data"]
        assert "temperature" in sensor_data
        assert "humidity" in sensor_data

class TestDataValidation:
    """Test data validation and error handling"""
    
    def test_invalid_query_parameters(self, client):
        """Test handling of invalid query parameters"""
        # Invalid limit (too high)
        response = client.get("/v1/sensors/latest?limit=2000")
        assert response.status_code == 422
        
        # Invalid hours (negative)
        response = client.get("/v1/sensors/history?sensor_id=test&hours=-5")
        assert response.status_code == 422
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON in requests"""
        response = client.post("/v1/auth/login", 
                             data="invalid json",
                             headers={"Content-Type": "application/json"})
        assert response.status_code == 422

class TestAPIPerformance:
    """Test API performance characteristics"""
    
    def test_response_time_latest_sensors(self, client):
        """Test response time for latest sensors endpoint"""
        import time
        
        start_time = time.time()
        response = client.get("/v1/sensors/latest")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_large_history_request(self, client):
        """Test handling of large history requests"""
        response = client.get("/v1/sensors/history?sensor_id=temp-test-001&limit=1000&hours=168")
        assert response.status_code == 200
        
        data = response.json()
        # Should respect the limit even if more data is available
        assert data["count"] <= 1000

class TestHealthCheck:
    """Test system health endpoints"""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "services" in data
        assert data["status"] == "healthy"
        
        services = data["services"]
        assert "database" in services
        assert services["database"] == "available"
    
    def test_api_status_endpoint(self, client):
        """Test API status endpoint"""
        response = client.get("/api/status")
        assert response.status_code in [200, 503]  # May be 503 if MQTT is down
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ["api_version", "active_websockets", "latest_readings_count"]
            for field in required_fields:
                assert field in data

class TestErrorHandling:
    """Test error handling scenarios"""
    
    def test_404_endpoints(self, client):
        """Test 404 handling for non-existent endpoints"""
        response = client.get("/v1/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test 405 handling for wrong HTTP methods"""
        response = client.put("/v1/sensors/latest")
        assert response.status_code == 405
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.options("/v1/sensors/latest")
        # CORS headers should be present if middleware is configured
        # This test might need adjustment based on actual CORS configuration

if __name__ == "__main__":
    pytest.main([__file__, "-v"])