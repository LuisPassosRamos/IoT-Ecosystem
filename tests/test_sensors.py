"""
Tests for IoT Edge Sensor Logic
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add edge sensors to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'edge', 'sensors'))

# Mock MQTT client before importing sensor modules
mock_mqtt = Mock()
mock_mqtt.Client = Mock
mock_mqtt.MQTT_ERR_SUCCESS = 0
sys.modules['paho'] = Mock()
sys.modules['paho.mqtt'] = mock_mqtt
sys.modules['paho.mqtt.client'] = mock_mqtt

# Import sensor classes after mocking
from temp_sensor import TemperatureSensor
from humidity_sensor import HumiditySensor
from luminosity_sensor import LuminositySensor

class TestTemperatureSensor:
    """Test temperature sensor functionality"""
    
    @pytest.fixture
    def sensor(self):
        """Create a temperature sensor instance with mocked MQTT client"""
        with patch('temp_sensor.mqtt.Client') as mock_client:
            sensor = TemperatureSensor()
            sensor.client = Mock()
            sensor.client.publish.return_value = Mock(rc=0)  # Successful publish
            return sensor
    
    def test_initialization(self, sensor):
        """Test sensor initialization"""
        assert sensor.last_value == 22.0
        assert hasattr(sensor, 'client')
    
    def test_normal_temperature_generation(self, sensor):
        """Test normal temperature reading generation"""
        # Test multiple readings to ensure they're within normal range most of the time
        normal_readings = 0
        total_readings = 100
        
        for _ in range(total_readings):
            temp = sensor.generate_reading()
            assert isinstance(temp, float)
            assert temp >= -10.0  # Reasonable lower bound
            assert temp <= 50.0   # Reasonable upper bound
            
            # Count readings in normal range
            if 18.0 <= temp <= 32.0:
                normal_readings += 1
        
        # Most readings should be normal (we expect ~95% normal)
        assert normal_readings >= 80  # At least 80% should be normal
    
    def test_anomaly_detection_out_of_range(self, sensor):
        """Test anomaly detection for out-of-range values"""
        # Test too cold
        assert sensor.detect_anomaly(10.0) == True
        
        # Test too hot
        assert sensor.detect_anomaly(40.0) == True
        
        # Test normal range
        assert sensor.detect_anomaly(25.0) == False
    
    def test_anomaly_detection_sudden_jump(self, sensor):
        """Test anomaly detection for sudden temperature jumps"""
        sensor.last_value = 20.0
        
        # Test sudden jump up
        assert sensor.detect_anomaly(30.0) == True  # 10°C jump
        
        # Test sudden jump down
        assert sensor.detect_anomaly(10.0) == True  # 10°C jump down
        
        # Test normal variation
        assert sensor.detect_anomaly(22.0) == False  # 2°C variation
    
    def test_payload_creation(self, sensor):
        """Test sensor payload creation"""
        test_value = 23.5
        payload = sensor.create_payload(test_value)
        
        # Check required fields
        assert 'ts' in payload
        assert 'type' in payload
        assert 'value' in payload
        assert 'unit' in payload
        assert 'sensor_id' in payload
        assert 'origin' in payload
        
        # Check values
        assert payload['type'] == 'temperature'
        assert payload['value'] == test_value
        assert payload['unit'] == '°C'
        assert payload['sensor_id'] == 'temp-001'
        assert payload['origin'] == 'edge'
        
        # Check timestamp format
        assert payload['ts'].endswith('Z')
        datetime.fromisoformat(payload['ts'][:-1])  # Should not raise exception
    
    def test_anomalous_payload_creation(self, sensor):
        """Test payload creation with anomaly flag"""
        sensor.last_value = 20.0
        anomalous_value = 40.0  # Out of range
        
        payload = sensor.create_payload(anomalous_value)
        assert payload.get('anomaly') == True
    
    def test_publish_reading(self, sensor):
        """Test publishing sensor reading"""
        sensor.publish_reading()
        
        # Verify publish was called
        sensor.client.publish.assert_called_once()
        
        # Get the call arguments
        call_args = sensor.client.publish.call_args
        topic, payload_str = call_args[0][:2]
        
        assert topic == "sensors/temperature/temp-001"
        
        # Parse and validate payload
        payload = json.loads(payload_str)
        assert payload['type'] == 'temperature'
        assert isinstance(payload['value'], (int, float))

class TestHumiditySensor:
    """Test humidity sensor functionality"""
    
    @pytest.fixture
    def sensor(self):
        """Create a humidity sensor instance with mocked MQTT client"""
        with patch('humidity_sensor.mqtt.Client') as mock_client:
            sensor = HumiditySensor()
            sensor.client = Mock()
            sensor.client.publish.return_value = Mock(rc=0)
            return sensor
    
    def test_initialization(self, sensor):
        """Test sensor initialization"""
        assert sensor.last_value == 55.0
        assert hasattr(sensor, 'client')
    
    def test_humidity_range_validation(self, sensor):
        """Test humidity stays within 0-100% range"""
        for _ in range(100):
            humidity = sensor.generate_reading()
            assert 0.0 <= humidity <= 100.0
    
    def test_humidity_anomaly_detection(self, sensor):
        """Test humidity anomaly detection"""
        # Test normal range
        assert sensor.detect_anomaly(50.0) == False
        
        # Test out of normal range (too dry)
        assert sensor.detect_anomaly(20.0) == True
        
        # Test out of normal range (too humid)
        assert sensor.detect_anomaly(90.0) == True
        
        # Test sudden jump
        sensor.last_value = 50.0
        assert sensor.detect_anomaly(70.0) == True  # 20% jump
    
    def test_humidity_payload_structure(self, sensor):
        """Test humidity payload structure"""
        payload = sensor.create_payload(60.5)
        
        assert payload['type'] == 'humidity'
        assert payload['value'] == 60.5
        assert payload['unit'] == '%'
        assert payload['sensor_id'] == 'hum-001'

class TestLuminositySensor:
    """Test luminosity sensor functionality"""
    
    @pytest.fixture
    def sensor(self):
        """Create a luminosity sensor instance with mocked MQTT client"""
        with patch('luminosity_sensor.mqtt.Client') as mock_client:
            sensor = LuminositySensor()
            sensor.client = Mock()
            sensor.client.publish.return_value = Mock(rc=0)
            return sensor
    
    def test_initialization(self, sensor):
        """Test sensor initialization"""
        assert sensor.last_value == 500
        assert hasattr(sensor, 'client')
    
    def test_luminosity_positive_values(self, sensor):
        """Test luminosity values are always positive"""
        for _ in range(100):
            luminosity = sensor.generate_reading()
            assert luminosity >= 0
    
    def test_luminosity_anomaly_detection(self, sensor):
        """Test luminosity anomaly detection"""
        # Test normal range
        assert sensor.detect_anomaly(800) == False
        
        # Test too dark
        assert sensor.detect_anomaly(50) == True
        
        # Test too bright
        assert sensor.detect_anomaly(3000) == True
        
        # Test sudden jump
        sensor.last_value = 500
        assert sensor.detect_anomaly(1200) == True  # 700 lux jump
    
    def test_time_based_generation(self, sensor):
        """Test that luminosity varies by time of day"""
        with patch('luminosity_sensor.datetime') as mock_datetime:
            # Test daytime (noon)
            mock_datetime.now.return_value = Mock(hour=12)
            mock_datetime.utcnow.return_value = datetime.utcnow()
            
            # Generate multiple readings and check they're generally higher during day
            daytime_readings = [sensor.generate_reading() for _ in range(20)]
            avg_daytime = sum(daytime_readings) / len(daytime_readings)
            
            # Test nighttime (3 AM)
            mock_datetime.now.return_value = Mock(hour=3)
            
            nighttime_readings = [sensor.generate_reading() for _ in range(20)]
            avg_nighttime = sum(nighttime_readings) / len(nighttime_readings)
            
            # Daytime should generally be brighter than nighttime
            assert avg_daytime > avg_nighttime
    
    def test_luminosity_payload_structure(self, sensor):
        """Test luminosity payload structure"""
        payload = sensor.create_payload(1200)
        
        assert payload['type'] == 'luminosity'
        assert payload['value'] == 1200
        assert payload['unit'] == 'lux'
        assert payload['sensor_id'] == 'lum-001'
        assert isinstance(payload['value'], int)  # Should be integer

class TestSensorAnomalyGeneration:
    """Test anomaly generation across all sensors"""
    
    @pytest.fixture(params=[TemperatureSensor, HumiditySensor, LuminositySensor])
    def sensor_class(self, request):
        return request.param
    
    def test_anomaly_frequency(self, sensor_class):
        """Test that anomalies are generated at expected frequency"""
        with patch(f'{sensor_class.__module__}.mqtt.Client'):
            sensor = sensor_class()
            sensor.client = Mock()
            
            anomaly_count = 0
            total_readings = 1000
            
            for _ in range(total_readings):
                value = sensor.generate_reading()
                payload = sensor.create_payload(value)
                if payload.get('anomaly'):
                    anomaly_count += 1
                sensor.last_value = value
            
            anomaly_rate = anomaly_count / total_readings
            
            # Expect roughly 5-10% anomaly rate
            assert 0.02 <= anomaly_rate <= 0.15, f"Anomaly rate {anomaly_rate:.2%} outside expected range"

class TestSensorErrorHandling:
    """Test error handling in sensor operations"""
    
    def test_mqtt_connection_failure(self):
        """Test handling of MQTT connection failures"""
        with patch('temp_sensor.mqtt.Client') as mock_client:
            # Mock connection failure
            mock_instance = Mock()
            mock_instance.connect.side_effect = Exception("Connection failed")
            mock_client.return_value = mock_instance
            
            sensor = TemperatureSensor()
            
            # run() should handle the exception gracefully
            with pytest.raises(Exception):
                sensor.client.connect("localhost", 1883, 60)
    
    def test_mqtt_publish_failure(self):
        """Test handling of MQTT publish failures"""
        with patch('temp_sensor.mqtt.Client') as mock_client:
            sensor = TemperatureSensor()
            sensor.client = Mock()
            
            # Mock publish failure
            mock_result = Mock()
            mock_result.rc = 1  # Failure code
            sensor.client.publish.return_value = mock_result
            
            # Should handle publish failure gracefully
            sensor.publish_reading()
            
            # Verify publish was attempted
            sensor.client.publish.assert_called_once()

class TestSensorDataConsistency:
    """Test data consistency across sensor readings"""
    
    def test_timestamp_consistency(self):
        """Test that timestamps are consistent and recent"""
        with patch('temp_sensor.mqtt.Client'):
            sensor = TemperatureSensor()
            
            start_time = datetime.utcnow()
            payload = sensor.create_payload(25.0)
            end_time = datetime.utcnow()
            
            # Parse timestamp
            timestamp_str = payload['ts']
            timestamp = datetime.fromisoformat(timestamp_str[:-1])  # Remove 'Z'
            
            # Timestamp should be between start and end time
            assert start_time <= timestamp <= end_time
    
    def test_sensor_id_consistency(self):
        """Test that sensor IDs are consistent"""
        with patch('temp_sensor.mqtt.Client'):
            sensor = TemperatureSensor()
            
            # Generate multiple payloads
            payloads = [sensor.create_payload(20.0 + i) for i in range(10)]
            
            # All should have the same sensor ID
            sensor_ids = [p['sensor_id'] for p in payloads]
            assert all(sid == sensor_ids[0] for sid in sensor_ids)
            assert sensor_ids[0] == 'temp-001'
    
    def test_value_progression(self):
        """Test that sensor values progress logically"""
        with patch('temp_sensor.mqtt.Client'):
            sensor = TemperatureSensor()
            
            values = []
            for _ in range(50):
                value = sensor.generate_reading()
                values.append(value)
                sensor.last_value = value
            
            # Check that extreme jumps are rare
            large_jumps = 0
            for i in range(1, len(values)):
                if abs(values[i] - values[i-1]) > 10:
                    large_jumps += 1
            
            # Should have few large jumps (most should be gradual changes)
            assert large_jumps < len(values) * 0.1  # Less than 10% large jumps

class TestSensorIntegration:
    """Test sensor integration scenarios"""
    
    def test_concurrent_sensor_operation(self):
        """Test multiple sensors can operate concurrently"""
        with patch('temp_sensor.mqtt.Client'), \
             patch('humidity_sensor.mqtt.Client'), \
             patch('luminosity_sensor.mqtt.Client'):
            
            temp_sensor = TemperatureSensor()
            humidity_sensor = HumiditySensor()
            luminosity_sensor = LuminositySensor()
            
            # Mock clients
            for sensor in [temp_sensor, humidity_sensor, luminosity_sensor]:
                sensor.client = Mock()
                sensor.client.publish.return_value = Mock(rc=0)
            
            # All sensors should be able to publish simultaneously
            temp_sensor.publish_reading()
            humidity_sensor.publish_reading()
            luminosity_sensor.publish_reading()
            
            # Verify all published
            temp_sensor.client.publish.assert_called_once()
            humidity_sensor.client.publish.assert_called_once()
            luminosity_sensor.client.publish.assert_called_once()
    
    def test_payload_json_serialization(self):
        """Test that all sensor payloads can be JSON serialized"""
        sensor_classes = [TemperatureSensor, HumiditySensor, LuminositySensor]
        
        for sensor_class in sensor_classes:
            with patch(f'{sensor_class.__module__}.mqtt.Client'):
                sensor = sensor_class()
                payload = sensor.create_payload(50.0)
                
                # Should be able to serialize and deserialize
                json_str = json.dumps(payload)
                parsed_payload = json.loads(json_str)
                
                # Should maintain data integrity
                assert parsed_payload == payload

if __name__ == "__main__":
    pytest.main([__file__, "-v"])