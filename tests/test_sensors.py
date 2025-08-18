#!/usr/bin/env python3
"""
Test suite for IoT-Ecosystem edge sensor simulators.
Tests sensor logic, anomaly detection, and MQTT publishing.
"""

import pytest
import json
import time
from unittest.mock import MagicMock, patch
from datetime import datetime

# Import sensor classes (adjust paths as needed)
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'edge', 'sensors'))

try:
    from temp_sensor import TemperatureSensor
    from humidity_sensor import HumiditySensor  
    from luminosity_sensor import LuminositySensor
except ImportError:
    # Create mock classes if imports fail
    class TemperatureSensor:
        def __init__(self):
            self.min_temp = 15.0
            self.max_temp = 35.0
            self.jump_threshold = 5.0
            self.last_value = None
        
        def detect_anomaly(self, value):
            return value < self.min_temp or value > self.max_temp
        
        def generate_temperature(self):
            return 25.0
    
    class HumiditySensor:
        def __init__(self):
            self.min_humidity = 30.0
            self.max_humidity = 90.0
            self.jump_threshold = 20.0
            self.last_value = None
        
        def detect_anomaly(self, value):
            return value < self.min_humidity or value > self.max_humidity
        
        def generate_humidity(self):
            return 65.0
    
    class LuminositySensor:
        def __init__(self):
            self.min_lux = 0.0
            self.max_lux = 1000.0
            self.jump_threshold = 200.0
            self.last_value = None
        
        def detect_anomaly(self, value):
            return value < self.min_lux or value > self.max_lux
        
        def generate_luminosity(self):
            return 450.0

