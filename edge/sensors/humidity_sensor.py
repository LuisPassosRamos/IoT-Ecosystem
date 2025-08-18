#!/usr/bin/env python3
"""
Humidity sensor simulator with anomaly detection.
Publishes data to MQTT broker with configurable thresholds.
"""

import os
import time
import json
import random
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HumiditySensor:
    def __init__(self):
        # MQTT Configuration
        self.mqtt_host = os.getenv("MQTT_HOST", "localhost")
        self.mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
        self.topic = "sensors/humidity/sim001"
        
        # Sensor configuration
        self.sensor_id = "humidity_sim_001"
        self.min_humidity = float(os.getenv("HUMIDITY_MIN", "30.0"))
        self.max_humidity = float(os.getenv("HUMIDITY_MAX", "90.0"))
        self.jump_threshold = float(os.getenv("HUMIDITY_JUMP_THRESHOLD", "20.0"))
        
        # State tracking for anomaly detection
        self.last_value: Optional[float] = None
        self.anomaly_probability = 0.04  # 4% chance of anomaly
        
        # MQTT Client
        self.client = mqtt.Client(client_id=f"humidity-sensor-{self.sensor_id}")
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.mqtt_host}:{self.mqtt_port}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        logger.warning(f"Disconnected from MQTT broker. Return code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        logger.debug(f"Message published with mid: {mid}")
    
    def detect_anomaly(self, value: float) -> bool:
        """Detect anomalies based on range and sudden jumps."""
        anomaly = False
        
        # Range-based anomaly
        if value < self.min_humidity or value > self.max_humidity:
            anomaly = True
            logger.warning(f"Range anomaly detected: {value}% (valid range: {self.min_humidity}-{self.max_humidity}%)")
        
        # Jump-based anomaly
        if self.last_value is not None:
            jump = abs(value - self.last_value)
            if jump > self.jump_threshold:
                anomaly = True
                logger.warning(f"Jump anomaly detected: {jump}% change from {self.last_value}% to {value}%")
        
        return anomaly
    
    def generate_humidity(self) -> float:
        """Generate humidity reading with occasional anomalies."""
        if random.random() < self.anomaly_probability:
            # Generate anomalous reading
            if random.choice([True, False]):
                # Out of range anomaly
                return round(random.choice([
                    random.uniform(0, self.min_humidity - 5),           # Too dry
                    random.uniform(self.max_humidity + 5, 100)          # Too humid
                ]), 2)
            else:
                # Jump anomaly (if we have previous value)
                if self.last_value is not None:
                    jump_direction = random.choice([-1, 1])
                    jump_size = random.uniform(self.jump_threshold + 5, self.jump_threshold + 15)
                    new_value = self.last_value + (jump_direction * jump_size)
                    return round(max(0, min(100, new_value)), 2)
        
        # Normal reading
        if self.last_value is not None:
            # Generate value close to previous (normal drift)
            drift = random.uniform(-5.0, 5.0)
            new_value = self.last_value + drift
            # Keep within reasonable bounds
            new_value = max(self.min_humidity + 5, min(self.max_humidity - 5, new_value))
        else:
            # First reading
            new_value = random.uniform(self.min_humidity + 5, self.max_humidity - 5)
        
        return round(new_value, 2)
    
    def create_payload(self, humidity: float) -> Dict[str, Any]:
        """Create MQTT payload with sensor data."""
        anomaly = self.detect_anomaly(humidity)
        
        payload = {
            "ts": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "type": "humidity",
            "value": humidity,
            "unit": "percent",
            "sensor_id": self.sensor_id,
            "origin": "edge",
            "anomaly": anomaly
        }
        
        if anomaly:
            payload["anomaly_details"] = {
                "out_of_range": humidity < self.min_humidity or humidity > self.max_humidity,
                "sudden_jump": self.last_value is not None and abs(humidity - self.last_value) > self.jump_threshold,
                "previous_value": self.last_value
            }
        
        return payload
    
    def publish_reading(self):
        """Generate and publish a single humidity reading."""
        try:
            humidity = self.generate_humidity()
            payload = self.create_payload(humidity)
            
            # Publish to MQTT
            result = self.client.publish(self.topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                status = "ANOMALY" if payload["anomaly"] else "NORMAL"
                logger.info(f"Published humidity: {humidity}% [{status}]")
            else:
                logger.error(f"Failed to publish message. Return code: {result.rc}")
            
            # Update last value for next anomaly detection
            self.last_value = humidity
            
        except Exception as e:
            logger.error(f"Error publishing reading: {e}")
    
    def run(self):
        """Main sensor loop."""
        try:
            # Connect to MQTT broker
            self.client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.client.loop_start()
            
            logger.info(f"Humidity sensor {self.sensor_id} started")
            logger.info(f"Publishing to topic: {self.topic}")
            
            while True:
                self.publish_reading()
                time.sleep(3)  # Publish every 3 seconds
                
        except KeyboardInterrupt:
            logger.info("Sensor stopped by user")
        except Exception as e:
            logger.error(f"Sensor error: {e}")
        finally:
            self.client.loop_stop()
            self.client.disconnect()

if __name__ == "__main__":
    sensor = HumiditySensor()
    sensor.run()