class TestTemperatureSensor:
    """Test cases for temperature sensor simulator."""
    
    def setup_method(self):
        """Setup test environment."""
        self.sensor = TemperatureSensor()
        self.sensor.client = MagicMock()  # Mock MQTT client
    
    def test_sensor_initialization(self):
        """Test sensor initialization with default values."""
        assert self.sensor.min_temp == 15.0
        assert self.sensor.max_temp == 35.0
        assert self.sensor.jump_threshold == 5.0
        assert self.sensor.last_value is None
        assert self.sensor.sensor_id == "temp_sim_001"
    
    def test_range_anomaly_detection(self):
        """Test anomaly detection for out-of-range values."""
        # Test normal values
        assert not self.sensor.detect_anomaly(20.0)
        assert not self.sensor.detect_anomaly(25.0)
        assert not self.sensor.detect_anomaly(30.0)
        
        # Test out-of-range values
        assert self.sensor.detect_anomaly(10.0)  # Too cold
        assert self.sensor.detect_anomaly(40.0)  # Too hot
        assert self.sensor.detect_anomaly(-5.0)  # Extremely cold
        assert self.sensor.detect_anomaly(50.0)  # Extremely hot
    
    def test_jump_anomaly_detection(self):
        """Test anomaly detection for sudden value jumps."""
        # Set previous value
        self.sensor.last_value = 25.0
        
        # Test normal variations
        assert not self.sensor.detect_anomaly(27.0)  # +2°C
        assert not self.sensor.detect_anomaly(22.0)  # -3°C
        assert not self.sensor.detect_anomaly(30.0)  # +5°C (at threshold)
        
        # Test jumps above threshold
        assert self.sensor.detect_anomaly(31.0)  # +6°C
        assert self.sensor.detect_anomaly(18.0)  # -7°C
    
    def test_temperature_generation(self):
        """Test temperature value generation."""
        temp = self.sensor.generate_temperature()
        
        # Should be a valid number
        assert isinstance(temp, (int, float))
        assert not str(temp) == 'nan'
        
        # Test multiple generations
        temps = [self.sensor.generate_temperature() for _ in range(10)]
        
        # Should have some variation
        assert len(set(temps)) > 1  # Not all the same
        
        # All should be reasonable values
        for temp in temps:
            assert -20 <= temp <= 60  # Reasonable temperature range
    
    def test_payload_creation(self):
        """Test sensor payload creation."""
        test_temp = 25.3
        payload = self.sensor.create_payload(test_temp)
        
        # Check required fields
        assert "ts" in payload
        assert "type" in payload
        assert "value" in payload
        assert "unit" in payload
        assert "sensor_id" in payload
        assert "origin" in payload
        assert "anomaly" in payload
        
        # Check values
        assert payload["type"] == "temperature"
        assert payload["value"] == test_temp
        assert payload["unit"] == "celsius"
        assert payload["sensor_id"] == "temp_sim_001"
        assert payload["origin"] == "edge"
        assert isinstance(payload["anomaly"], bool)
        
        # Check timestamp format
        try:
            datetime.fromisoformat(payload["ts"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Invalid timestamp format")
    
    def test_anomalous_payload_details(self):
        """Test payload creation for anomalous readings."""
        # Create anomalous reading
        anomalous_temp = 45.0  # Above max threshold
        payload = self.sensor.create_payload(anomalous_temp)
        
        assert payload["anomaly"] is True
        assert "anomaly_details" in payload
        
        details = payload["anomaly_details"]
        assert "out_of_range" in details
        assert "sudden_jump" in details
        assert details["out_of_range"] is True

class TestHumiditySensor:
    """Test cases for humidity sensor simulator."""
    
    def setup_method(self):
        """Setup test environment."""
        self.sensor = HumiditySensor()
        self.sensor.client = MagicMock()
    
    def test_sensor_initialization(self):
        """Test sensor initialization."""
        assert self.sensor.min_humidity == 30.0
        assert self.sensor.max_humidity == 90.0
        assert self.sensor.jump_threshold == 20.0
        assert self.sensor.sensor_id == "humidity_sim_001"
    
    def test_humidity_range_validation(self):
        """Test humidity range anomaly detection."""
        # Normal humidity values
        assert not self.sensor.detect_anomaly(50.0)
        assert not self.sensor.detect_anomaly(70.0)
        assert not self.sensor.detect_anomaly(30.0)  # At minimum
        assert not self.sensor.detect_anomaly(90.0)  # At maximum
        
        # Out-of-range values
        assert self.sensor.detect_anomaly(25.0)   # Too dry
        assert self.sensor.detect_anomaly(95.0)   # Too humid
        assert self.sensor.detect_anomaly(0.0)    # Extremely dry
        assert self.sensor.detect_anomaly(100.0)  # Saturated
    
    def test_humidity_generation(self):
        """Test humidity value generation."""
        humidity = self.sensor.generate_humidity()
        
        assert isinstance(humidity, (int, float))
        assert 0 <= humidity <= 100  # Valid humidity range
        
        # Test multiple generations
        humidities = [self.sensor.generate_humidity() for _ in range(10)]
        assert len(set(humidities)) > 1  # Should vary
    
    def test_payload_structure(self):
        """Test humidity payload structure."""
        test_humidity = 65.2
        payload = self.sensor.create_payload(test_humidity)
        
        assert payload["type"] == "humidity"
        assert payload["value"] == test_humidity
        assert payload["unit"] == "percent"
        assert payload["sensor_id"] == "humidity_sim_001"

class TestLuminositySensor:
    """Test cases for luminosity sensor simulator."""
    
    def setup_method(self):
        """Setup test environment."""
        self.sensor = LuminositySensor()
        self.sensor.client = MagicMock()
    
    def test_sensor_initialization(self):
        """Test sensor initialization."""
        assert self.sensor.min_lux == 0.0
        assert self.sensor.max_lux == 1000.0
        assert self.sensor.jump_threshold == 200.0
        assert self.sensor.sensor_id == "luminosity_sim_001"
    
    def test_luminosity_range_validation(self):
        """Test luminosity range anomaly detection."""
        # Normal luminosity values
        assert not self.sensor.detect_anomaly(100.0)
        assert not self.sensor.detect_anomaly(500.0)
        assert not self.sensor.detect_anomaly(0.0)     # At minimum
        assert not self.sensor.detect_anomaly(1000.0)  # At maximum
        
        # Out-of-range values
        assert self.sensor.detect_anomaly(-10.0)   # Negative light
        assert self.sensor.detect_anomaly(1500.0)  # Too bright
    
    def test_daily_pattern_influence(self):
        """Test that luminosity generation considers time of day."""
        # This test assumes the sensor considers current hour
        luminosity = self.sensor.generate_luminosity()
        
        assert isinstance(luminosity, (int, float))
        assert luminosity >= 0  # Cannot be negative
        
        # Test multiple generations
        luminosities = [self.sensor.generate_luminosity() for _ in range(5)]
        assert all(lux >= 0 for lux in luminosities)
    
    def test_payload_structure(self):
        """Test luminosity payload structure."""
        test_luminosity = 450.7
        payload = self.sensor.create_payload(test_luminosity)
        
        assert payload["type"] == "luminosity"
        assert payload["value"] == test_luminosity
        assert payload["unit"] == "lux"
        assert payload["sensor_id"] == "luminosity_sim_001"

class TestSensorIntegration:
    """Integration tests for sensor components."""
    
    @patch('paho.mqtt.client.Client')
    def test_mqtt_client_initialization(self, mock_mqtt_client):
        """Test MQTT client initialization for sensors."""
        mock_client_instance = MagicMock()
        mock_mqtt_client.return_value = mock_client_instance
        
        sensor = TemperatureSensor()
        
        # Verify MQTT client was created
        mock_mqtt_client.assert_called_once()
        
        # Verify callbacks were set
        assert sensor.client.on_connect == sensor.on_connect
        assert sensor.client.on_disconnect == sensor.on_disconnect
        assert sensor.client.on_publish == sensor.on_publish
    
    def test_sensor_payload_serialization(self):
        """Test that sensor payloads can be serialized to JSON."""
        sensors = [
            TemperatureSensor(),
            HumiditySensor(),
            LuminositySensor()
        ]
        
        for sensor in sensors:
            # Generate a test reading
            if hasattr(sensor, 'generate_temperature'):
                value = sensor.generate_temperature()
            elif hasattr(sensor, 'generate_humidity'):
                value = sensor.generate_humidity()
            else:
                value = sensor.generate_luminosity()
            
            payload = sensor.create_payload(value)
            
            # Should be serializable to JSON
            try:
                json_str = json.dumps(payload)
                parsed_payload = json.loads(json_str)
                
                # Should preserve all data
                assert parsed_payload["value"] == payload["value"]
                assert parsed_payload["type"] == payload["type"]
                assert parsed_payload["anomaly"] == payload["anomaly"]
                
            except (TypeError, ValueError) as e:
                pytest.fail(f"Payload serialization failed for {sensor.__class__.__name__}: {e}")
    
    def test_anomaly_consistency(self):
        """Test that anomaly detection is consistent across sensors."""
        sensors = [
            (TemperatureSensor(), [-10, 50]),    # Out of range values
            (HumiditySensor(), [10, 95]),        # Out of range values
            (LuminositySensor(), [-5, 1200])     # Out of range values
        ]
        
        for sensor, test_values in sensors:
            for value in test_values:
                # Should detect as anomaly
                is_anomaly = sensor.detect_anomaly(value)
                assert is_anomaly, f"{sensor.__class__.__name__} should detect {value} as anomaly"
                
                # Payload should also mark as anomaly
                payload = sensor.create_payload(value)
                assert payload["anomaly"] is True, f"Payload should mark {value} as anomaly"
    
    def test_sensor_id_uniqueness(self):
        """Test that each sensor type has unique sensor IDs."""
        temp_sensor = TemperatureSensor()
        humidity_sensor = HumiditySensor()
        luminosity_sensor = LuminositySensor()
        
        sensor_ids = [
            temp_sensor.sensor_id,
            humidity_sensor.sensor_id,
            luminosity_sensor.sensor_id
        ]
        
        # All sensor IDs should be unique
        assert len(sensor_ids) == len(set(sensor_ids)), "Sensor IDs should be unique"
        
        # All should be non-empty strings
        for sensor_id in sensor_ids:
            assert isinstance(sensor_id, str)
            assert len(sensor_id) > 0

class TestAnomalyDetection:
    """Specific tests for anomaly detection algorithms."""
    
    def test_threshold_based_anomalies(self):
        """Test threshold-based anomaly detection."""
        sensor = TemperatureSensor()
        
        # Test values at boundaries
        assert not sensor.detect_anomaly(15.0)  # At minimum
        assert not sensor.detect_anomaly(35.0)  # At maximum
        assert sensor.detect_anomaly(14.9)      # Just below minimum
        assert sensor.detect_anomaly(35.1)      # Just above maximum
    
    def test_jump_based_anomalies(self):
        """Test jump-based anomaly detection."""
        sensor = TemperatureSensor()
        
        # Set baseline
        sensor.last_value = 25.0
        
        # Test gradual changes (should not be anomalies)
        assert not sensor.detect_anomaly(26.0)  # +1°C
        assert not sensor.detect_anomaly(27.0)  # +2°C
        
        # Update last value and test larger jumps
        sensor.last_value = 25.0
        assert not sensor.detect_anomaly(30.0)  # +5°C (at threshold)
        
        sensor.last_value = 25.0
        assert sensor.detect_anomaly(31.0)      # +6°C (above threshold)
        
        sensor.last_value = 25.0
        assert sensor.detect_anomaly(18.0)      # -7°C (above threshold)
    
    def test_combined_anomaly_conditions(self):
        """Test scenarios with multiple anomaly conditions."""
        sensor = TemperatureSensor()
        sensor.last_value = 25.0
        
        # Value that's both out of range AND a large jump
        anomalous_value = 45.0  # Above max (35°C) and big jump from 25°C
        
        assert sensor.detect_anomaly(anomalous_value)
        
        payload = sensor.create_payload(anomalous_value)
        assert payload["anomaly"] is True
        
        if "anomaly_details" in payload:
            details = payload["anomaly_details"]
            # Should detect both types of anomaly
            assert details.get("out_of_range", False) is True
            assert details.get("sudden_jump", False) is True

# Performance tests
class TestSensorPerformance:
    """Performance tests for sensor operations."""
    
    def test_sensor_generation_speed(self):
        """Test that sensor value generation is reasonably fast."""
        sensor = TemperatureSensor()
        
        start_time = time.time()
        
        # Generate many values
        for _ in range(1000):
            sensor.generate_temperature()
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly (less than 1 second for 1000 generations)
        assert elapsed_time < 1.0, f"Sensor generation too slow: {elapsed_time}s"
    
    def test_payload_creation_speed(self):
        """Test that payload creation is reasonably fast."""
        sensor = TemperatureSensor()
        
        start_time = time.time()
        
        # Create many payloads
        for i in range(100):
            sensor.create_payload(25.0 + i * 0.1)
        
        elapsed_time = time.time() - start_time
        
        # Should complete quickly
        assert elapsed_time < 0.5, f"Payload creation too slow: {elapsed_time}s"

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])